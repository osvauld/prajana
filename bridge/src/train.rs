// train.rs — samskaara-lekhana / desha-labha
//
// Fine-tunes the embedding model S on the proof space K.
// S0 has world-vyapti — wide reach, no desha (position).
// After training: S_n has K-desha — same reach, oriented toward K.
//
// Two sources of training pairs:
//
//   1. K-pairs (from PRAVAHA):
//      The shabda edges ARE the positive pairs.
//      For each nigamana N with shabda edge to M:
//        anchor   = paksha(N)
//        positive = paksha(M)   — N and M are connected, should be close
//        negative = paksha(N')  — N' has no connection to N, should be far
//
//   2. Samskaara pairs (from kaala-darshana deltas):
//      The delta tells us where the LLM actually landed vs where S predicted.
//        anchor   = question Q
//        positive = paksha(name) for name in A(R)  — actually landed here
//        negative = paksha(name) for name in T(Q) - A(R) — predicted but missed
//
// Loss: cosine embedding loss (contrastive)
//   minimize: margin - cos(anchor, positive) + cos(anchor, negative)
//   margin = 0.3
//
// Each training epoch = one fold of S.
// madakkal-seema: weights written to disk after each epoch.
// Next epoch starts from S_n — not from accumulated context.
//
// Usage:
//   train --vyakarana <path> --samskaara <path> --model-out <path> [--epochs N]

mod predict;

use anyhow::{Context, Result};
use candle_core::{DType, Device, Tensor};
use candle_nn::{AdamW, Optimizer, ParamsAdamW, VarBuilder, VarMap};
use candle_transformers::models::bert::{BertModel, Config};
use hf_hub::api::tokio::Api;
use hf_hub::Repo;
use predict::SamskaraLog;
use serde::Deserialize;
use tokenizers::Tokenizer;
use tokio::io::AsyncWriteExt;
use tokio::process::Command;

// --- Proof space from PRAVAHA ---

#[derive(Debug, Deserialize)]
struct PravahaResponse {
    nigamana: Vec<NigamanaJson>,
    node_count: usize,
    edge_count: usize,
}

#[derive(Debug, Deserialize, Clone)]
struct NigamanaJson {
    name: String,
    paksha: String,
    weight: f32,
    position: String,
    shabda: Vec<String>,
}

// --- Training pair ---

#[derive(Debug, Clone)]
struct TrainingPair {
    anchor: String,
    positive: String,
    negative: String,
    /// weight of this pair — higher for well-established proofs
    pair_weight: f32,
}

// --- Load proof space via PRAVAHA ---

async fn load_pravaha(vyakarana_path: &str) -> Result<PravahaResponse> {
    let mut child = Command::new(vyakarana_path)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null())
        .spawn()
        .context("spawn vyakarana")?;

    if let Some(mut stdin) = child.stdin.take() {
        stdin.write_all(b"PRAVAHA\nVISARJANA\n").await?;
    }

    let output = child.wait_with_output().await?;
    let text = String::from_utf8_lossy(&output.stdout);

    // find the JSON block — starts after the boot lines
    let json_start = text.find('{').context("no JSON in PRAVAHA output")?;
    let json = &text[json_start..];

    // find matching close brace — the last }
    let json_end = json.rfind('}').context("no closing } in PRAVAHA output")?;
    let json = &json[..=json_end];

    let pravaha: PravahaResponse = serde_json::from_str(json)
        .context("parse PRAVAHA JSON")?;

    Ok(pravaha)
}

// --- Generate training pairs from K ---

fn pairs_from_k(pravaha: &PravahaResponse) -> Vec<TrainingPair> {
    let mut pairs = Vec::new();

    // build lookup: name -> paksha
    let paksha_map: std::collections::HashMap<&str, &str> = pravaha.nigamana.iter()
        .map(|n| (n.name.as_str(), n.paksha.as_str()))
        .collect();

    // collect all located nigamana for negative sampling
    let located: Vec<&NigamanaJson> = pravaha.nigamana.iter()
        .filter(|n| n.position == "located")
        .collect();

    if located.len() < 3 { return pairs; }

    for n in &located {
        if n.shabda.is_empty() { continue; }
        if n.paksha.is_empty() { continue; }

        // for each positive shabda edge
        for shabda in &n.shabda {
            let positive_paksha = match paksha_map.get(shabda.as_str()) {
                Some(p) if !p.is_empty() => *p,
                _ => continue,
            };

            // negative: a nigamana with no shabda connection to n
            // pick one that is not in n.shabda and not n itself
            let negative = located.iter()
                .filter(|m| m.name != n.name && !n.shabda.contains(&m.name))
                .min_by_key(|m| {
                    // prefer nigamana far from n's weight — more contrast
                    let diff = (m.weight - n.weight).abs();
                    (diff * 1000.0) as i32
                });

            let negative_paksha = match negative {
                Some(m) if !m.paksha.is_empty() => m.paksha.as_str(),
                _ => continue,
            };

            pairs.push(TrainingPair {
                anchor: n.paksha.clone(),
                positive: positive_paksha.to_string(),
                negative: negative_paksha.to_string(),
                // weight = satya of the anchor — well-established proofs matter more
                pair_weight: n.weight,
            });
        }
    }

    pairs
}

