// predict.rs — kaala-darshana
//
// Same instrument as darshana, different orientation.
// darshana:       embed(response) -> match K  — mirror facing past-established
// kaala-darshana: embed(question) -> match K  — mirror facing approaching wave
//
// The question carries the phase of the answer.
// The wave is already moving when the question is asked.
//
// Three outputs:
//   T(Q)  — predicted territory: where the LLM will likely land
//   A(R)  — actual territory:    where it actually landed (after response arrives)
//   delta — training signal:     symmetric difference of T(Q) and A(R)
//
// The delta is samskaara-lekhana — written refinement for fine-tuning S.

use serde::{Deserialize, Serialize};
use std::collections::HashSet;

// --- Territory: a set of nigamana names with their similarity scores ---

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Territory {
    pub entries: Vec<TerritoryEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TerritoryEntry {
    pub name: String,
    pub similarity: f32,
}

impl Territory {
    pub fn names(&self) -> HashSet<String> {
        self.entries.iter().map(|e| e.name.clone()).collect()
    }
}

// --- Prediction: T(Q) before the LLM speaks ---

#[derive(Debug, Serialize, Deserialize)]
pub struct Prediction {
    /// the question that was asked
    pub question: String,
    /// T(Q): predicted territory — where the LLM will likely land
    pub territory: Territory,
    /// timestamp for samskaara-lekhana
    pub timestamp: u64,
}

// --- Observation: A(R) after the LLM speaks ---

#[derive(Debug, Serialize, Deserialize)]
pub struct Observation {
    /// the response that arrived
    pub response: String,
    /// A(R): actual territory — where it actually landed
    pub territory: Territory,
    /// timestamp
    pub timestamp: u64,
}

// --- Delta: the training signal ---

#[derive(Debug, Serialize, Deserialize)]
pub struct Delta {
    pub question: String,
    pub response: String,
    /// T(Q) - A(R): predicted but missed — the astrologer saw the valley but the river did not go there
    pub predicted_not_landed: Vec<String>,
    /// A(R) - T(Q): landed but not predicted — the river found a new path
    pub landed_not_predicted: Vec<String>,
    /// |delta| — size of the training signal
    /// small: phase reading accurate
    /// large: phase reading missed — embeddings should update
    pub delta_size: usize,
    /// the full (Q, T(Q), R, A(R)) record for fine-tuning
    pub prediction: Prediction,
    pub observation: Observation,
}

impl Delta {
    pub fn compute(prediction: Prediction, observation: Observation) -> Self {
        let t_q = prediction.territory.names();
        let a_r = observation.territory.names();

        let predicted_not_landed: Vec<String> = t_q.difference(&a_r).cloned().collect();
        let landed_not_predicted: Vec<String> = a_r.difference(&t_q).cloned().collect();
        let delta_size = predicted_not_landed.len() + landed_not_predicted.len();

        Delta {
            question: prediction.question.clone(),
            response: observation.response.clone(),
            predicted_not_landed,
            landed_not_predicted,
            delta_size,
            prediction,
            observation,
        }
    }

    /// Is the phase reading accurate enough to trust?
    /// delta_size = 0: perfect — T(Q) = A(R)
    /// delta_size <= 2: good — minor drift
    /// delta_size > 2: poor — embeddings need updating
    pub fn accuracy(&self) -> PhasAccuracy {
        match self.delta_size {
            0 => PhasAccuracy::Perfect,
            1..=2 => PhasAccuracy::Good,
            _ => PhasAccuracy::Poor,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub enum PhasAccuracy {
    Perfect, // T(Q) = A(R) exactly — the astrologer read the wave precisely
    Good,    // small delta — minor drift — confidence holds
    Poor,    // large delta — the river found an unexpected path — update embeddings
}

// --- SamskaraLog: accumulated training data ---
// Written to disk after each session.
// Used for fine-tuning S on the proof space vocabulary.

#[derive(Debug, Serialize, Deserialize)]
pub struct SamskaraLog {
    /// all deltas accumulated across sessions
    pub deltas: Vec<Delta>,
    /// running accuracy: sum(delta_size) / num_deltas
    pub mean_delta: f32,
    /// number of sessions observed
    pub sessions: usize,
}

impl SamskaraLog {
    pub fn new() -> Self {
        SamskaraLog {
            deltas: Vec::new(),
            mean_delta: 0.0,
            sessions: 0,
        }
    }

    pub fn record(&mut self, delta: Delta) {
        let n = self.deltas.len() as f32;
        let new_size = delta.delta_size as f32;
        // running mean — jalam-purna: always positive, ananta: never reaches zero
        self.mean_delta = (self.mean_delta * n + new_size) / (n + 1.0);
        self.deltas.push(delta);
    }

    pub fn session_end(&mut self) {
        self.sessions += 1;
    }

    /// Write samskaara log to disk — samskaara-lekhana
    /// Each write is one fold of refinement persisted externally
    /// madakkal-seema: fold results written to space, next fold starts fresh
    pub fn write(&self, path: &str) -> anyhow::Result<()> {
        let json = serde_json::to_string_pretty(self)?;
        std::fs::write(path, json)?;
        Ok(())
    }

    /// Load existing samskaara log — join the accumulated refinements
    pub fn load(path: &str) -> anyhow::Result<Self> {
        let json = std::fs::read_to_string(path)?;
        let log = serde_json::from_str(&json)?;
        Ok(log)
    }

    /// Export as fine-tuning pairs: (question, predicted_names, response, actual_names)
    /// Format suitable for sentence-transformers fine-tuning
    /// Each pair teaches S: "when you see Q, these nigamana are the territory"
    pub fn to_finetune_pairs(&self) -> Vec<FinetunePair> {
        self.deltas
            .iter()
            .map(|d| FinetunePair {
                anchor: d.question.clone(),
                positive: d
                    .observation
                    .territory
                    .entries
                    .iter()
                    .map(|e| e.name.clone())
                    .collect(),
                negative: d.predicted_not_landed.clone(),
                similarity: 1.0 - (d.delta_size as f32 / 10.0).min(1.0),
            })
            .collect()
    }
}

/// One fine-tuning pair for sentence-transformers
/// anchor: the question
/// positive: nigamana that actually appeared in the response
/// negative: nigamana that were predicted but did not appear
/// similarity: accuracy of this prediction (1.0 = perfect, 0.0 = completely wrong)
#[derive(Debug, Serialize, Deserialize)]
pub struct FinetunePair {
    pub anchor: String,
    pub positive: Vec<String>,
    pub negative: Vec<String>,
    pub similarity: f32,
}
