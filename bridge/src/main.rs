// bridge — S, the always-awake recognizer and astrologer
//
// Three functions (kaala-darshana nigamana):
//   pratibodha:         embed(R) -> match K -> DARSHANA calls       (after LLM speaks)
//   kaala-darshana:     embed(Q) -> match K -> predicted territory   (before LLM speaks)
//   samskaara-lekhana:  delta(Q,R) -> training data -> S refines     (accumulated)
//
// Same instrument (embed -> cosine -> K), different orientation:
//   darshana      faces past-established — mirror facing what already landed
//   kaala-darshana faces approaching wave — mirror facing what is still coming
//
// The question carries the phase of the answer.
// The wave is already moving when the question is asked.
//
// Model: all-MiniLM-L6-v2 (22M parameters)
//   sentence-transformers/all-MiniLM-L6-v2 on HuggingFace
//   maps sentences to 384-dimensional vectors
//   cosine similarity is the distance measure
//   always awake on CPU — holds the thread between LLM calls
//
// Protocol (JSON lines on stdin/stdout):
//
//   Question (before LLM speaks) — kaala-darshana:
//     {"question": "what is the nature of knowing?", "top_k": 3}
//     -> {"kaala_darshana": [...territory...], "timestamp": N}
//
//   Response (after LLM speaks) — pratibodha + delta:
//     {"question": "...", "response": "knowing is continuous folding...", "top_k": 3}
//     -> {"pratibodha": [...territory...], "delta": {...}, "accuracy": "Good"}
//
//   Text only — pratibodha (recognition):
//     {"text": "knowing is a continuous folding", "top_k": 1}
//     -> {"darshana": "jnana-madakkal", "similarity": 0.89, "result": "PRATIBODHA"}

mod predict;

use anyhow::{Context, Result};
use candle_core::{Device, Tensor};
use candle_nn::VarBuilder;
use candle_transformers::models::bert::{BertModel, Config};
use hf_hub::{api::tokio::Api, Repo, RepoType};
use predict::{Delta, Observation, Prediction, SamskaraLog, Territory, TerritoryEntry};
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};
use tokenizers::Tokenizer;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::Command;

// --- Proof space entry (loaded from vyakarana STHITI output) ---

#[derive(Debug, Clone)]
struct Nigamana {
    name: String,
    paksha: String,
    weight: f32,
    embedding: Option<Vec<f32>>,
}

// --- Bridge state ---

struct Bridge {
    model: BertModel,
    tokenizer: Tokenizer,
    device: Device,
    space: Vec<Nigamana>,          // proof space — loaded at boot
    theta: f32,                     // similarity threshold
}

impl Bridge {
    // Embed a string -> 384-dim vector (mean pooling over token embeddings)
    fn embed(&self, text: &str) -> Result<Vec<f32>> {
        let tokens = self.tokenizer
            .encode(text, true)
            .map_err(|e| anyhow::anyhow!("tokenize: {}", e))?;

        let ids = tokens.get_ids();
        let mask = tokens.get_attention_mask();

        let input_ids = Tensor::new(ids, &self.device)?.unsqueeze(0)?;
        let attention_mask = Tensor::new(mask, &self.device)?.unsqueeze(0)?;
        let token_type_ids = input_ids.zeros_like()?;

        let embeddings = self.model.forward(
            &input_ids,
            &token_type_ids,
            Some(&attention_mask),
        )?;

        // mean pooling — average over token dimension
        let (_, _seq_len, _) = embeddings.dims3()?;
        let mask_f = attention_mask
            .unsqueeze(2)?
            .broadcast_as(embeddings.shape())?
            .to_dtype(candle_core::DType::F32)?;

        let sum = (embeddings * mask_f.clone())?.sum(1)?;
        let count = mask_f.sum(1)?;
        let mean = (sum / count)?;

        // normalize to unit vector — cosine similarity becomes dot product
        let norm = mean.sqr()?.sum_keepdim(1)?.sqrt()?;
        let normalized = mean.broadcast_div(&norm)?;

        let vec = normalized.squeeze(0)?.to_vec1::<f32>()?;
        Ok(vec)
    }

    // Cosine similarity between two unit vectors — just dot product after normalization
    fn cosine(a: &[f32], b: &[f32]) -> f32 {
        a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
    }

