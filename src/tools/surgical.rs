use anyhow::{bail, Context, Result};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::path::Path;
use std::path::PathBuf;
use std::process::Command;
use std::sync::Arc;
use tree_sitter::{Node, Parser};
use tracing::{debug, warn};

use crate::tools::rust_analyzer::{RustAnalyzerClient, SymbolQuery};
use crate::tools::{Tool, ToolResult};

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RustBlockKind {
    Function,
    Struct,
    Impl,
    Enum,
    Trait,
}

#[derive(Clone, Debug)]
pub struct BlockTarget {
    pub kind: RustBlockKind,
    pub name: String,
}

#[derive(Clone, Debug, Default)]
pub struct BlockLocator {
    pub module_path: Option<String>,
    pub line_hint: Option<usize>,
}

#[derive(Clone, Debug)]
struct BlockMatch {
    start_byte: usize,
    end_byte: usize,
    start_line: usize,
    module_path: String,
}

#[derive(Clone, Debug)]
pub struct SymbolInfo {
    pub kind: RustBlockKind,
    pub name: String,
    pub start_line: usize,
    pub end_line: usize,
}

#[derive(Clone, Debug)]
pub struct EditOutcome {
    pub file: String,
    pub start_byte: usize,
    pub end_byte: usize,
    pub inserted_bytes: usize,
    pub symbol: String,
    pub symbol_kind: RustBlockKind,
    pub symbol_module_path: String,
    pub validation: ValidationStatus,
    pub old_block_hash: String,
}

#[derive(Clone, Debug)]
pub struct ValidationStatus {
    pub rust_syntax_ok: bool,
    pub rustfmt_ran: bool,
    pub rustfmt_ok: bool,
    pub cargo_check_ran: bool,
    pub cargo_check_ok: bool,
}

impl ValidationStatus {
    fn syntax_only() -> Self {
        Self {
            rust_syntax_ok: true,
            rustfmt_ran: false,
            rustfmt_ok: false,
            cargo_check_ran: false,
            cargo_check_ok: false,
        }
    }
}

pub trait SurgicalEditor {
    fn list_symbols(&self, path: &Path) -> Result<Vec<SymbolInfo>>;
    fn replace_block(
        &self,
        path: &Path,
        target: &BlockTarget,
        locator: &BlockLocator,
        new_block: &str,
        expected_old_hash: Option<&str>,
        expected_old_block: Option<&str>,
        run_rustfmt: bool,
        run_cargo_check: bool,
        workspace_root: &Path,
    ) -> Result<EditOutcome>;
    fn insert_after_block(
        &self,
        path: &Path,
        target: &BlockTarget,
        locator: &BlockLocator,
        snippet: &str,
        expected_old_hash: Option<&str>,
        expected_old_block: Option<&str>,
        run_rustfmt: bool,
        run_cargo_check: bool,
        workspace_root: &Path,
    ) -> Result<EditOutcome>;
    fn validate(&self, path: &Path) -> Result<()>;
}

pub struct RustSurgicalEditor {
    ra_client: Option<Arc<RustAnalyzerClient>>,
}

impl RustSurgicalEditor {
    pub fn new(ra_client: Option<Arc<RustAnalyzerClient>>) -> Self {
        Self { ra_client }
    }

    fn parse_source(&self, source: &str) -> Result<tree_sitter::Tree> {
        let mut parser = Parser::new();
        parser
            .set_language(&tree_sitter_rust::LANGUAGE.into())
            .context("failed to set Rust tree-sitter grammar")?;
        parser
            .parse(source, None)
            .ok_or_else(|| anyhow::anyhow!("failed to parse Rust source"))
    }

    fn kind_for_node(node: &Node) -> Option<RustBlockKind> {
        match node.kind() {
            "function_item" => Some(RustBlockKind::Function),
            "struct_item" => Some(RustBlockKind::Struct),
            "impl_item" => Some(RustBlockKind::Impl),
            "enum_item" => Some(RustBlockKind::Enum),
            "trait_item" => Some(RustBlockKind::Trait),
            _ => None,
        }
    }

