use ratatui::layout::Rect;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::Paragraph;
use ratatui::Frame;

use crate::runtime::bus::AgentStatus;
use crate::ui::theme::Theme;

const SPINNER_FRAMES: &[&str] = &["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

pub struct StatusBar {
    pub session: String,
    pub selected_agent: String,
    pub agent_status: AgentStatus,
    pub tick: usize,
    pub notification: Option<Notification>,
    pub pending_questions: usize,
}

pub struct Notification {
    pub level: NotificationLevel,
    pub text: String,
    pub ttl_ticks: u16,
}

#[derive(Clone, Copy)]
pub enum NotificationLevel {
    Info,
    Warn,
    Error,
}

impl StatusBar {
    pub fn new() -> Self {
        Self {
            session: "default".to_string(),
            selected_agent: "planner".to_string(),
            agent_status: AgentStatus::Idle,
            tick: 0,
            notification: None,
            pending_questions: 0,
        }
    }

    pub fn tick(&mut self) {
        self.tick = self.tick.wrapping_add(1);
        if let Some(n) = self.notification.as_mut() {
            n.ttl_ticks = n.ttl_ticks.saturating_sub(1);
            if n.ttl_ticks == 0 {
                self.notification = None;
            }
        }
    }

    pub fn notify(&mut self, level: NotificationLevel, text: impl Into<String>) {
        self.notification = Some(Notification {
            level,
            text: text.into(),
            ttl_ticks: 80,
        });
    }

    pub fn draw(&self, frame: &mut Frame, area: Rect, theme: &Theme) {
        let spinner_idx = self.tick / 2 % SPINNER_FRAMES.len();

        let (status_text, status_style) = match &self.agent_status {
            AgentStatus::Idle => ("idle".to_string(), theme.status_idle()),
            AgentStatus::Thinking => (
                format!("{} thinking...", SPINNER_FRAMES[spinner_idx]),
                theme.status_thinking(),
            ),
            AgentStatus::Streaming => (
                format!("{} streaming...", SPINNER_FRAMES[spinner_idx]),
                theme.status_streaming(),
            ),
            AgentStatus::WaitingForTool => (
                format!("{} running tool...", SPINNER_FRAMES[spinner_idx]),
                theme.status_tool(),
            ),
            AgentStatus::Error(e) => (format!("error: {}", truncate(e, 40)), theme.status_error()),
        };

        let mut spans = vec![
            Span::styled(
                " Agent-X ",
                Style::default()
                    .fg(theme.mauve())
                    .add_modifier(Modifier::BOLD),
            ),
            Span::styled("│ ", Style::default().fg(theme.surface1())),
            Span::styled(format!("session:{} ", self.session), theme.label_style()),
            Span::styled("│ ", Style::default().fg(theme.surface1())),
            Span::styled(
                format!("@{} ", self.selected_agent),
                Style::default()
                    .fg(theme.agent_color(&self.selected_agent))
                    .add_modifier(Modifier::BOLD),
            ),
            Span::styled(status_text, status_style),
            Span::styled("│ ", Style::default().fg(theme.surface1())),
            Span::styled(
                format!("pending:{} ", self.pending_questions),
                if self.pending_questions > 0 {
                    theme.status_tool().add_modifier(Modifier::BOLD)
                } else {
                    theme.muted_style()
                },
            ),
            Span::styled("│ ", Style::default().fg(theme.surface1())),
            Span::styled(
                " Tab:panels  1/2/3:filter  r:reply  ?:help  Ctrl-C:quit ",
                theme.muted_style(),
            ),
        ];

        if let Some(n) = &self.notification {
            let (tag, style) = match n.level {
                NotificationLevel::Info => (" INFO ", theme.status_streaming()),
                NotificationLevel::Warn => (" WARN ", theme.status_tool()),
                NotificationLevel::Error => (" ERROR ", theme.status_error()),
            };
            spans.push(Span::styled("│ ", Style::default().fg(theme.surface1())));
            spans.push(Span::styled(tag, style.add_modifier(Modifier::BOLD)));
            spans.push(Span::styled(
                format!(" {}", truncate(&n.text, 80)),
                theme.muted_style(),
            ));
        }

        let line = Line::from(spans);

        let bar = Paragraph::new(line).style(Style::default().bg(theme.surface0()));

        frame.render_widget(bar, area);
    }
}

fn truncate(s: &str, max: usize) -> String {
    if s.len() <= max {
        s.to_string()
    } else {
        format!("{}…", &s[..max])
    }
}
