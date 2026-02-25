use ratatui::style::{Color, Style};
use ratatui::text::{Line, Span};
use syntect::easy::HighlightLines;
use syntect::highlighting::{FontStyle, ThemeSet};
use syntect::parsing::SyntaxSet;
use syntect::util::LinesWithEndings;

use super::theme::Theme;

/// Shared syntax highlighting state. Create once, reuse.
pub struct Highlighter {
    syntax_set: SyntaxSet,
    theme_set: ThemeSet,
}

impl Highlighter {
    pub fn new() -> Self {
        Self {
            syntax_set: SyntaxSet::load_defaults_newlines(),
            theme_set: ThemeSet::load_defaults(),
        }
    }

    /// Highlight a block of code, returning styled ratatui Lines.
    /// `lang` is the fence tag (e.g. "rust", "python", "bash").
    /// Falls back to plain text if language is unknown.
    pub fn highlight_code<'a>(&self, code: &str, lang: &str, _app_theme: &Theme) -> Vec<Line<'a>> {
        let syntax = self
            .syntax_set
            .find_syntax_by_token(lang)
            .or_else(|| self.syntax_set.find_syntax_by_extension(lang))
            .unwrap_or_else(|| self.syntax_set.find_syntax_plain_text());

        let theme = &self.theme_set.themes["base16-ocean.dark"];
        let mut h = HighlightLines::new(syntax, theme);

        let mut lines = Vec::new();
        for line_str in LinesWithEndings::from(code) {
            let ranges = h
                .highlight_line(line_str, &self.syntax_set)
                .unwrap_or_default();

            let spans: Vec<Span<'a>> = ranges
                .into_iter()
                .map(|(style, text)| {
                    let fg = Color::Rgb(style.foreground.r, style.foreground.g, style.foreground.b);
                    let mut ratatui_style = Style::default().fg(fg);
                    if style.font_style.contains(FontStyle::BOLD) {
                        ratatui_style = ratatui_style.add_modifier(ratatui::style::Modifier::BOLD);
                    }
                    if style.font_style.contains(FontStyle::ITALIC) {
                        ratatui_style =
                            ratatui_style.add_modifier(ratatui::style::Modifier::ITALIC);
                    }
                    Span::styled(text.trim_end_matches('\n').to_string(), ratatui_style)
                })
                .collect();

            lines.push(Line::from(spans));
        }

        lines
    }

    /// Highlight a single line of code, for inline use.
    pub fn highlight_inline<'a>(
        &self,
        text: &str,
        lang: &str,
        _app_theme: &Theme,
    ) -> Vec<Span<'a>> {
        let syntax = self
            .syntax_set
            .find_syntax_by_token(lang)
            .or_else(|| self.syntax_set.find_syntax_by_extension(lang))
            .unwrap_or_else(|| self.syntax_set.find_syntax_plain_text());

        let theme = &self.theme_set.themes["base16-ocean.dark"];
        let mut h = HighlightLines::new(syntax, theme);

        let ranges = h.highlight_line(text, &self.syntax_set).unwrap_or_default();

        ranges
            .into_iter()
            .map(|(style, t)| {
                let fg = Color::Rgb(style.foreground.r, style.foreground.g, style.foreground.b);
                Span::styled(t.to_string(), Style::default().fg(fg))
            })
            .collect()
    }
}