    fn kind_as_str(kind: &RustBlockKind) -> &'static str {
        match kind {
            RustBlockKind::Function => "function",
            RustBlockKind::Struct => "struct",
            RustBlockKind::Impl => "impl",
            RustBlockKind::Enum => "enum",
            RustBlockKind::Trait => "trait",
        }
    }

    fn node_name(node: &Node, source: &[u8]) -> Option<String> {
        if node.kind() == "impl_item" {
            return node
                .child_by_field_name("type")
                .and_then(|n| n.utf8_text(source).ok())
                .map(|s| s.to_string());
        }

        node.child_by_field_name("name")
            .and_then(|n| n.utf8_text(source).ok())
            .map(|s| s.to_string())
    }

    fn collect_symbol_nodes<'a>(&self, root: Node<'a>) -> Vec<Node<'a>> {
        let mut out = Vec::new();
        let mut stack = vec![root];
        while let Some(node) = stack.pop() {
            if Self::kind_for_node(&node).is_some() {
                out.push(node);
            }
            let mut cursor = node.walk();
            for child in node.children(&mut cursor) {
                stack.push(child);
            }
        }
        out
    }

    fn module_path_for_node(node: &Node, source: &[u8]) -> String {
        let mut parts = Vec::new();
        let mut current = *node;
        while let Some(parent) = current.parent() {
            if parent.kind() == "mod_item" {
                if let Some(name) = parent
                    .child_by_field_name("name")
                    .and_then(|n| n.utf8_text(source).ok())
                {
                    parts.push(name.to_string());
                }
            }
            current = parent;
        }
        parts.reverse();
        parts.join("::")
    }

    fn block_hash(block: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(block.as_bytes());
        let digest = hasher.finalize();
        let mut out = String::with_capacity(digest.len() * 2);
        for b in digest {
            out.push_str(&format!("{:02x}", b));
        }
        out
    }

    /// Try rust-analyzer resolution first, then fall back to tree-sitter.
    fn find_target_match(
        &self,
        path: &Path,
        source: &str,
        target: &BlockTarget,
        locator: &BlockLocator,
    ) -> Result<BlockMatch> {
        // Attempt RA-based resolution first
        if let Some(ref ra) = self.ra_client {
            match self.find_target_match_ra(ra, path, source, target, locator) {
                Ok(m) => {
                    debug!(
                        symbol = %target.name,
                        line = m.start_line,
                        "resolved via rust-analyzer"
                    );
                    return Ok(m);
                }
                Err(e) => {
                    warn!(
                        symbol = %target.name,
                        err = %e,
                        "rust-analyzer resolution failed, falling back to tree-sitter"
                    );
                }
            }
        }

        self.find_target_match_ts(source, target, locator)
    }

    /// Resolve a target using rust-analyzer's document symbols.
    fn find_target_match_ra(
        &self,
        ra: &RustAnalyzerClient,
        path: &Path,
        source: &str,
        target: &BlockTarget,
        locator: &BlockLocator,
    ) -> Result<BlockMatch> {
        let query = SymbolQuery {
            name: target.name.clone(),
            kind: Some(target.kind.clone()),
            file: Some(path.to_path_buf()),
            module_path: locator.module_path.clone(),
            line_hint: locator.line_hint.map(|l| l as u32),
        };

        let resolved = ra.resolve_symbol(&query)?;

        // RA gives us line/col ranges. We need byte ranges for the edit.
        // RA's byte range comes from our lsp_position_to_byte conversion,
        // but tree-sitter gives us the full syntactic extent (including body).
        // Use RA's start position to locate the node in tree-sitter for
        // the authoritative byte range (RA range may not include full body).
        let tree = self.parse_source(source)?;
        let root = tree.root_node();
        let bytes = source.as_bytes();

        // Find the tree-sitter node at RA's reported position
        let ra_start_byte = resolved.start_byte;
        let mut best_node: Option<tree_sitter::Node> = None;

        for node in self.collect_symbol_nodes(root) {
            let Some(kind) = Self::kind_for_node(&node) else {
                continue;
            };
            if kind != target.kind {
                continue;
            }
            let Some(name) = Self::node_name(&node, bytes) else {
                continue;
            };
            if name != target.name {
                continue;
            }
            // Pick the node whose start_byte is closest to RA's reported position
            match best_node {
                None => best_node = Some(node),
                Some(ref prev) => {
                    let prev_dist = prev.start_byte().abs_diff(ra_start_byte);
                    let this_dist = node.start_byte().abs_diff(ra_start_byte);
                    if this_dist < prev_dist {
                        best_node = Some(node);
                    }
                }
            }
        }

        let node = best_node.context("rust-analyzer found symbol but tree-sitter could not locate matching node")?;

        Ok(BlockMatch {
            start_byte: node.start_byte(),
            end_byte: node.end_byte(),
            start_line: node.start_position().row + 1,
            module_path: resolved.container.unwrap_or_default(),
        })
    }

    /// Pure tree-sitter resolution (original logic).
    fn find_target_match_ts(
        &self,
        source: &str,
        target: &BlockTarget,
        locator: &BlockLocator,
    ) -> Result<BlockMatch> {
        let tree = self.parse_source(source)?;
        let root = tree.root_node();
        let bytes = source.as_bytes();

        let mut matches = Vec::new();
        for node in self.collect_symbol_nodes(root) {
            let Some(kind) = Self::kind_for_node(&node) else {
                continue;
            };
            if kind != target.kind {
                continue;
            }
            let Some(name) = Self::node_name(&node, bytes) else {
                continue;
            };
            if name == target.name {
                matches.push(BlockMatch {
                    start_byte: node.start_byte(),
                    end_byte: node.end_byte(),
                    start_line: node.start_position().row + 1,
                    module_path: Self::module_path_for_node(&node, bytes),
                });
            }
        }

        if matches.is_empty() {
            bail!("target not found: {:?} {}", target.kind, target.name);
        }

        if let Some(module_path) = &locator.module_path {
            matches.retain(|m| &m.module_path == module_path);
            if matches.is_empty() {
                bail!(
                    "target not found after module_path filter '{}' for {:?} {}",
                    module_path,
                    target.kind,
                    target.name
                );
            }
        }

        if matches.len() == 1 {
            return Ok(matches.remove(0));
        }

        if let Some(line_hint) = locator.line_hint {
            let mut min_dist = usize::MAX;
            let mut best_indices = Vec::new();
            for (idx, m) in matches.iter().enumerate() {
                let dist = m.start_line.abs_diff(line_hint);
                if dist < min_dist {
                    min_dist = dist;
                    best_indices.clear();
                    best_indices.push(idx);
                } else if dist == min_dist {
                    best_indices.push(idx);
                }
            }
            if best_indices.len() == 1 {
                return Ok(matches.remove(best_indices[0]));
            }
            bail!(
                "ambiguous target: {:?} {} matched {} blocks even with line_hint={}",
                target.kind,
                target.name,
                matches.len(),
                line_hint
            );
        }

        bail!(
            "ambiguous target: {:?} {} matched {} blocks; provide module_path or line_hint",
            target.kind,
            target.name,
            matches.len()
        )
    }

    fn validate_source(&self, source: &str) -> Result<()> {
        let tree = self.parse_source(source)?;
        if tree.root_node().has_error() {
            bail!("edited source is not valid Rust syntax");
        }
        Ok(())
    }
}