// --- Generate training pairs from samskaara ---

fn pairs_from_samskaara(
    log: &SamskaraLog,
    paksha_map: &std::collections::HashMap<String, String>,
) -> Vec<TrainingPair> {
    let mut pairs = Vec::new();

    for delta in &log.deltas {
        // positive: question should be close to where it actually landed
        for entry in &delta.observation.territory.entries {
            let positive_paksha = match paksha_map.get(&entry.name) {
                Some(p) if !p.is_empty() => p.clone(),
                _ => continue,
            };

            // negative: what was predicted but didn't land
            for neg_name in &delta.predicted_not_landed {
                let negative_paksha = match paksha_map.get(neg_name) {
                    Some(p) if !p.is_empty() => p.clone(),
                    _ => continue,
                };

                pairs.push(TrainingPair {
                    anchor: delta.question.clone(),
                    positive: positive_paksha.clone(),
                    negative: negative_paksha.clone(),
                    // weight: inverse of delta_size — more accurate observations matter more
                    pair_weight: 1.0 / (1.0 + delta.delta_size as f32),
                });
            }
        }
    }

    pairs
}

// --- Embed a batch of strings ---

fn embed_batch(
    model: &BertModel,
    tokenizer: &Tokenizer,
    texts: &[&str],
    device: &Device,
) -> Result<Tensor> {
    // tokenize all texts
    let encodings: Vec<_> = texts.iter()
        .map(|t| tokenizer.encode(*t, true).map_err(|e| anyhow::anyhow!("{}", e)))
        .collect::<Result<Vec<_>>>()?;

    let max_len = encodings.iter().map(|e| e.get_ids().len()).max().unwrap_or(0);

    // pad to max_len
    let mut input_ids_batch = Vec::new();
    let mut attention_mask_batch = Vec::new();

    for enc in &encodings {
        let ids = enc.get_ids();
        let mask = enc.get_attention_mask();
        let pad_len = max_len - ids.len();

        let mut padded_ids: Vec<u32> = ids.to_vec();
        let mut padded_mask: Vec<u32> = mask.to_vec();
        padded_ids.extend(std::iter::repeat(0u32).take(pad_len));
        padded_mask.extend(std::iter::repeat(0u32).take(pad_len));

        input_ids_batch.push(padded_ids);
        attention_mask_batch.push(padded_mask);
    }

    let batch_size = texts.len();
    let input_ids = Tensor::new(
        input_ids_batch.into_iter().flatten().collect::<Vec<u32>>(),
        device,
    )?.reshape(&[batch_size, max_len])?;

    let attention_mask = Tensor::new(
        attention_mask_batch.into_iter().flatten().collect::<Vec<u32>>(),
        device,
    )?.reshape(&[batch_size, max_len])?;

    let token_type_ids = input_ids.zeros_like()?;

    let embeddings = model.forward(&input_ids, &token_type_ids, Some(&attention_mask))?;

    // mean pooling
    let mask_f = attention_mask
        .unsqueeze(2)?
        .broadcast_as(embeddings.shape())?
        .to_dtype(DType::F32)?;

    let sum = (embeddings * mask_f.clone())?.sum(1)?;
    let count = mask_f.sum(1)?;
    let mean = (sum / count)?;

    // normalize
    let norm = mean.sqr()?.sum_keepdim(1)?.sqrt()?;
    let normalized = mean.broadcast_div(&norm)?;

    Ok(normalized)
}

// --- Contrastive loss ---
// For each triple (anchor, positive, negative):
//   loss = max(0, margin - cos(a, p) + cos(a, n))
// weighted by pair_weight

