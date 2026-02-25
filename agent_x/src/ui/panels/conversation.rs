use ratatui::layout::Rect;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{
    Block, Borders, Paragraph, Scrollbar, ScrollbarOrientation, ScrollbarState,
};
use ratatui::Frame;

use crate::ui::highlight::Highlighter;
use crate::ui::message::ChatMessage;
use crate::ui::theme::Theme;

pub struct ConversationPanel {
    pub messages: Vec<ChatMessage>,
    pub focused: bool,
    pub scroll_offset: u16,
    /// Cached rendered lines. Invalidated on new message or streaming update.
    rendered_cache: Vec<Line<'static>>,
    cache_valid: bool,
    filter: ConversationFilter,
}

#[derive(Clone)]
pub enum ConversationFilter {
    All,
    Agent(String),
    Thread(String),
}

impl ConversationPanel {
    pub fn new() -> Self {
        Self {
            messages: Vec::new(),
            focused: true,
            scroll_offset: 0,
            rendered_cache: Vec::new(),
            cache_valid: false,
            filter: ConversationFilter::All,
        }
    }

    pub fn push_message(&mut self, msg: ChatMessage) {
        self.messages.push(msg);
        self.cache_valid = false;
        // Auto-scroll to bottom
        self.scroll_to_bottom();
    }

    pub fn update_streaming(&mut self, agent_id: &str, token: &str) {
        // Find or create a streaming message for this agent
        if let Some(msg) = self
            .messages
            .iter_mut()
            .rev()
            .find(|m| m.agent_id == agent_id && m.is_streaming)
        {
            msg.content.push_str(token);
        } else {
            // Create new streaming message
            let mut msg = ChatMessage::from_user("", String::new());
            msg.agent_id = agent_id.to_string();
            msg.from_id = agent_id.to_string();
            msg.to_id = "user".to_string();
            msg.role = crate::ui::message::MessageRole::Assistant;
            msg.content = token.to_string();
            msg.is_streaming = true;
            msg.kind = crate::runtime::bus::MessageKind::StreamChunk;
            msg.thread_id = String::new();
            msg.parent_id = None;
            self.messages.push(msg);
        }
        self.cache_valid = false;
    }

    pub fn finish_streaming(&mut self, agent_id: &str) {
        if let Some(idx) = self
            .messages
            .iter()
            .rposition(|m| m.agent_id == agent_id && m.is_streaming)
        {
            // Streaming text is model action JSON, while the canonical
            // user-visible message arrives as a regular bus message.
            // Remove the transient stream bubble to avoid duplicate/raw JSON lines.
            self.messages.remove(idx);
        }
        self.cache_valid = false;
    }

    pub fn scroll_up(&mut self, amount: u16) {
        self.scroll_offset = self.scroll_offset.saturating_add(amount);
    }

    pub fn scroll_down(&mut self, amount: u16) {
        self.scroll_offset = self.scroll_offset.saturating_sub(amount);
    }

    pub fn scroll_to_bottom(&mut self) {
        self.scroll_offset = 0;
    }

    fn ensure_cache(&mut self, theme: &Theme, highlighter: &Highlighter, width: usize) {
        if self.cache_valid {
            return;
        }

        self.rendered_cache.clear();

        if self.messages.is_empty() {
            // Welcome message
            self.rendered_cache.push(Line::from(""));
            self.rendered_cache.push(Line::from(Span::styled(
                "  Welcome to Agent-X".to_string(),
                Style::default()
                    .fg(theme.mauve())
                    .add_modifier(Modifier::BOLD),
            )));
            self.rendered_cache.push(Line::from(""));
            self.rendered_cache.push(Line::from(Span::styled(
                "  Type a message and press Enter to begin.".to_string(),
                theme.muted_style(),
            )));
            self.rendered_cache.push(Line::from(Span::styled(
                "  Press Tab to switch panels, ? for help.".to_string(),
                theme.muted_style(),
            )));
        } else {
            let filter = self.filter.clone();
            for msg in self
                .messages
                .iter()
                .filter(|m| matches_filter_with(&filter, m))
            {
                let rendered = msg.render(theme, highlighter, width);
                self.rendered_cache.extend(rendered);
            }
        }

        self.cache_valid = true;
    }