fn kind_from_str(raw: &str) -> Result<RustBlockKind> {
    match raw {
        "function" => Ok(RustBlockKind::Function),
        "struct" => Ok(RustBlockKind::Struct),
        "impl" => Ok(RustBlockKind::Impl),
        "enum" => Ok(RustBlockKind::Enum),
        "trait" => Ok(RustBlockKind::Trait),
        other => bail!("unsupported rust block kind: {}", other),
    }
}

fn run_post_edit_validations(
    editor: &RustSurgicalEditor,
    path: &Path,
    workspace_root: &Path,
    run_rustfmt: bool,
    run_cargo_check: bool,
) -> Result<ValidationStatus> {
    editor.validate(path)?;

    let mut status = ValidationStatus::syntax_only();

    if run_rustfmt {
        status.rustfmt_ran = true;
        let rustfmt_output = Command::new("rustfmt")
            .arg(path)
            .current_dir(workspace_root)
            .output()
            .with_context(|| format!("failed to spawn rustfmt for {}", path.display()))?;
        status.rustfmt_ok = rustfmt_output.status.success();
        if !status.rustfmt_ok {
            bail!(
                "rustfmt failed for {}: {}",
                path.display(),
                String::from_utf8_lossy(&rustfmt_output.stderr)
            );
        }

        editor.validate(path)?;
    }

    if run_cargo_check {
        status.cargo_check_ran = true;
        let check_output = Command::new("cargo")
            .arg("check")
            .current_dir(workspace_root)
            .output()
            .context("failed to spawn cargo check")?;
        status.cargo_check_ok = check_output.status.success();
        if !status.cargo_check_ok {
            bail!(
                "cargo check failed: {}",
                String::from_utf8_lossy(&check_output.stderr)
            );
        }
    }

    Ok(status)
}