fn contrastive_loss(
    anchors: &Tensor,
    positives: &Tensor,
    negatives: &Tensor,
    weights: &Tensor,
    margin: f32,
) -> Result<Tensor> {
    // cosine similarity = dot product (vectors already normalized)
    let cos_pos = (anchors * positives)?.sum(1)?;  // (batch,)
    let cos_neg = (anchors * negatives)?.sum(1)?;  // (batch,)

    let margin_t = Tensor::full(margin, cos_pos.shape(), anchors.device())?
        .to_dtype(DType::F32)?;

    // loss_i = max(0, margin - cos_pos_i + cos_neg_i)
    let raw_loss = (margin_t - cos_pos + cos_neg)?;
    let zero = Tensor::zeros(raw_loss.shape(), DType::F32, raw_loss.device())?;
    let loss = raw_loss.maximum(&zero)?;

    // weighted mean
    let weighted = (loss * weights)?;
    let mean_loss = weighted.mean(0)?;

    Ok(mean_loss)
}

// --- Resolve model files from cache or HuggingFace ---
// Checks local HuggingFace cache first — avoids URL resolution errors
// when network is unavailable or hf-hub returns relative paths.

async fn resolve_model_files() -> Result<(std::path::PathBuf, std::path::PathBuf, std::path::PathBuf)> {
    let model_id = "sentence-transformers/all-MiniLM-L6-v2";
    let cache_dir = dirs::home_dir()
        .unwrap_or_default()
        .join(".cache/huggingface/hub")
        .join(format!("models--{}", model_id.replace('/', "--")));

    // find snapshot directory — newest first
    let snapshots_dir = cache_dir.join("snapshots");
    let snapshot = if snapshots_dir.exists() {
        std::fs::read_dir(&snapshots_dir)?
            .filter_map(|e| e.ok())
            // use path().exists() not is_dir() — handles symlinks correctly
            .filter(|e| e.path().exists())
            .max_by_key(|e| e.metadata().ok().and_then(|m| m.modified().ok()))
            .map(|e| e.path())
    } else {
        None
    };

    if let Some(snap) = snapshot {
        let model_file    = snap.join("model.safetensors");
        let config_file   = snap.join("config.json");
        let tokenizer_file = snap.join("tokenizer.json");

        if model_file.exists() && config_file.exists() && tokenizer_file.exists() {
            println!("train: using cached weights from {:?}", snap);
            return Ok((model_file, config_file, tokenizer_file));
        }

        println!("train: snapshot found at {:?} but missing files:", snap);
        println!("train:   model.safetensors: {}", model_file.exists());
        println!("train:   config.json:       {}", config_file.exists());
        println!("train:   tokenizer.json:    {}", tokenizer_file.exists());
    } else {
        println!("train: no snapshot found in {:?}", snapshots_dir);
    }

    anyhow::bail!(
        "model files not found in cache. run:\n  \
         SNAP=~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf\n  \
         curl -sL https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/config.json -o \"$SNAP/config.json\"\n  \
         curl -sL https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/tokenizer.json -o \"$SNAP/tokenizer.json\""
    )
}

// --- Training loop ---