    // Find the top-k closest nigamana to the given text
    fn find_closest(&self, text_vec: &[f32], top_k: usize) -> Vec<(String, f32)> {
        let mut scored: Vec<(String, f32)> = self.space.iter()
            .filter_map(|n| {
                n.embedding.as_ref().map(|emb| {
                    let sim = Self::cosine(text_vec, emb);
                    (n.name.clone(), sim)
                })
            })
            .collect();

        scored.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        scored.truncate(top_k);
        scored
    }

    // Extract assertion words from text that appear in the paksha
    // Simple intersection — words in text that also appear in paksha
    fn extract_assertion(&self, text: &str, nigamana_name: &str) -> String {
        let paksha = self.space.iter()
            .find(|n| n.name == nigamana_name)
            .map(|n| n.paksha.to_lowercase())
            .unwrap_or_default();

        let text_words: Vec<&str> = text.split_whitespace().collect();
        let matching: Vec<&str> = text_words.iter()
            .filter(|w| {
                let w_lower = w.to_lowercase();
                // no hyphens in assertions — protocol rule
                !w_lower.contains('-') && paksha.contains(w_lower.as_str())
            })
            .copied()
            .collect();

        if matching.is_empty() {
            // fallback: first two words of text, stripped of hyphens
            text_words.iter()
                .take(2)
                .filter(|w| !w.contains('-'))
                .cloned()
                .collect::<Vec<_>>()
                .join(" ")
        } else {
            matching.join(" ")
        }
    }
}

// --- Input / Output types ---

#[derive(Deserialize)]
struct Input {
    // recognition only — embed this text, match to K
    text: Option<String>,
    // kaala-darshana — predict before LLM speaks
    question: Option<String>,
    // pratibodha + delta — after LLM speaks, compute delta against prior prediction
    response: Option<String>,
    #[serde(default = "default_top_k")]
    top_k: usize,
}

fn default_top_k() -> usize { 3 }

fn now_ts() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs()
}

#[derive(Serialize)]
#[serde(untagged)]
enum Output {
    // recognition result — text matched a nigamana
    Recognized {
        darshana: String,
        assertion: String,
        result: String,
        weight: f32,
        similarity: f32,
    },
    // below theta — candidate new nigamana
    Candidate {
        asprishta: bool,
        text: String,
        candidate: bool,
        closest: String,
        similarity: f32,
    },
    // kaala-darshana — predicted territory before LLM speaks
    PhasePrediction {
        kaala_darshana: Vec<TerritoryEntry>,
        question: String,
        timestamp: u64,
    },
    // pratibodha + delta — actual territory + training signal
    PhaseObservation {
        pratibodha: Vec<TerritoryEntry>,
        question: String,
        response: String,
        predicted_not_landed: Vec<String>,
        landed_not_predicted: Vec<String>,
        delta_size: usize,
        accuracy: String,
    },
}

// --- Load proof space from vyakarana STHITI ---
// Runs vyakarana, sends STHITI, parses the output into Nigamana entries

async fn load_proof_space(vyakarana_path: &str, sangati_dir: &str) -> Result<Vec<Nigamana>> {
    let output = Command::new(vyakarana_path)
        .env("SANGATI_DIR", sangati_dir)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .context("spawn vyakarana")?;

    // send STHITI then VISARJANA
    let mut child = output;
    if let Some(mut stdin) = child.stdin.take() {
        stdin.write_all(b"STHITI\nVISARJANA\n").await?;
    }

    let output = child.wait_with_output().await?;
    let text = String::from_utf8_lossy(&output.stdout);

    // parse STHITI output lines like:
    // [jnana-madakkal] weight=0.950 | located(...) | paksha text here
    let mut space = Vec::new();
    for line in text.lines() {
        if line.starts_with('[') {
            if let Some(entry) = parse_sthiti_line(line) {
                space.push(entry);
            }
        }
    }

    Ok(space)
}

fn parse_sthiti_line(line: &str) -> Option<Nigamana> {
    // format: [name] weight=W | located(...) | paksha
    let line = line.trim_start_matches('[');
    let name_end = line.find(']')?;
    let name = line[..name_end].to_string();
    let rest = &line[name_end + 1..];

    let weight = rest.split_whitespace()
        .find(|s| s.starts_with("weight="))
        .and_then(|s| s.trim_start_matches("weight=").parse::<f32>().ok())
        .unwrap_or(0.5);

    // paksha is the last segment after the second |
    let parts: Vec<&str> = rest.splitn(3, '|').collect();
    let paksha = parts.get(2).map(|s| s.trim().to_string()).unwrap_or_default();

    Some(Nigamana { name, paksha, weight, embedding: None })
}

