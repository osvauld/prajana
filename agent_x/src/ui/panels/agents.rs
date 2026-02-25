use ratatui::layout::Rect;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, ListState};
use ratatui::Frame;

use crate::runtime::bus::AgentStatus;
use crate::ui::theme::Theme;

#[derive(Clone)]
pub struct AgentEntry {
    pub id: String,
    pub role: String,
    pub status: AgentStatus,
    pub tmux_active: bool,
}

pub enum AgentClickAction {
    Select(usize),
    OpenTmux(usize),
    KillTmux(usize),
    ToggleTmuxSection,
}

pub struct AgentsPanel {
    pub entries: Vec<AgentEntry>,
    pub state: ListState,
    pub focused: bool,
    pub tmux_expanded: bool,
}

impl AgentsPanel {
    pub fn new(entries: Vec<AgentEntry>) -> Self {
        let mut state = ListState::default();
        if !entries.is_empty() {
            state.select(Some(0));
        }
        Self {
            entries,
            state,
            focused: false,
            tmux_expanded: false,
        }
    }

    pub fn selected_agent_id(&self) -> Option<&str> {
        self.state
            .selected()
            .and_then(|i| self.entries.get(i))
            .map(|e| e.id.as_str())
    }

    pub fn select_next(&mut self) {
        if self.entries.is_empty() {
            return;
        }
        let i = self.state.selected().unwrap_or(0);
        let next = if i + 1 < self.entries.len() { i + 1 } else { i };
        self.state.select(Some(next));
    }

    pub fn select_prev(&mut self) {
        let i = self.state.selected().unwrap_or(0);
        let prev = i.saturating_sub(1);
        self.state.select(Some(prev));
    }

    pub fn update_status(&mut self, agent_id: &str, status: AgentStatus) {
        if let Some(entry) = self.entries.iter_mut().find(|e| e.id == agent_id) {
            entry.status = status;
        }
    }

    pub fn set_tmux_active(&mut self, agent_id: &str, active: bool) {
        if let Some(entry) = self.entries.iter_mut().find(|e| e.id == agent_id) {
            entry.tmux_active = active;
        }
    }

    pub fn select_index(&mut self, idx: usize) {
        if idx < self.entries.len() {
            self.state.select(Some(idx));
        }
    }

    pub fn click_action(&self, area: Rect, x: u16, y: u16) -> Option<AgentClickAction> {
        if x < area.x || x >= area.x + area.width || y < area.y || y >= area.y + area.height {
            return None;
        }

        // Header row toggle region: [tmux]
        if y == area.y && x >= area.x + area.width.saturating_sub(8) {
            return Some(AgentClickAction::ToggleTmuxSection);
        }

        // Rows start after border/title line.
        let row = y.saturating_sub(area.y + 1) as usize;
        if row >= self.entries.len() {
            return None;
        }

        if self.tmux_expanded {
            let kill_start = area.x + area.width.saturating_sub(5); // [x]
            let open_start = area.x + area.width.saturating_sub(12); // [o]
            if x >= kill_start {
                return Some(AgentClickAction::KillTmux(row));
            }
            if x >= open_start {
                return Some(AgentClickAction::OpenTmux(row));
            }
        }

        Some(AgentClickAction::Select(row))
    }

    pub fn draw(&mut self, frame: &mut Frame, area: Rect, theme: &Theme) {
        let border_style = if self.focused {
            theme.focused_border()
        } else {
            theme.unfocused_border()
        };

        let items: Vec<ListItem> = self
            .entries
            .iter()
            .map(|entry| {
                let (status_icon, status_style) = match &entry.status {
                    AgentStatus::Idle => ("○", theme.status_idle()),
                    AgentStatus::Thinking => ("◉", theme.status_thinking()),
                    AgentStatus::Streaming => ("●", theme.status_streaming()),
                    AgentStatus::WaitingForTool => ("⚙", theme.status_tool()),
                    AgentStatus::Error(_) => ("✗", theme.status_error()),
                };

                let agent_color = theme.agent_color(&entry.id);

                ListItem::new(Line::from(vec![
                    Span::styled(format!(" {} ", status_icon), status_style),
                    Span::styled(
                        entry.id.clone(),
                        Style::default()
                            .fg(agent_color)
                            .add_modifier(Modifier::BOLD),
                    ),
                    if self.tmux_expanded {
                        Span::styled(
                            if entry.tmux_active {
                                "  [o] [x]"
                            } else {
                                "  [o]"
                            },
                            theme.muted_style(),
                        )
                    } else {
                        Span::raw("")
                    },
                ]))
            })
            .collect();

        let title = if self.tmux_expanded {
            " Agents [tmux▼] "
        } else {
            " Agents [tmux▶] "
        };

        let block = Block::default()
            .title(Span::styled(
                title,
                Style::default()
                    .fg(theme.text())
                    .add_modifier(Modifier::BOLD),
            ))
            .borders(Borders::ALL)
            .border_style(border_style);

        let list = List::new(items)
            .block(block)
            .highlight_style(theme.selected_style())
            .highlight_symbol("▸ ");

        frame.render_stateful_widget(list, area, &mut self.state);
    }
}
