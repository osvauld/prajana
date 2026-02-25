use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};

use crate::runtime::bus::{Envelope, MessageKind};

use super::highlight::Highlighter;
use super::markdown::render_markdown;
use super::theme::Theme;

/// A structured chat message for the UI.
#[derive(Clone, Debug)]
pub struct ChatMessage {
    pub id: String,
    pub agent_id: String,
    pub from_id: String,
    pub to_id: String,
    pub thread_id: String,
    pub parent_id: Option<String>,
    pub role: MessageRole,
    pub content: String,
    pub kind: MessageKind,
    pub tool_name: Option<String>,
    pub metadata: Option<serde_json::Value>,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub is_streaming: bool,
}

#[derive(Clone, Debug, PartialEq)]
pub enum MessageRole {
    User,
    Assistant,
    Tool,
    System,
}

impl ChatMessage {
    pub fn from_user(target: &str, content: String) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            agent_id: target.to_string(),
            from_id: "user".to_string(),
            to_id: target.to_string(),
            thread_id: String::new(),
            parent_id: None,
            role: MessageRole::User,
            content,
            kind: MessageKind::UserInstruction,
            tool_name: None,
            metadata: None,
            timestamp: chrono::Utc::now(),
            is_streaming: false,
        }
    }

    pub fn from_envelope(env: &Envelope) -> Self {
        let role = match env.kind {
            MessageKind::UserInstruction => MessageRole::User,
            MessageKind::ToolResult | MessageKind::ToolCall => MessageRole::Tool,
            MessageKind::Error => MessageRole::System,
            _ => MessageRole::Assistant,
        };

        // Extract tool name from tool results
        let tool_name = if matches!(env.kind, MessageKind::ToolResult | MessageKind::ToolCall) {
            // Try to extract tool name from content prefix like "[tool_name success=true]"
            env.payload
                .content
                .strip_prefix('[')
                .and_then(|s| s.split_whitespace().next())
                .map(|s| s.to_string())
        } else {
            None
        };

        Self {
            id: env.id.clone(),
            agent_id: env.from.clone(),
            from_id: env.from.clone(),
            to_id: env.to.clone(),
            thread_id: env.thread_id.clone(),
            parent_id: env.parent_id.clone(),
            role,
            content: env.payload.content.clone(),
            kind: env.kind.clone(),
            tool_name,
            metadata: env.payload.data.clone(),
            timestamp: env.timestamp,
            is_streaming: false,
        }
    }

    /// Render this message into styled ratatui Lines.
    pub fn render(
        &self,
        theme: &Theme,
        highlighter: &Highlighter,
        width: usize,
    ) -> Vec<Line<'static>> {
        let mut lines = Vec::new();
        let content_width = width.saturating_sub(4); // account for border + padding

        // Header line
        lines.push(self.render_header(theme));

        // Content based on role and type
        match self.role {
            MessageRole::User => {
                let content_lines =
                    render_markdown(&self.content, theme, highlighter, content_width);
                for line in content_lines {
                    lines.push(add_border(line, theme.user_border()));
                }
            }
            MessageRole::Assistant => {
                let content_lines =
                    render_markdown(&self.content, theme, highlighter, content_width);
                for line in content_lines {
                    lines.push(add_border(line, theme.assistant_border(&self.agent_id)));
                }
            }
            MessageRole::Tool => {
                let tool_lines = self.render_tool_result(theme, highlighter, content_width);
                for line in tool_lines {
                    lines.push(add_border(line, theme.tool_border()));
                }
            }
            MessageRole::System => {
                if matches!(self.kind, MessageKind::Error) {
                    lines.push(add_border(
                        Line::from(Span::styled(self.content.clone(), theme.error_style())),
                        Style::default().fg(theme.red()),
                    ));
                } else {
                    lines.push(add_border(
                        Line::from(Span::styled(self.content.clone(), theme.muted_style())),
                        theme.tool_border(),
                    ));
                }
            }
        }

        // Spacer after message
        lines.push(Line::from(""));
        lines
    }

    fn render_header(&self, theme: &Theme) -> Line<'static> {
        let time = self.timestamp.format("%H:%M:%S").to_string();
        let mut spans = vec![];

        match self.role {
            MessageRole::User => {
                spans.push(Span::styled("▌ ".to_string(), theme.user_border()));
                spans.push(Span::styled(
                    "you".to_string(),
                    theme.user_border().add_modifier(Modifier::BOLD),
                ));
                spans.push(Span::styled(" -> ".to_string(), theme.muted_style()));
                spans.push(Span::styled(
                    format!("@{}", self.to_id),
                    theme
                        .assistant_border(&self.to_id)
                        .add_modifier(Modifier::BOLD),
                ));
            }
            MessageRole::Assistant => {
                spans.push(Span::styled(
                    "▌ ".to_string(),
                    theme.assistant_border(&self.from_id),
                ));
                spans.push(Span::styled(
                    format!("@{}", self.from_id),
                    theme
                        .assistant_border(&self.from_id)
                        .add_modifier(Modifier::BOLD),
                ));
                spans.push(Span::styled(" -> ".to_string(), theme.muted_style()));
                spans.push(Span::styled(
                    format!("@{}", self.to_id),
                    theme
                        .assistant_border(&self.to_id)
                        .add_modifier(Modifier::BOLD),
                ));
            }
            MessageRole::Tool => {
                let tool = self.tool_name.as_deref().unwrap_or("tool");
                spans.push(Span::styled("▌ ".to_string(), theme.tool_border()));
                spans.push(Span::styled(
                    format!("⚙ {}", tool),
                    theme.tool_border().add_modifier(Modifier::BOLD),
                ));
                spans.push(Span::styled("  ".to_string(), theme.muted_style()));
                spans.push(Span::styled(
                    format!("@{}", self.from_id),
                    theme.assistant_border(&self.from_id),
                ));
                spans.push(Span::styled(" -> ".to_string(), theme.muted_style()));
                spans.push(Span::styled(
                    format!("@{}", self.to_id),
                    theme.assistant_border(&self.to_id),
                ));
            }
            MessageRole::System => {
                spans.push(Span::styled("▌ ".to_string(), theme.error_style()));
                spans.push(Span::styled(
                    "system".to_string(),
                    theme.error_style().add_modifier(Modifier::BOLD),
                ));
            }
        }

        spans.push(Span::styled(format!("  {}", time), theme.muted_style()));
        if self.is_streaming {
            spans.push(Span::styled("  ●".to_string(), theme.status_streaming()));
        }

        Line::from(spans)
    }

    fn render_tool_result(
        &self,
        theme: &Theme,
        highlighter: &Highlighter,
        width: usize,
    ) -> Vec<Line<'static>> {
        let mut lines = Vec::new();

        // Detect tool type and render accordingly
        let tool_name = self.tool_name.as_deref().unwrap_or("");

        match tool_name {
            "shell" | "bash" => {
                // Render as bash code block
                let content = strip_tool_header(&self.content);
                let highlighted = highlighter.highlight_code(&content, "bash", theme);
                let max_lines = 10;
                let total = highlighted.len();
                for (i, line) in highlighted.into_iter().enumerate() {
                    if i >= max_lines {
                        lines.push(Line::from(Span::styled(
                            format!("  ... +{} more lines", total - max_lines),
                            theme.muted_style(),
                        )));
                        break;
                    }
                    let mut prefixed = vec![Span::raw("  ".to_string())];
                    prefixed.extend(line.spans.into_iter());
                    lines.push(Line::from(prefixed));
                }
            }
            "rust_replace_block" | "rust_insert_after_block" | "rust_validate_file" => {
                // Render metadata if available
                if let Some(ref data) = self.metadata {
                    let json = serde_json::to_string_pretty(data).unwrap_or_default();
                    let highlighted = highlighter.highlight_code(&json, "json", theme);
                    for line in highlighted.into_iter().take(12) {
                        let mut prefixed = vec![Span::raw("  ".to_string())];
                        prefixed.extend(line.spans.into_iter());
                        lines.push(Line::from(prefixed));
                    }
                } else {
                    let content = strip_tool_header(&self.content);
                    for line_str in content.lines().take(10) {
                        lines.push(Line::from(Span::styled(
                            format!("  {}", line_str),
                            Style::default().fg(theme.text()),
                        )));
                    }
                }

                // Show validation badge
                if let Some(ref data) = self.metadata {
                    if let Some(validation) = data.get("validation") {
                        let syntax_ok = validation
                            .get("rust_syntax_ok")
                            .and_then(|v| v.as_bool())
                            .unwrap_or(false);
                        let cargo_ok = validation.get("cargo_check_ok").and_then(|v| v.as_bool());

                        let badge = if syntax_ok {
                            Span::styled(" ✓ syntax ", Style::default().fg(theme.green()))
                        } else {
                            Span::styled(" ✗ syntax ", theme.error_style())
                        };
                        let mut badge_line = vec![Span::raw("  ".to_string()), badge];

                        if let Some(ok) = cargo_ok {
                            badge_line.push(if ok {
                                Span::styled(" ✓ cargo ", Style::default().fg(theme.green()))
                            } else {
                                Span::styled(" ✗ cargo ", theme.error_style())
                            });
                        }
                        lines.push(Line::from(badge_line));
                    }
                }
            }
            "read_file" => {
                let content = strip_tool_header(&self.content);
                // Try to detect language from first line (path hint)
                let lang = detect_lang_from_content(&content);
                let highlighted = highlighter.highlight_code(&content, lang, theme);
                let max_lines = 10;
                let total = highlighted.len();
                for (i, line) in highlighted.into_iter().enumerate() {
                    if i >= max_lines {
                        lines.push(Line::from(Span::styled(
                            format!("  ... +{} more lines", total - max_lines),
                            theme.muted_style(),
                        )));
                        break;
                    }
                    let mut prefixed = vec![Span::raw("  ".to_string())];
                    prefixed.extend(line.spans.into_iter());
                    lines.push(Line::from(prefixed));
                }
            }
            "call_agent" => {
                lines.push(Line::from(Span::styled(
                    format!("  {}", self.content.replace('\n', " ")),
                    Style::default().fg(theme.teal()),
                )));
            }
            _ => {
                // Default: muted plain text, truncated
                let content = strip_tool_header(&self.content);
                for line_str in content.lines().take(8) {
                    lines.push(Line::from(Span::styled(
                        format!("  {}", line_str),
                        theme.muted_style(),
                    )));
                }
                let total_lines = content.lines().count();
                if total_lines > 8 {
                    lines.push(Line::from(Span::styled(
                        format!("  ... +{} more lines", total_lines - 8),
                        theme.muted_style(),
                    )));
                }
            }
        }

        if lines.is_empty() {
            lines.push(Line::from(Span::styled(
                "  (empty result)".to_string(),
                theme.muted_style(),
            )));
        }

        lines
    }
}

/// Add a thick left border to a line.
fn add_border(line: Line<'static>, style: Style) -> Line<'static> {
    let mut spans = vec![Span::styled("▌ ".to_string(), style)];
    spans.extend(line.spans.into_iter());
    Line::from(spans)
}

/// Strip the "[tool_name success=...]\n" header from tool output.
fn strip_tool_header(content: &str) -> String {
    if content.starts_with('[') {
        if let Some(idx) = content.find("]\n") {
            return content[idx + 2..].to_string();
        }
    }
    content.to_string()
}

/// Guess language from content for syntax highlighting.
fn detect_lang_from_content(content: &str) -> &str {
    let first_line = content.lines().next().unwrap_or("");
    if first_line.contains(".rs") {
        "rust"
    } else if first_line.contains(".py") {
        "python"
    } else if first_line.contains(".ts") || first_line.contains(".tsx") {
        "typescript"
    } else if first_line.contains(".js") || first_line.contains(".jsx") {
        "javascript"
    } else if first_line.contains(".go") {
        "go"
    } else if first_line.contains(".toml") {
        "toml"
    } else if first_line.contains(".json") {
        "json"
    } else if first_line.contains(".md") {
        "markdown"
    } else {
        "text"
    }
}
