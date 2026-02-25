use ratatui::style::{Color, Modifier, Style};
use std::collections::HashMap;

/// Catppuccin Mocha-inspired dark theme for agent_x.
pub struct Theme {
    agent_colors: HashMap<String, Color>,
}

impl Default for Theme {
    fn default() -> Self {
        let mut agent_colors = HashMap::new();
        agent_colors.insert("reader".into(), Color::Rgb(97, 175, 239)); // #61afef
        agent_colors.insert("planner".into(), Color::Rgb(198, 120, 221)); // #c678dd
        agent_colors.insert("writer".into(), Color::Rgb(152, 195, 121)); // #98c379
        agent_colors.insert("reviewer".into(), Color::Rgb(229, 192, 123)); // #e5c07b
        agent_colors.insert("docs".into(), Color::Rgb(86, 182, 194)); // #56b6c2
        Self { agent_colors }
    }
}

impl Theme {
    pub fn with_agent_colors(mut self, colors: &HashMap<String, String>) -> Self {
        for (id, hex) in colors {
            if let Some(c) = parse_hex(hex) {
                self.agent_colors.insert(id.clone(), c);
            }
        }
        self
    }

    // ── Base palette ────────────────────────────────────────────

    pub fn bg(&self) -> Color {
        Color::Rgb(30, 30, 46) // #1e1e2e
    }

    pub fn surface0(&self) -> Color {
        Color::Rgb(49, 50, 68) // #313244
    }

    pub fn surface1(&self) -> Color {
        Color::Rgb(69, 71, 90) // #45475a
    }

    pub fn overlay0(&self) -> Color {
        Color::Rgb(108, 112, 134) // #6c7086
    }

    pub fn text(&self) -> Color {
        Color::Rgb(205, 214, 244) // #cdd6f4
    }

    pub fn subtext0(&self) -> Color {
        Color::Rgb(166, 173, 200) // #a6adc8
    }

    pub fn subtext1(&self) -> Color {
        Color::Rgb(186, 194, 222) // #bac2de
    }

    // ── Accent colors ───────────────────────────────────────────

    pub fn blue(&self) -> Color {
        Color::Rgb(137, 180, 250) // #89b4fa
    }

    pub fn green(&self) -> Color {
        Color::Rgb(166, 227, 161) // #a6e3a1
    }

    pub fn red(&self) -> Color {
        Color::Rgb(243, 139, 168) // #f38ba8
    }

    pub fn yellow(&self) -> Color {
        Color::Rgb(249, 226, 175) // #f9e2af
    }

    pub fn mauve(&self) -> Color {
        Color::Rgb(203, 166, 247) // #cba6f7
    }

    pub fn teal(&self) -> Color {
        Color::Rgb(148, 226, 213) // #94e2d5
    }

    pub fn peach(&self) -> Color {
        Color::Rgb(250, 179, 135) // #fab387
    }

    // ── Semantic styles ─────────────────────────────────────────

    pub fn agent_color(&self, agent_id: &str) -> Color {
        self.agent_colors
            .get(agent_id)
            .copied()
            .unwrap_or(self.text())
    }

    pub fn user_border(&self) -> Style {
        Style::default().fg(self.blue())
    }

    pub fn assistant_border(&self, agent_id: &str) -> Style {
        Style::default().fg(self.agent_color(agent_id))
    }

    pub fn tool_border(&self) -> Style {
        Style::default().fg(self.overlay0())
    }

    pub fn error_style(&self) -> Style {
        Style::default().fg(self.red()).add_modifier(Modifier::BOLD)
    }

    pub fn header_style(&self) -> Style {
        Style::default()
            .fg(self.text())
            .add_modifier(Modifier::BOLD)
    }

    pub fn muted_style(&self) -> Style {
        Style::default().fg(self.overlay0())
    }

    pub fn label_style(&self) -> Style {
        Style::default().fg(self.subtext0())
    }

    pub fn status_idle(&self) -> Style {
        Style::default().fg(self.overlay0())
    }

    pub fn status_thinking(&self) -> Style {
        Style::default()
            .fg(self.yellow())
            .add_modifier(Modifier::BOLD)
    }

    pub fn status_streaming(&self) -> Style {
        Style::default()
            .fg(self.green())
            .add_modifier(Modifier::BOLD)
    }

    pub fn status_tool(&self) -> Style {
        Style::default().fg(self.peach())
    }

    pub fn status_error(&self) -> Style {
        Style::default().fg(self.red()).add_modifier(Modifier::BOLD)
    }

    pub fn focused_border(&self) -> Style {
        Style::default().fg(self.blue())
    }

    pub fn unfocused_border(&self) -> Style {
        Style::default().fg(self.surface1())
    }

    pub fn selected_style(&self) -> Style {
        Style::default()
            .fg(self.text())
            .bg(self.surface0())
            .add_modifier(Modifier::BOLD)
    }

    pub fn code_bg(&self) -> Color {
        Color::Rgb(24, 24, 37) // #181825 — slightly darker than bg
    }

    pub fn blockquote_bar(&self) -> Color {
        self.surface1()
    }

    pub fn link_style(&self) -> Style {
        Style::default()
            .fg(self.blue())
            .add_modifier(Modifier::UNDERLINED)
    }

    pub fn diff_added_bg(&self) -> Color {
        Color::Rgb(48, 58, 48) // #303a30
    }

    pub fn diff_removed_bg(&self) -> Color {
        Color::Rgb(58, 48, 48) // #3a3030
    }
}

fn parse_hex(hex: &str) -> Option<Color> {
    let hex = hex.trim_start_matches('#');
    if hex.len() != 6 {
        return None;
    }
    let r = u8::from_str_radix(&hex[0..2], 16).ok()?;
    let g = u8::from_str_radix(&hex[2..4], 16).ok()?;
    let b = u8::from_str_radix(&hex[4..6], 16).ok()?;
    Some(Color::Rgb(r, g, b))
}