    pub fn draw(
        &mut self,
        frame: &mut Frame,
        area: Rect,
        theme: &Theme,
        highlighter: &Highlighter,
    ) {
        let content_width = area.width.saturating_sub(2) as usize;
        self.ensure_cache(theme, highlighter, content_width);

        let border_style = if self.focused {
            theme.focused_border()
        } else {
            theme.unfocused_border()
        };

        let block = Block::default()
            .title(Span::styled(
                format!(" Conversation [{}] ", self.filter_label()),
                Style::default()
                    .fg(theme.text())
                    .add_modifier(Modifier::BOLD),
            ))
            .borders(Borders::ALL)
            .border_style(border_style);

        let total_lines = self.rendered_cache.len() as u16;
        let visible_height = area.height.saturating_sub(2);

        // Calculate scroll position (we show bottom by default, scroll_offset moves up)
        let max_scroll = total_lines.saturating_sub(visible_height);
        let actual_scroll = max_scroll.saturating_sub(self.scroll_offset);

        let paragraph = Paragraph::new(self.rendered_cache.clone())
            .block(block)
            .scroll((actual_scroll, 0));

        frame.render_widget(paragraph, area);

        // Scrollbar
        if total_lines > visible_height {
            let mut scrollbar_state = ScrollbarState::new(total_lines as usize)
                .position(actual_scroll as usize)
                .viewport_content_length(visible_height as usize);

            let scrollbar = Scrollbar::new(ScrollbarOrientation::VerticalRight)
                .begin_symbol(Some("↑"))
                .end_symbol(Some("↓"));

            frame.render_stateful_widget(
                scrollbar,
                area.inner(ratatui::layout::Margin {
                    vertical: 1,
                    horizontal: 0,
                }),
                &mut scrollbar_state,
            );
        }
    }

    pub fn line_text_at(&self, area: Rect, row: u16) -> Option<String> {
        if row <= area.y || row >= area.y + area.height {
            return None;
        }

        let total_lines = self.rendered_cache.len() as u16;
        if total_lines == 0 {
            return None;
        }
        let visible_height = area.height.saturating_sub(2);
        if visible_height == 0 {
            return None;
        }

        let max_scroll = total_lines.saturating_sub(visible_height);
        let actual_scroll = max_scroll.saturating_sub(self.scroll_offset);
        let content_row = row.saturating_sub(area.y + 1);
        let idx = actual_scroll.saturating_add(content_row) as usize;
        let line = self.rendered_cache.get(idx)?;
        let text = line
            .spans
            .iter()
            .map(|s| s.content.as_ref())
            .collect::<String>();
        let trimmed = text.trim().to_string();
        if trimmed.is_empty() {
            None
        } else {
            Some(trimmed)
        }
    }

    pub fn annotate_message(&mut self, message_id: &str, annotation: &str) {
        if let Some(msg) = self.messages.iter_mut().find(|m| m.id == message_id) {
            if !msg.content.contains(annotation) {
                msg.content.push_str("\n\n");
                msg.content.push_str(annotation);
                self.cache_valid = false;
            }
        }
    }

    pub fn set_filter_all(&mut self) {
        self.filter = ConversationFilter::All;
        self.cache_valid = false;
    }

    pub fn set_filter_agent(&mut self, agent_id: impl Into<String>) {
        self.filter = ConversationFilter::Agent(agent_id.into());
        self.cache_valid = false;
    }

    pub fn set_filter_thread(&mut self, thread_id: impl Into<String>) {
        self.filter = ConversationFilter::Thread(thread_id.into());
        self.cache_valid = false;
    }

    pub fn latest_thread_for_agent(&self, agent_id: &str) -> Option<String> {
        self.messages
            .iter()
            .rev()
            .find(|m| (m.from_id == agent_id || m.to_id == agent_id) && !m.thread_id.is_empty())
            .map(|m| m.thread_id.clone())
    }

    fn filter_label(&self) -> String {
        match &self.filter {
            ConversationFilter::All => "all".to_string(),
            ConversationFilter::Agent(id) => format!("agent:{}", id),
            ConversationFilter::Thread(id) => format!("thread:{}", truncate(id, 10)),
        }
    }
}

fn matches_filter_with(filter: &ConversationFilter, m: &ChatMessage) -> bool {
    match filter {
        ConversationFilter::All => true,
        ConversationFilter::Agent(id) => m.from_id == *id || m.to_id == *id,
        ConversationFilter::Thread(thread_id) => !thread_id.is_empty() && m.thread_id == *thread_id,
    }
}

fn truncate(s: &str, max: usize) -> String {
    if s.len() <= max {
        s.to_string()
    } else {
        format!("{}...", &s[..max])
    }
}
