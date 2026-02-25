use ratatui::layout::Rect;
use ratatui::style::{Modifier, Style};
use ratatui::text::Span;
use ratatui::widgets::{Block, Borders};
use ratatui::Frame;
use tui_textarea::TextArea;

use crate::ui::theme::Theme;

pub struct InputPanel {
    pub textarea: TextArea<'static>,
    pub focused: bool,
    target_agent: String,
    mention_matches: Vec<String>,
    mention_index: usize,
}

impl InputPanel {
    pub fn new() -> Self {
        let mut textarea = TextArea::default();
        textarea.set_cursor_line_style(Style::default());
        textarea.set_placeholder_text("Type a message... (Enter to send, Shift+Enter for newline)");

        Self {
            textarea,
            focused: false,
            target_agent: "planner".to_string(),
            mention_matches: Vec::new(),
            mention_index: 0,
        }
    }

    pub fn set_target_agent(&mut self, agent: &str) {
        self.target_agent = agent.to_string();
    }

    /// Take the current input text and clear the textarea.
    pub fn take_input(&mut self) -> String {
        let lines = self.textarea.lines().to_vec();
        let text = lines.join("\n");

        // Clear textarea
        self.textarea = TextArea::default();
        self.textarea.set_cursor_line_style(Style::default());
        self.textarea
            .set_placeholder_text("Type a message... (Enter to send, Shift+Enter for newline)");
        self.mention_matches.clear();
        self.mention_index = 0;

        text
    }

    pub fn is_empty(&self) -> bool {
        self.textarea.lines().iter().all(|l| l.trim().is_empty())
    }

    pub fn text(&self) -> String {
        self.textarea.lines().join("\n")
    }

    pub fn refresh_mentions(&mut self, agent_ids: &[String]) {
        let text = self.text();
        let Some(query) = trailing_mention_query(&text) else {
            self.mention_matches.clear();
            self.mention_index = 0;
            return;
        };

        let q = query.to_lowercase();
        let mut matches: Vec<String> = agent_ids
            .iter()
            .filter(|id| id.to_lowercase().starts_with(&q))
            .cloned()
            .collect();
        matches.sort();

        self.mention_matches = matches;
        if self.mention_index >= self.mention_matches.len() {
            self.mention_index = 0;
        }
    }

    pub fn has_mention_suggestions(&self) -> bool {
        !self.mention_matches.is_empty()
    }

    pub fn apply_active_mention(&mut self) {
        if self.mention_matches.is_empty() {
            return;
        }
        let choice = self.mention_matches[self.mention_index].clone();
        let text = self.text();
        if let Some((start, _query)) = trailing_mention_span(&text) {
            let mut replaced = String::new();
            replaced.push_str(&text[..start]);
            replaced.push('@');
            replaced.push_str(&choice);
            replaced.push(' ');
            self.set_text(replaced);
            self.mention_matches.clear();
            self.mention_index = 0;
        }
    }

    pub fn cycle_mention_next(&mut self) {
        if self.mention_matches.is_empty() {
            return;
        }
        self.mention_index = (self.mention_index + 1) % self.mention_matches.len();
    }

    fn set_text(&mut self, text: String) {
        let lines: Vec<String> = if text.contains('\n') {
            text.lines().map(|s| s.to_string()).collect()
        } else {
            vec![text]
        };
        let mut textarea = TextArea::from(lines);
        textarea.set_cursor_line_style(Style::default());
        textarea.set_placeholder_text("Type a message... (Enter to send, Shift+Enter for newline)");
        self.textarea = textarea;
    }

    pub fn draw(&mut self, frame: &mut Frame, area: Rect, theme: &Theme) {
        let border_style = if self.focused {
            theme.focused_border()
        } else {
            theme.unfocused_border()
        };

        let title = if self.mention_matches.is_empty() {
            format!(" → @{} ", self.target_agent)
        } else {
            let preview: Vec<String> = self
                .mention_matches
                .iter()
                .take(3)
                .enumerate()
                .map(|(i, id)| {
                    if i == self.mention_index {
                        format!("[@{}]", id)
                    } else {
                        format!("@{}", id)
                    }
                })
                .collect();
            format!(
                " → @{}  mention:{} (Tab accept) ",
                self.target_agent,
                preview.join(" ")
            )
        };
        let block = Block::default()
            .title(Span::styled(
                title,
                Style::default()
                    .fg(theme.agent_color(&self.target_agent))
                    .add_modifier(Modifier::BOLD),
            ))
            .borders(Borders::ALL)
            .border_style(border_style);

        self.textarea.set_block(block);
        self.textarea.set_style(Style::default().fg(theme.text()));
        self.textarea.set_cursor_style(if self.focused {
            Style::default().fg(theme.bg()).bg(theme.text())
        } else {
            Style::default()
        });

        frame.render_widget(&self.textarea, area);
    }
}

fn trailing_mention_query(text: &str) -> Option<String> {
    trailing_mention_span(text).map(|(_, q)| q)
}

fn trailing_mention_span(text: &str) -> Option<(usize, String)> {
    let at = text.rfind('@')?;
    if at > 0 {
        let prev = text[..at].chars().next_back()?;
        if !prev.is_whitespace() {
            return None;
        }
    }
    let suffix = &text[at + 1..];
    if suffix.chars().any(|c| c.is_whitespace()) {
        return None;
    }
    Some((at, suffix.to_string()))
}