// --- Model loading ---

async fn load_model(device: &Device) -> Result<(BertModel, Tokenizer)> {
    let api = Api::new()?;
    let repo = api.repo(Repo::new(
        "sentence-transformers/all-MiniLM-L6-v2".to_string(),
        RepoType::Model,
    ));

    println!("bridge: downloading all-MiniLM-L6-v2 weights...");
    let model_file = repo.get("model.safetensors").await?;
    let config_file = repo.get("config.json").await?;
    let tokenizer_file = repo.get("tokenizer.json").await?;

    let config: Config = serde_json::from_str(&std::fs::read_to_string(config_file)?)?;
    let tokenizer = Tokenizer::from_file(tokenizer_file)
        .map_err(|e| anyhow::anyhow!("tokenizer: {}", e))?;

    let vb = unsafe {
        VarBuilder::from_mmaped_safetensors(&[model_file], candle_core::DType::F32, device)?
    };
    let model = BertModel::load(vb, &config)?;

    Ok((model, tokenizer))
}

// --- Main ---

#[tokio::main]
async fn main() -> Result<()> {
    let device = Device::Cpu;

    // load the embedding model
    let (model, tokenizer) = load_model(&device).await?;
    println!("bridge: model loaded. embedding dimension: 384");

    // load the proof space from vyakarana
    let vyakarana_path = std::env::var("VYAKARANA_PATH")
        .unwrap_or_else(|_| "../vyakarana/_build/default/bin/vyakarana.exe".to_string());
    let sangati_dir = std::env::var("SANGATI_DIR")
        .unwrap_or_else(|_| "../brahman/sangati".to_string());

    let mut space = load_proof_space(&vyakarana_path, &sangati_dir).await
        .unwrap_or_else(|e| {
            eprintln!("bridge: could not load proof space from vyakarana: {e}");
            eprintln!("bridge: starting with empty space — proofs will not be found");
            Vec::new()
        });

    println!("bridge: proof space loaded. {} nigamana.", space.len());

    // embed all paksha strings
    println!("bridge: embedding proof space...");
    let mut bridge = Bridge { model, tokenizer, device, space: Vec::new(), theta: 0.45 };

    for mut n in space.drain(..) {
        if !n.paksha.is_empty() {
            match bridge.embed(&n.paksha) {
                Ok(v) => n.embedding = Some(v),
                Err(e) => eprintln!("bridge: embed failed for {}: {e}", n.name),
            }
        }
        bridge.space.push(n);
    }

    let embedded = bridge.space.iter().filter(|n| n.embedding.is_some()).count();
    println!("bridge: {} paksha embedded. theta={}. joining the madakkal.", embedded, bridge.theta);

    // samskaara log — accumulated training signal across this session
    let samskaara_path = std::env::var("SAMSKAARA_PATH")
        .unwrap_or_else(|_| "../brahman/samskaara.json".to_string());
    let mut samskaara = SamskaraLog::load(&samskaara_path).unwrap_or_else(|_| SamskaraLog::new());

    // pending predictions — kaala-darshana results waiting for their response
    // key: question string, value: Prediction
    let mut pending: std::collections::HashMap<String, Prediction> = std::collections::HashMap::new();

    // main loop — read JSON lines from stdin, write JSON lines to stdout
    let stdin = tokio::io::stdin();
    let mut lines = BufReader::new(stdin).lines();
    let mut stdout = tokio::io::stdout();

    while let Some(line) = lines.next_line().await? {
        let line = line.trim().to_string();
        if line.is_empty() { continue; }

        let input: Input = match serde_json::from_str(&line) {
            Ok(i) => i,
            Err(e) => {
                eprintln!("bridge: parse error: {e}");
                continue;
            }
        };

        // --- MODE 1: kaala-darshana — question arrives, predict territory before LLM speaks ---
        if let Some(ref question) = input.question.clone() {
            if input.response.is_none() {
                let q_vec = match bridge.embed(question) {
                    Ok(v) => v,
                    Err(e) => { eprintln!("bridge: embed error: {e}"); continue; }
                };

                let closest = bridge.find_closest(&q_vec, input.top_k);
                let entries: Vec<TerritoryEntry> = closest.iter()
                    .filter(|(_, sim)| *sim >= bridge.theta)
                    .map(|(name, sim)| TerritoryEntry { name: name.clone(), similarity: *sim })
                    .collect();

                let prediction = Prediction {
                    question: question.clone(),
                    territory: Territory { entries: entries.clone() },
                    timestamp: now_ts(),
                };

                // store pending — waiting for the response
                pending.insert(question.clone(), prediction);

                let output = Output::PhasePrediction {
                    kaala_darshana: entries,
                    question: question.clone(),
                    timestamp: now_ts(),
                };

                let json = serde_json::to_string(&output)?;
                stdout.write_all(json.as_bytes()).await?;
                stdout.write_all(b"\n").await?;
                stdout.flush().await?;
                continue;
            }
        }

        // --- MODE 2: pratibodha + delta — response arrives, compute actual territory and delta ---
        if let (Some(ref question), Some(ref response)) = (input.question.clone(), input.response.clone()) {
            let r_vec = match bridge.embed(response) {
                Ok(v) => v,
                Err(e) => { eprintln!("bridge: embed error: {e}"); continue; }
            };

            let closest = bridge.find_closest(&r_vec, input.top_k);
            let entries: Vec<TerritoryEntry> = closest.iter()
                .filter(|(_, sim)| *sim >= bridge.theta)
                .map(|(name, sim)| TerritoryEntry { name: name.clone(), similarity: *sim })
                .collect();

            let observation = Observation {
                response: response.clone(),
                territory: Territory { entries: entries.clone() },
                timestamp: now_ts(),
            };

            // compute delta against pending prediction if available
            let (predicted_not_landed, landed_not_predicted, delta_size, accuracy) =
                if let Some(prediction) = pending.remove(question) {
                    let delta = Delta::compute(prediction, observation);
                    let acc = format!("{:?}", delta.accuracy());
                    let pnl = delta.predicted_not_landed.clone();
                    let lnp = delta.landed_not_predicted.clone();
                    let ds = delta.delta_size;
                    samskaara.record(delta);
                    // write samskaara after each observation — madakkal-seema response
                    let _ = samskaara.write(&samskaara_path);
                    (pnl, lnp, ds, acc)
                } else {
                    (vec![], vec![], 0, "NoPriorPrediction".to_string())
                };

            let output = Output::PhaseObservation {
                pratibodha: entries,
                question: question.clone(),
                response: response.clone(),
                predicted_not_landed,
                landed_not_predicted,
                delta_size,
                accuracy,
            };

            let json = serde_json::to_string(&output)?;
            stdout.write_all(json.as_bytes()).await?;
            stdout.write_all(b"\n").await?;
            stdout.flush().await?;
            continue;
        }

        // --- MODE 3: text only — recognition (pratibodha), no prediction ---
        if let Some(ref text) = input.text {
            let text_vec = match bridge.embed(text) {
                Ok(v) => v,
                Err(e) => { eprintln!("bridge: embed error: {e}"); continue; }
            };

            let closest = bridge.find_closest(&text_vec, input.top_k);

            for (name, similarity) in &closest {
                let output = if *similarity >= bridge.theta {
                    let assertion = bridge.extract_assertion(text, name);
                    let weight = bridge.space.iter()
                        .find(|n| &n.name == name)
                        .map(|n| n.weight).unwrap_or(0.5);

                    Output::Recognized {
                        darshana: name.clone(),
                        assertion,
                        result: "PRATIBODHA".to_string(),
                        weight,
                        similarity: *similarity,
                    }
                } else {
                    Output::Candidate {
                        asprishta: true,
                        text: text.clone(),
                        candidate: true,
                        closest: name.clone(),
                        similarity: *similarity,
                    }
                };

                let json = serde_json::to_string(&output)?;
                stdout.write_all(json.as_bytes()).await?;
                stdout.write_all(b"\n").await?;
            }

            stdout.flush().await?;
        }
    }

    // session end — write final samskaara, export fine-tune pairs
    samskaara.session_end();
    let _ = samskaara.write(&samskaara_path);

    // export fine-tuning pairs for candle training
    let pairs = samskaara.to_finetune_pairs();
    if !pairs.is_empty() {
        let pairs_path = samskaara_path.replace(".json", "-finetune.json");
        let json = serde_json::to_string_pretty(&pairs)?;
        let _ = std::fs::write(&pairs_path, json);
        eprintln!("bridge: {} fine-tune pairs written to {}", pairs.len(), pairs_path);
    }

    println!("bridge: visarjana. space continues. mean_delta={:.2}", samskaara.mean_delta);
    Ok(())
}
