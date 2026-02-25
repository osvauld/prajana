use anyhow::{bail, Context, Result};
use lsp_types::{
    notification::{DidChangeTextDocument, DidOpenTextDocument, DidSaveTextDocument, Initialized},
    request::{DocumentSymbolRequest, GotoDefinition, Initialize, Shutdown},
    DidChangeTextDocumentParams, DidOpenTextDocumentParams, DidSaveTextDocumentParams,
    DocumentSymbolParams, DocumentSymbolResponse, GotoDefinitionParams, GotoDefinitionResponse,
    InitializeParams, InitializeResult, InitializedParams, Location, Position, SymbolKind,
    TextDocumentContentChangeEvent, TextDocumentIdentifier, TextDocumentItem,
    TextDocumentPositionParams, Uri, VersionedTextDocumentIdentifier, WorkspaceFolder,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::io::{BufRead, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::atomic::{AtomicI64, Ordering};
use std::sync::Mutex;

use super::surgical::RustBlockKind;

/// Convert a filesystem path to an `lsp_types::Uri` (file:// URI).
fn path_to_uri(path: &Path) -> Result<Uri> {
    let abs = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir()
            .context("failed to get cwd")?
            .join(path)
    };
    let uri_string = format!("file://{}", abs.display());
    uri_string
        .parse::<Uri>()
        .map_err(|e| anyhow::anyhow!("invalid URI '{}': {}", uri_string, e))
}

/// A resolved symbol location from rust-analyzer.
#[derive(Clone, Debug)]
pub struct ResolvedSymbol {
    pub name: String,
    pub kind: RustBlockKind,
    pub file: PathBuf,
    pub start_line: u32,
    pub start_col: u32,
    pub end_line: u32,
    pub end_col: u32,
    pub start_byte: usize,
    pub end_byte: usize,
    pub container: Option<String>,
}

/// Deterministic target query used by tools.
#[derive(Clone, Debug)]
pub struct SymbolQuery {
    pub name: String,
    pub kind: Option<RustBlockKind>,
    pub file: Option<PathBuf>,
    pub module_path: Option<String>,
    pub line_hint: Option<u32>,
}

/// Manages a rust-analyzer LSP process and provides synchronous queries.
pub struct RustAnalyzerClient {
    process: Child,
    stdin: Mutex<ChildStdin>,
    stdout: Mutex<BufReader<ChildStdout>>,
    next_id: AtomicI64,
    workspace_root: PathBuf,
    file_versions: Mutex<HashMap<PathBuf, i32>>,
    initialized: Mutex<bool>,
}

#[derive(Serialize)]
struct LspRequest {
    jsonrpc: &'static str,
    id: i64,
    method: String,
    params: Value,
}

#[derive(Serialize)]
struct LspNotification {
    jsonrpc: &'static str,
    method: String,
    params: Value,
}

#[derive(Deserialize)]
struct LspResponse {
    id: Option<i64>,
    result: Option<Value>,
    error: Option<LspError>,
}

#[derive(Deserialize, Debug)]
struct LspError {
    code: i64,
    message: String,
}

impl RustAnalyzerClient {
    /// Spawn rust-analyzer and perform LSP initialization handshake.
    pub fn start(workspace_root: PathBuf) -> Result<Self> {
        let mut child = Command::new("rust-analyzer")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .current_dir(&workspace_root)
            .spawn()
            .context("failed to spawn rust-analyzer; is it installed?")?;

        let stdin = child.stdin.take().context("no stdin on rust-analyzer")?;
        let stdout = child.stdout.take().context("no stdout on rust-analyzer")?;

        let client = Self {
            process: child,
            stdin: Mutex::new(stdin),
            stdout: Mutex::new(BufReader::new(stdout)),
            next_id: AtomicI64::new(1),
            workspace_root,
            file_versions: Mutex::new(HashMap::new()),
            initialized: Mutex::new(false),
        };

        client.do_initialize()?;
        Ok(client)
    }

    fn do_initialize(&self) -> Result<()> {
        let root_uri = path_to_uri(&self.workspace_root)?;

        #[allow(deprecated)]
        let params = InitializeParams {
            root_uri: Some(root_uri.clone()),
            workspace_folders: Some(vec![WorkspaceFolder {
                uri: root_uri,
                name: "workspace".to_string(),
            }]),
            capabilities: lsp_types::ClientCapabilities::default(),
            ..Default::default()
        };

        let _result: InitializeResult = self.send_request::<Initialize>(params)?;
        self.send_notification::<Initialized>(InitializedParams {})?;

        let mut init = self.initialized.lock().unwrap();
        *init = true;

        Ok(())
    }

    /// Notify rust-analyzer a file was opened or changed.
    pub fn sync_file(&self, path: &Path) -> Result<()> {
        let content = std::fs::read_to_string(path)
            .with_context(|| format!("failed to read {} for LSP sync", path.display()))?;
        let uri = path_to_uri(path)?;

        let mut versions = self.file_versions.lock().unwrap();
        let version = versions.entry(path.to_path_buf()).or_insert(0);

        if *version == 0 {
            self.send_notification::<DidOpenTextDocument>(DidOpenTextDocumentParams {
                text_document: TextDocumentItem {
                    uri,
                    language_id: "rust".to_string(),
                    version: 1,
                    text: content,
                },
            })?;
            *version = 1;
        } else {
            *version += 1;
            let new_version = *version;
            self.send_notification::<DidChangeTextDocument>(DidChangeTextDocumentParams {
                text_document: VersionedTextDocumentIdentifier {
                    uri: uri.clone(),
                    version: new_version,
                },
                content_changes: vec![TextDocumentContentChangeEvent {
                    range: None,
                    range_length: None,
                    text: content,
                }],
            })?;
            self.send_notification::<DidSaveTextDocument>(DidSaveTextDocumentParams {
                text_document: TextDocumentIdentifier { uri },
                text: None,
            })?;
        }

        Ok(())
    }

    /// Get document symbols for a file (flat list).
    pub fn document_symbols(&self, path: &Path) -> Result<Vec<ResolvedSymbol>> {
        self.sync_file(path)?;
        let uri = path_to_uri(path)?;

        let params = DocumentSymbolParams {
            text_document: TextDocumentIdentifier { uri },
            work_done_progress_params: Default::default(),
            partial_result_params: Default::default(),
        };

        let response: DocumentSymbolResponse = self
            .send_request::<DocumentSymbolRequest>(params)?
            .context("rust-analyzer returned no document symbols")?;
        let source = std::fs::read_to_string(path)?;

        let mut symbols = Vec::new();
        match response {
            DocumentSymbolResponse::Flat(flat) => {
                for sym in flat {
                    if let Some(kind) = lsp_kind_to_block_kind(sym.kind) {
                        let resolved = lsp_symbol_to_resolved(
                            &sym.name,
                            kind,
                            path,
                            sym.location.range.start.line,
                            sym.location.range.start.character,
                            sym.location.range.end.line,
                            sym.location.range.end.character,
                            sym.container_name.as_deref(),
                            &source,
                        );
                        symbols.push(resolved);
                    }
                }
            }
            DocumentSymbolResponse::Nested(nested) => {
                flatten_nested_symbols(&nested, path, &source, None, &mut symbols);
            }
        }

        Ok(symbols)
    }

    /// Deterministic symbol resolution: returns exactly one match or error.
    pub fn resolve_symbol(&self, query: &SymbolQuery) -> Result<ResolvedSymbol> {
        let file = match &query.file {
            Some(f) => {
                let abs = if f.is_absolute() {
                    f.clone()
                } else {
                    self.workspace_root.join(f)
                };
                abs
            }
            None => bail!("resolve_symbol requires a file path"),
        };

        let all_symbols = self.document_symbols(&file)?;
        let mut candidates: Vec<ResolvedSymbol> = all_symbols
            .into_iter()
            .filter(|s| s.name == query.name)
            .collect();

        if candidates.is_empty() {
            bail!("symbol '{}' not found in {}", query.name, file.display());
        }

        // Filter by kind
        if let Some(ref kind) = query.kind {
            candidates.retain(|s| &s.kind == kind);
            if candidates.is_empty() {
                bail!(
                    "symbol '{}' found but no match for kind {:?} in {}",
                    query.name,
                    kind,
                    file.display()
                );
            }
        }

        // Filter by module_path (container name from RA)
        if let Some(ref module_path) = query.module_path {
            candidates.retain(|s| {
                s.container
                    .as_deref()
                    .map(|c| c == module_path.as_str())
                    .unwrap_or(module_path.is_empty())
            });
            if candidates.is_empty() {
                bail!(
                    "symbol '{}' found but no match for module_path '{}' in {}",
                    query.name,
                    module_path,
                    file.display()
                );
            }
        }

        // Exactly one: done
        if candidates.len() == 1 {
            return Ok(candidates.remove(0));
        }

        // Disambiguate by line_hint
        if let Some(line_hint) = query.line_hint {
            let mut min_dist = u32::MAX;
            let mut best_indices = Vec::new();
            for (idx, s) in candidates.iter().enumerate() {
                let dist = s.start_line.abs_diff(line_hint);
                if dist < min_dist {
                    min_dist = dist;
                    best_indices.clear();
                    best_indices.push(idx);
                } else if dist == min_dist {
                    best_indices.push(idx);
                }
            }
            if best_indices.len() == 1 {
                return Ok(candidates.remove(best_indices[0]));
            }
            bail!(
                "ambiguous: '{}' matched {} symbols even with line_hint={} in {}",
                query.name,
                candidates.len(),
                line_hint,
                file.display()
            );
        }

        bail!(
            "ambiguous: '{}' matched {} symbols in {}; provide kind, module_path, or line_hint",
            query.name,
            candidates.len(),
            file.display()
        )
    }

    /// Get definition location for a position in a file.
    pub fn goto_definition(&self, path: &Path, line: u32, character: u32) -> Result<Vec<Location>> {
        self.sync_file(path)?;
        let uri = path_to_uri(path)?;

        let params = GotoDefinitionParams {
            text_document_position_params: TextDocumentPositionParams {
                text_document: TextDocumentIdentifier { uri },
                position: Position { line, character },
            },
            work_done_progress_params: Default::default(),
            partial_result_params: Default::default(),
        };

        let response: GotoDefinitionResponse = self
            .send_request::<GotoDefinition>(params)?
            .context("rust-analyzer returned no definition")?;
        let locations = match response {
            GotoDefinitionResponse::Scalar(loc) => vec![loc],
            GotoDefinitionResponse::Array(locs) => locs,
            GotoDefinitionResponse::Link(links) => links
                .into_iter()
                .map(|link| Location {
                    uri: link.target_uri,
                    range: link.target_selection_range,
                })
                .collect(),
        };

        Ok(locations)
    }

    // ── LSP transport ──────────────────────────────────────────────

    fn send_request<R: lsp_types::request::Request>(&self, params: R::Params) -> Result<R::Result>
    where
        R::Params: Serialize,
        R::Result: for<'de> Deserialize<'de>,
    {
        let id = self.next_id.fetch_add(1, Ordering::SeqCst);
        let body = serde_json::to_string(&LspRequest {
            jsonrpc: "2.0",
            id,
            method: R::METHOD.to_string(),
            params: serde_json::to_value(params)?,
        })?;

        self.write_message(&body)?;

        // Read responses until we get the one matching our id.
        // Skip notifications and responses for other ids.
        loop {
            let response = self.read_message()?;
            let parsed: LspResponse = serde_json::from_str(&response)
                .with_context(|| format!("failed to parse LSP response JSON"))?;

            if parsed.id == Some(id) {
                if let Some(err) = parsed.error {
                    bail!(
                        "LSP error (code {}): {} [method={}]",
                        err.code,
                        err.message,
                        R::METHOD
                    );
                }
                let result = parsed.result.unwrap_or(Value::Null);
                let typed: R::Result = serde_json::from_value(result)
                    .with_context(|| format!("failed to decode LSP result for {}", R::METHOD))?;
                return Ok(typed);
            }
            // else: notification or different request response; skip
        }
    }

    fn send_notification<N: lsp_types::notification::Notification>(
        &self,
        params: N::Params,
    ) -> Result<()>
    where
        N::Params: Serialize,
    {
        let body = serde_json::to_string(&LspNotification {
            jsonrpc: "2.0",
            method: N::METHOD.to_string(),
            params: serde_json::to_value(params)?,
        })?;
        self.write_message(&body)
    }

    fn write_message(&self, body: &str) -> Result<()> {
        let header = format!("Content-Length: {}\r\n\r\n", body.len());
        let mut stdin = self.stdin.lock().unwrap();
        stdin.write_all(header.as_bytes())?;
        stdin.write_all(body.as_bytes())?;
        stdin.flush()?;
        Ok(())
    }

    fn read_message(&self) -> Result<String> {
        let mut stdout = self.stdout.lock().unwrap();
        let mut content_length: usize = 0;

        // Read headers
        loop {
            let mut header_line = String::new();
            stdout.read_line(&mut header_line)?;
            let trimmed = header_line.trim();
            if trimmed.is_empty() {
                break;
            }
            if let Some(val) = trimmed.strip_prefix("Content-Length: ") {
                content_length = val
                    .parse::<usize>()
                    .with_context(|| format!("bad Content-Length: {}", val))?;
            }
        }

        if content_length == 0 {
            bail!("LSP message with Content-Length 0 or missing header");
        }

        let mut buf = vec![0u8; content_length];
        (&mut *stdout).read_exact(&mut buf)?;
        String::from_utf8(buf).context("LSP response not valid UTF-8")
    }
}

impl Drop for RustAnalyzerClient {
    fn drop(&mut self) {
        // Best-effort shutdown
        let _ = self.send_request::<Shutdown>(());
        let _ = self.process.kill();
    }
}

// ── Helpers ──────────────────────────────────────────────────────────

fn lsp_kind_to_block_kind(kind: SymbolKind) -> Option<RustBlockKind> {
    match kind {
        SymbolKind::FUNCTION | SymbolKind::METHOD => Some(RustBlockKind::Function),
        SymbolKind::STRUCT => Some(RustBlockKind::Struct),
        SymbolKind::ENUM => Some(RustBlockKind::Enum),
        SymbolKind::INTERFACE => Some(RustBlockKind::Trait),
        SymbolKind::CLASS => Some(RustBlockKind::Impl), // RA reports impl blocks as Class
        _ => None,
    }
}

fn lsp_symbol_to_resolved(
    name: &str,
    kind: RustBlockKind,
    path: &Path,
    start_line: u32,
    start_col: u32,
    end_line: u32,
    end_col: u32,
    container: Option<&str>,
    source: &str,
) -> ResolvedSymbol {
    let start_byte = lsp_position_to_byte(source, start_line, start_col);
    let end_byte = lsp_position_to_byte(source, end_line, end_col);

    ResolvedSymbol {
        name: name.to_string(),
        kind,
        file: path.to_path_buf(),
        start_line,
        start_col,
        end_line,
        end_col,
        start_byte,
        end_byte,
        container: container.map(|s| s.to_string()),
    }
}

fn flatten_nested_symbols(
    symbols: &[lsp_types::DocumentSymbol],
    path: &Path,
    source: &str,
    parent_name: Option<&str>,
    out: &mut Vec<ResolvedSymbol>,
) {
    for sym in symbols {
        if let Some(kind) = lsp_kind_to_block_kind(sym.kind) {
            let resolved = lsp_symbol_to_resolved(
                &sym.name,
                kind,
                path,
                sym.range.start.line,
                sym.range.start.character,
                sym.range.end.line,
                sym.range.end.character,
                parent_name,
                source,
            );
            out.push(resolved);
        }

        if let Some(ref children) = sym.children {
            flatten_nested_symbols(children, path, source, Some(&sym.name), out);
        }
    }
}

/// Convert LSP (line, col) position to byte offset in source text.
/// LSP uses 0-based line numbers and UTF-16 code unit offsets.
fn lsp_position_to_byte(source: &str, line: u32, col_utf16: u32) -> usize {
    let mut byte_offset = 0;
    for (i, src_line) in source.lines().enumerate() {
        if i == line as usize {
            // Walk UTF-16 code units to find byte offset within line
            let mut utf16_units = 0u32;
            for (byte_idx, ch) in src_line.char_indices() {
                if utf16_units >= col_utf16 {
                    return byte_offset + byte_idx;
                }
                utf16_units += ch.len_utf16() as u32;
            }
            // col is past end of line
            return byte_offset + src_line.len();
        }
        byte_offset += src_line.len() + 1; // +1 for newline
    }
    // Past end of file
    source.len()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lsp_position_to_byte_ascii() {
        let source = "fn foo() {\n    let x = 1;\n}\n";
        assert_eq!(lsp_position_to_byte(source, 0, 0), 0);
        assert_eq!(lsp_position_to_byte(source, 0, 3), 3); // 'f','n',' ' -> byte 3
        assert_eq!(lsp_position_to_byte(source, 1, 4), 15); // "    " on line 1
        assert_eq!(lsp_position_to_byte(source, 2, 0), 26); // "}"
    }

    #[test]
    fn test_lsp_kind_mapping() {
        assert!(matches!(
            lsp_kind_to_block_kind(SymbolKind::FUNCTION),
            Some(RustBlockKind::Function)
        ));
        assert!(matches!(
            lsp_kind_to_block_kind(SymbolKind::STRUCT),
            Some(RustBlockKind::Struct)
        ));
        assert!(matches!(
            lsp_kind_to_block_kind(SymbolKind::ENUM),
            Some(RustBlockKind::Enum)
        ));
        assert!(matches!(
            lsp_kind_to_block_kind(SymbolKind::INTERFACE),
            Some(RustBlockKind::Trait)
        ));
        assert!(lsp_kind_to_block_kind(SymbolKind::VARIABLE).is_none());
    }
}