pub struct RustListSymbolsTool {
    workspace_root: PathBuf,
    ra_client: Option<Arc<RustAnalyzerClient>>,
}

impl RustListSymbolsTool {
    pub fn new(workspace_root: PathBuf, ra_client: Option<Arc<RustAnalyzerClient>>) -> Self {
        Self { workspace_root, ra_client }
    }

    fn resolve(&self, path: &str) -> PathBuf {
        self.workspace_root.join(path)
    }
}

#[derive(Deserialize)]
struct ListSymbolsArgs {
    path: String,
}

#[async_trait::async_trait]
impl Tool for RustListSymbolsTool {
    fn name(&self) -> &str {
        "rust_list_symbols"
    }

    fn description(&self) -> &str {
        "List Rust symbols in a file"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: ListSymbolsArgs = serde_json::from_value(args)?;
        let editor = RustSurgicalEditor::new(self.ra_client.clone());
        let symbols = editor.list_symbols(&self.resolve(&args.path))?;
        let output = symbols
            .into_iter()
            .map(|s| format!("{:?} {} [{}-{}]", s.kind, s.name, s.start_line, s.end_line))
            .collect::<Vec<_>>()
            .join("\n");

        Ok(ToolResult {
            name: self.name().to_string(),
            success: true,
            output,
        })
    }
}

pub struct RustReplaceBlockTool {
    workspace_root: PathBuf,
    ra_client: Option<Arc<RustAnalyzerClient>>,
}

impl RustReplaceBlockTool {
    pub fn new(workspace_root: PathBuf, ra_client: Option<Arc<RustAnalyzerClient>>) -> Self {
        Self { workspace_root, ra_client }
    }

    fn resolve(&self, path: &str) -> PathBuf {
        self.workspace_root.join(path)
    }
}

#[derive(Deserialize)]
struct ReplaceBlockArgs {
    path: String,
    kind: String,
    name: String,
    new_block: String,
    #[serde(default)]
    expected_old_hash: Option<String>,
    #[serde(default)]
    expected_old_block: Option<String>,
    #[serde(default)]
    module_path: Option<String>,
    #[serde(default)]
    line_hint: Option<usize>,
    #[serde(default)]
    run_rustfmt: Option<bool>,
    #[serde(default)]
    run_cargo_check: Option<bool>,
}

#[async_trait::async_trait]
impl Tool for RustReplaceBlockTool {
    fn name(&self) -> &str {
        "rust_replace_block"
    }