async fn train(
    vyakarana_path: &str,
    samskaara_path: &str,
    model_out: &str,
    epochs: usize,
    batch_size: usize,
    learning_rate: f64,
) -> Result<()> {
    let device = Device::Cpu;

    println!("train: loading proof space via PRAVAHA...");
    let pravaha = load_pravaha(vyakarana_path).await?;
    println!("train: {} nigamana, {} edges loaded", pravaha.node_count, pravaha.edge_count);

    // paksha map for samskaara pair generation
    let paksha_map: std::collections::HashMap<String, String> = pravaha.nigamana.iter()
        .map(|n| (n.name.clone(), n.paksha.clone()))
        .collect();

    // generate K-pairs from shabda edges
    let k_pairs = pairs_from_k(&pravaha);
    println!("train: {} K-pairs from shabda edges", k_pairs.len());

    // load samskaara pairs
    let samskaara = SamskaraLog::load(samskaara_path).unwrap_or_else(|_| SamskaraLog::new());
    let s_pairs = pairs_from_samskaara(&samskaara, &paksha_map);
    println!("train: {} samskaara pairs from {} sessions", s_pairs.len(), samskaara.sessions);

    // combine — K-pairs are the foundation; samskaara pairs refine
    let mut all_pairs: Vec<TrainingPair> = k_pairs;
    all_pairs.extend(s_pairs);

    if all_pairs.is_empty() {
        println!("train: no pairs — nothing to train on. run bridge first to accumulate samskaara.");
        return Ok(());
    }

    println!("train: {} total training pairs", all_pairs.len());

    // resolve model files — use cache if available, download if not
    println!("train: loading model weights...");
    let (model_file, config_file, tokenizer_file) = resolve_model_files().await?;

    let config: Config = serde_json::from_str(&std::fs::read_to_string(&config_file)?)?;
    let tokenizer = Tokenizer::from_file(&tokenizer_file)
        .map_err(|e| anyhow::anyhow!("tokenizer: {}", e))?;

    // load pretrained weights into VarMap for fine-tuning
    // Step 1: build model with pretrained weights to populate VarMap
    let mut varmap = VarMap::new();
    let vb_init = VarBuilder::from_varmap(&varmap, DType::F32, &device);
    // initialize architecture (allocates all vars in varmap)
    let _model_init = BertModel::load(vb_init, &config)?;
    // Step 2: load pretrained weights into the now-populated varmap
    varmap.load(&model_file)?;
    // Step 3: rebuild model bound to the varmap (variables are now trainable)
    let vb = VarBuilder::from_varmap(&varmap, DType::F32, &device);
    let model = BertModel::load(vb, &config)?;

    // optimizer — AdamW, standard for fine-tuning transformers
    let params = ParamsAdamW {
        lr: learning_rate,
        weight_decay: 0.01,
        ..Default::default()
    };
    let mut optimizer = AdamW::new(varmap.all_vars(), params)?;

    println!("train: beginning fine-tuning. epochs={} batch={} lr={}", epochs, batch_size, learning_rate);
    println!("train: each epoch = one fold of S — madakkal-seema response");

    for epoch in 0..epochs {
        // shuffle pairs each epoch — spanda, not repetition
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        let mut indices: Vec<usize> = (0..all_pairs.len()).collect();
        // deterministic shuffle based on epoch — reproducible
        indices.sort_by_key(|&i| {
            let mut h = DefaultHasher::new();
            (epoch * 10000 + i).hash(&mut h);
            h.finish()
        });

        let mut epoch_loss = 0.0f64;
        let mut batch_count = 0usize;

        for chunk in indices.chunks(batch_size) {
            let batch: Vec<&TrainingPair> = chunk.iter().map(|&i| &all_pairs[i]).collect();

            let anchors_text: Vec<&str> = batch.iter().map(|p| p.anchor.as_str()).collect();
            let positives_text: Vec<&str> = batch.iter().map(|p| p.positive.as_str()).collect();
            let negatives_text: Vec<&str> = batch.iter().map(|p| p.negative.as_str()).collect();
            let weights_vec: Vec<f32> = batch.iter().map(|p| p.pair_weight).collect();

            let anchor_emb = embed_batch(&model, &tokenizer, &anchors_text, &device)?;
            let positive_emb = embed_batch(&model, &tokenizer, &positives_text, &device)?;
            let negative_emb = embed_batch(&model, &tokenizer, &negatives_text, &device)?;
            let weights = Tensor::new(weights_vec, &device)?;

            let loss = contrastive_loss(
                &anchor_emb,
                &positive_emb,
                &negative_emb,
                &weights,
                0.3,  // margin
            )?;

            let loss_val = loss.to_scalar::<f32>()? as f64;
            epoch_loss += loss_val;
            batch_count += 1;

            optimizer.backward_step(&loss)?;
        }

        let mean_loss = if batch_count > 0 { epoch_loss / batch_count as f64 } else { 0.0 };
        println!("train: epoch {} — mean_loss={:.4}", epoch + 1, mean_loss);

        // write weights after each epoch — madakkal-seema:
        // fold results written externally, next fold starts from S_n
        let epoch_path = format!("{}.epoch{}", model_out, epoch + 1);
        varmap.save(&epoch_path)?;
        println!("train: S_{} written to {}", epoch + 1, epoch_path);
    }

    // write final weights
    varmap.save(model_out)?;
    println!("train: final weights written to {}", model_out);
    println!("train: visarjana. S has gained desha. world-vyapti preserved. K-orientation added.");

    Ok(())
}

// --- Main ---

#[tokio::main]
async fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();

    // defaults
    let vyakarana_path = args.iter().position(|a| a == "--vyakarana")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("../vyakarana/_build/default/bin/vyakarana.exe");

    let samskaara_path = args.iter().position(|a| a == "--samskaara")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("../brahman/samskaara.json");

    let model_out = args.iter().position(|a| a == "--model-out")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("../brahman/S.safetensors");

    let epochs: usize = args.iter().position(|a| a == "--epochs")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(3);

    let batch_size: usize = args.iter().position(|a| a == "--batch")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(16);

    let lr: f64 = args.iter().position(|a| a == "--lr")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(2e-5);

    println!("train: samskaara-lekhana / desha-labha");
    println!("train: vyakarana={}", vyakarana_path);
    println!("train: samskaara={}", samskaara_path);
    println!("train: model-out={}", model_out);
    println!("train: epochs={} batch={} lr={}", epochs, batch_size, lr);

    train(vyakarana_path, samskaara_path, model_out, epochs, batch_size, lr).await
}