    fn description(&self) -> &str {
        "Replace a Rust AST block by kind/name"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: ReplaceBlockArgs = serde_json::from_value(args)?;
        let editor = RustSurgicalEditor::new(self.ra_client.clone());
        let target = BlockTarget {
            kind: kind_from_str(&args.kind)?,
            name: args.name,
        };
        let locator = BlockLocator {
            module_path: args.module_path,
            line_hint: args.line_hint,
        };
        let outcome = editor.replace_block(
            &self.resolve(&args.path),
            &target,
            &locator,
            &args.new_block,
            args.expected_old_hash.as_deref(),
            args.expected_old_block.as_deref(),
            args.run_rustfmt.unwrap_or(false),
            args.run_cargo_check.unwrap_or(false),
            &self.workspace_root,
        )?;

        let metadata = serde_json::json!({
            "file": outcome.file,
            "byte_range": {"start": outcome.start_byte, "end": outcome.end_byte},
            "symbol": {
                "kind": RustSurgicalEditor::kind_as_str(&outcome.symbol_kind),
                "name": outcome.symbol,
                "module_path": outcome.symbol_module_path,
            },
            "validation": {
                "rust_syntax_ok": outcome.validation.rust_syntax_ok,
                "rustfmt_ran": outcome.validation.rustfmt_ran,
                "rustfmt_ok": outcome.validation.rustfmt_ok,
                "cargo_check_ran": outcome.validation.cargo_check_ran,
                "cargo_check_ok": outcome.validation.cargo_check_ok,
            },
            "old_block_hash": outcome.old_block_hash,
            "inserted_bytes": outcome.inserted_bytes,
        });

        Ok(ToolResult {
            name: self.name().to_string(),
            success: true,
            output: format!(
                "updated {} bytes in {} at [{}..{}]\nmetadata={}",
                outcome.inserted_bytes,
                outcome.file,
                outcome.start_byte,
                outcome.end_byte,
                metadata
            ),
        })
    }
}

pub struct RustInsertAfterBlockTool {
    workspace_root: PathBuf,
    ra_client: Option<Arc<RustAnalyzerClient>>,
}

impl RustInsertAfterBlockTool {
    pub fn new(workspace_root: PathBuf, ra_client: Option<Arc<RustAnalyzerClient>>) -> Self {
        Self { workspace_root, ra_client }
    }

    fn resolve(&self, path: &str) -> PathBuf {
        self.workspace_root.join(path)
    }
}

#[derive(Deserialize)]
struct InsertAfterArgs {
    path: String,
    kind: String,
    name: String,
    snippet: String,
    #[serde(default)]
    expected_old_hash: Option<String>,
    #[serde(default)]
    expected_old_block: Option<String>,
    #[serde(default)]
    module_path: Option<String>,
    #[serde(default)]
    line_hint: Option<usize>,
    #[serde(default)]
    run_rustfmt: Option<bool>,
    #[serde(default)]
    run_cargo_check: Option<bool>,
}

#[async_trait::async_trait]
impl Tool for RustInsertAfterBlockTool {
    fn name(&self) -> &str {
        "rust_insert_after_block"
    }

    fn description(&self) -> &str {
        "Insert snippet after a Rust AST block"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: InsertAfterArgs = serde_json::from_value(args)?;
        let editor = RustSurgicalEditor::new(self.ra_client.clone());
        let target = BlockTarget {
            kind: kind_from_str(&args.kind)?,
            name: args.name,
        };
        let locator = BlockLocator {
            module_path: args.module_path,
            line_hint: args.line_hint,
        };
        let outcome = editor.insert_after_block(
            &self.resolve(&args.path),
            &target,
            &locator,
            &args.snippet,
            args.expected_old_hash.as_deref(),
            args.expected_old_block.as_deref(),
            args.run_rustfmt.unwrap_or(false),
            args.run_cargo_check.unwrap_or(false),
            &self.workspace_root,
        )?;

        let metadata = serde_json::json!({
            "file": outcome.file,
            "byte_range": {"start": outcome.start_byte, "end": outcome.end_byte},
            "symbol": {
                "kind": RustSurgicalEditor::kind_as_str(&outcome.symbol_kind),
                "name": outcome.symbol,
                "module_path": outcome.symbol_module_path,
            },
            "validation": {
                "rust_syntax_ok": outcome.validation.rust_syntax_ok,
                "rustfmt_ran": outcome.validation.rustfmt_ran,
                "rustfmt_ok": outcome.validation.rustfmt_ok,
                "cargo_check_ran": outcome.validation.cargo_check_ran,
                "cargo_check_ok": outcome.validation.cargo_check_ok,
            },
            "old_block_hash": outcome.old_block_hash,
            "inserted_bytes": outcome.inserted_bytes,
        });

        Ok(ToolResult {
            name: self.name().to_string(),
            success: true,
            output: format!(
                "inserted {} bytes in {} after byte {}\nmetadata={}",
                outcome.inserted_bytes, outcome.file, outcome.start_byte, metadata
            ),
        })
    }
}

pub struct RustValidateFileTool {
    workspace_root: PathBuf,
    ra_client: Option<Arc<RustAnalyzerClient>>,
}

impl RustValidateFileTool {
    pub fn new(workspace_root: PathBuf, ra_client: Option<Arc<RustAnalyzerClient>>) -> Self {
        Self { workspace_root, ra_client }
    }
}

#[derive(Deserialize)]
struct ValidateArgs {
    path: String,
}

#[async_trait::async_trait]
impl Tool for RustValidateFileTool {
    fn name(&self) -> &str {
        "rust_validate_file"
    }

    fn description(&self) -> &str {
        "Validate Rust file syntax"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: ValidateArgs = serde_json::from_value(args)?;
        let editor = RustSurgicalEditor::new(self.ra_client.clone());
        let path = self.workspace_root.join(args.path);
        match editor.validate(&path) {
            Ok(()) => Ok(ToolResult {
                name: self.name().to_string(),
                success: true,
                output: format!("valid Rust syntax: {}", path.display()),
            }),
            Err(e) => Ok(ToolResult {
                name: self.name().to_string(),
                success: false,
                output: format!("invalid Rust syntax: {}", e),
            }),
        }
    }
}

impl SurgicalEditor for RustSurgicalEditor {
    fn list_symbols(&self, path: &Path) -> Result<Vec<SymbolInfo>> {
        // Try RA first for richer symbol info
        if let Some(ref ra) = self.ra_client {
            match ra.document_symbols(path) {
                Ok(ra_symbols) => {
                    debug!(path = %path.display(), count = ra_symbols.len(), "symbols via rust-analyzer");
                    let symbols = ra_symbols
                        .into_iter()
                        .map(|s| SymbolInfo {
                            kind: s.kind,
                            name: s.name,
                            start_line: s.start_line as usize + 1, // RA is 0-indexed
                            end_line: s.end_line as usize + 1,
                        })
                        .collect();
                    return Ok(symbols);
                }
                Err(e) => {
                    warn!(
                        path = %path.display(),
                        err = %e,
                        "rust-analyzer list_symbols failed, falling back to tree-sitter"
                    );
                }
            }
        }

        // Tree-sitter fallback
        let source = std::fs::read_to_string(path)
            .with_context(|| format!("failed to read {}", path.display()))?;
        let tree = self.parse_source(&source)?;
        let bytes = source.as_bytes();
        let root = tree.root_node();

        let mut symbols = Vec::new();
        for node in self.collect_symbol_nodes(root) {
            let Some(kind) = Self::kind_for_node(&node) else {
                continue;
            };
            let Some(name) = Self::node_name(&node, bytes) else {
                continue;
            };
            symbols.push(SymbolInfo {
                kind,
                name,
                start_line: node.start_position().row + 1,
                end_line: node.end_position().row + 1,
            });
        }

        symbols.sort_by(|a, b| a.start_line.cmp(&b.start_line));
        Ok(symbols)
    }

    fn replace_block(
        &self,
        path: &Path,
        target: &BlockTarget,
        locator: &BlockLocator,
        new_block: &str,
        expected_old_hash: Option<&str>,
        expected_old_block: Option<&str>,
        run_rustfmt: bool,
        run_cargo_check: bool,
        workspace_root: &Path,
    ) -> Result<EditOutcome> {
        let source = std::fs::read_to_string(path)
            .with_context(|| format!("failed to read {}", path.display()))?;
        let target_match = self.find_target_match(path, &source, target, locator)?;
        let start = target_match.start_byte;
        let end = target_match.end_byte;
        let old_block = &source[start..end];
        let old_block_hash = Self::block_hash(old_block);

        if let Some(expected) = expected_old_hash {
            if old_block_hash != expected {
                bail!(
                    "stale target: expected_old_hash={} but found {} for {:?} {}",
                    expected,
                    old_block_hash,
                    target.kind,
                    target.name
                );
            }
        }
        if let Some(expected) = expected_old_block {
            if old_block != expected {
                bail!(
                    "stale target: expected_old_block mismatch for {:?} {}",
                    target.kind,
                    target.name
                );
            }
        }

        let mut edited = String::with_capacity(source.len() + new_block.len());
        edited.push_str(&source[..start]);
        edited.push_str(new_block);
        edited.push_str(&source[end..]);

        self.validate_source(&edited)?;
        std::fs::write(path, edited.as_bytes())
            .with_context(|| format!("failed to write {}", path.display()))?;
        let validation =
            run_post_edit_validations(self, path, workspace_root, run_rustfmt, run_cargo_check)?;

        Ok(EditOutcome {
            file: path.display().to_string(),
            start_byte: start,
            end_byte: end,
            inserted_bytes: new_block.len(),
            symbol: target.name.clone(),
            symbol_kind: target.kind.clone(),
            symbol_module_path: target_match.module_path,
            validation,
            old_block_hash,
        })
    }

    fn insert_after_block(
        &self,
        path: &Path,
        target: &BlockTarget,
        locator: &BlockLocator,
        snippet: &str,
        expected_old_hash: Option<&str>,
        expected_old_block: Option<&str>,
        run_rustfmt: bool,
        run_cargo_check: bool,
        workspace_root: &Path,
    ) -> Result<EditOutcome> {
        let source = std::fs::read_to_string(path)
            .with_context(|| format!("failed to read {}", path.display()))?;
        let target_match = self.find_target_match(path, &source, target, locator)?;
        let end = target_match.end_byte;
        let old_block = &source[target_match.start_byte..target_match.end_byte];
        let old_block_hash = Self::block_hash(old_block);

        if let Some(expected) = expected_old_hash {
            if old_block_hash != expected {
                bail!(
                    "stale target: expected_old_hash={} but found {} for {:?} {}",
                    expected,
                    old_block_hash,
                    target.kind,
                    target.name
                );
            }
        }
        if let Some(expected) = expected_old_block {
            if old_block != expected {
                bail!(
                    "stale target: expected_old_block mismatch for {:?} {}",
                    target.kind,
                    target.name
                );
            }
        }

        let mut edited = String::with_capacity(source.len() + snippet.len() + 1);
        edited.push_str(&source[..end]);
        edited.push('\n');
        edited.push_str(snippet);
        edited.push_str(&source[end..]);

        self.validate_source(&edited)?;
        std::fs::write(path, edited.as_bytes())
            .with_context(|| format!("failed to write {}", path.display()))?;
        let validation =
            run_post_edit_validations(self, path, workspace_root, run_rustfmt, run_cargo_check)?;

        Ok(EditOutcome {
            file: path.display().to_string(),
            start_byte: end,
            end_byte: end,
            inserted_bytes: snippet.len() + 1,
            symbol: target.name.clone(),
            symbol_kind: target.kind.clone(),
            symbol_module_path: target_match.module_path,
            validation,
            old_block_hash,
        })
    }

    fn validate(&self, path: &Path) -> Result<()> {
        let source = std::fs::read_to_string(path)
            .with_context(|| format!("failed to read {}", path.display()))?;
        self.validate_source(&source)
    }
}
