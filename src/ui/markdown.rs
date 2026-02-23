use pulldown_cmark::{CodeBlockKind, Event, Options, Parser, Tag, TagEnd};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};

use super::highlight::Highlighter;
use super::theme::Theme;

/// Render a markdown string into styled ratatui Lines.
pub fn render_markdown<'a>(
    content: &str,
    theme: &Theme,
    highlighter: &Highlighter,
    width: usize,
) -> Vec<Line<'a>> {
    let mut opts = Options::empty();
    opts.insert(Options::ENABLE_STRIKETHROUGH);
    opts.insert(Options::ENABLE_TABLES);

    let parser = Parser::new_ext(content, opts);
    let mut renderer = MarkdownRenderer::new(theme, highlighter, width);
    renderer.render(parser);
    renderer.lines
}

struct MarkdownRenderer<'t> {
    theme: &'t Theme,
    highlighter: &'t Highlighter,
    _width: usize,
    lines: Vec<Line<'static>>,
    current_spans: Vec<Span<'static>>,
    style_stack: Vec<Style>,
    in_code_block: bool,
    code_lang: String,
    code_buffer: String,
    in_blockquote: bool,
    list_depth: usize,
    heading_level: u8,
}

impl<'t> MarkdownRenderer<'t> {
    fn new(theme: &'t Theme, highlighter: &'t Highlighter, width: usize) -> Self {
        Self {
            theme,
            highlighter,
            _width: width,
            lines: Vec::new(),
            current_spans: Vec::new(),
            style_stack: vec![Style::default().fg(theme.text())],
            in_code_block: false,
            code_lang: String::new(),
            code_buffer: String::new(),
            in_blockquote: false,
            list_depth: 0,
            heading_level: 0,
        }
    }

    fn current_style(&self) -> Style {
        self.style_stack.last().copied().unwrap_or_default()
    }

    fn push_style(&mut self, style: Style) {
        self.style_stack.push(style);
    }

    fn pop_style(&mut self) {
        if self.style_stack.len() > 1 {
            self.style_stack.pop();
        }
    }

    fn flush_line(&mut self) {
        if !self.current_spans.is_empty() {
            let mut spans = Vec::new();
            if self.in_blockquote {
                spans.push(Span::styled(
                    "┃ ".to_string(),
                    Style::default().fg(self.theme.blockquote_bar()),
                ));
            }
            spans.append(&mut self.current_spans);
            self.lines.push(Line::from(spans));
        }
    }

    fn render(&mut self, parser: Parser) {
        for event in parser {
            match event {
                Event::Start(tag) => self.start_tag(tag),
                Event::End(tag) => self.end_tag(tag),
                Event::Text(text) => {
                    if self.in_code_block {
                        self.code_buffer.push_str(&text);
                    } else {
                        let style = self.current_style();
                        // Handle multi-line text
                        let text_str = text.to_string();
                        let mut first = true;
                        for line in text_str.split('\n') {
                            if !first {
                                self.flush_line();
                            }
                            if !line.is_empty() {
                                self.current_spans
                                    .push(Span::styled(line.to_string(), style));
                            }
                            first = false;
                        }
                    }
                }
                Event::Code(code) => {
                    let style = Style::default()
                        .fg(self.theme.peach())
                        .bg(self.theme.code_bg());
                    self.current_spans
                        .push(Span::styled(format!(" {} ", code), style));
                }
                Event::SoftBreak => {
                    self.current_spans.push(Span::raw(" ".to_string()));
                }
                Event::HardBreak => {
                    self.flush_line();
                }
                Event::Rule => {
                    self.flush_line();
                    self.lines.push(Line::from(Span::styled(
                        "─".repeat(40),
                        Style::default().fg(self.theme.surface1()),
                    )));
                }
                _ => {}
            }
        }
        self.flush_line();
    }

    fn start_tag(&mut self, tag: Tag) {
        match tag {
            Tag::Heading { level, .. } => {
                self.flush_line();
                self.heading_level = level as u8;
                let color = match level {
                    pulldown_cmark::HeadingLevel::H1 => self.theme.mauve(),
                    pulldown_cmark::HeadingLevel::H2 => self.theme.blue(),
                    pulldown_cmark::HeadingLevel::H3 => self.theme.teal(),
                    _ => self.theme.text(),
                };
                self.push_style(Style::default().fg(color).add_modifier(Modifier::BOLD));
            }
            Tag::Paragraph => {
                self.flush_line();
            }
            Tag::BlockQuote(_) => {
                self.flush_line();
                self.in_blockquote = true;
                self.push_style(Style::default().fg(self.theme.subtext0()));
            }
            Tag::CodeBlock(kind) => {
                self.flush_line();
                self.in_code_block = true;
                self.code_buffer.clear();
                self.code_lang = match kind {
                    CodeBlockKind::Fenced(lang) => lang.to_string(),
                    CodeBlockKind::Indented => String::new(),
                };
            }
            Tag::List(_) => {
                self.flush_line();
                self.list_depth += 1;
            }
            Tag::Item => {
                self.flush_line();
                let indent = "  ".repeat(self.list_depth.saturating_sub(1));
                self.current_spans.push(Span::styled(
                    format!("{}• ", indent),
                    Style::default().fg(self.theme.blue()),
                ));
            }
            Tag::Emphasis => {
                let base = self.current_style();
                self.push_style(base.add_modifier(Modifier::ITALIC));
            }
            Tag::Strong => {
                let base = self.current_style();
                self.push_style(base.add_modifier(Modifier::BOLD));
            }
            Tag::Strikethrough => {
                let base = self.current_style();
                self.push_style(base.add_modifier(Modifier::CROSSED_OUT));
            }
            Tag::Link { dest_url, .. } => {
                self.push_style(self.theme.link_style());
                // Store URL for potential display
                let _ = dest_url;
            }
            _ => {}
        }
    }

    fn end_tag(&mut self, tag: TagEnd) {
        match tag {
            TagEnd::Heading(_) => {
                self.pop_style();
                self.flush_line();
                self.heading_level = 0;
            }
            TagEnd::Paragraph => {
                self.flush_line();
                self.lines.push(Line::from(""));
            }
            TagEnd::BlockQuote(_) => {
                self.pop_style();
                self.in_blockquote = false;
                self.flush_line();
            }
            TagEnd::CodeBlock => {
                self.in_code_block = false;
                let code = std::mem::take(&mut self.code_buffer);
                let lang = std::mem::take(&mut self.code_lang);

                // Render code block header
                let lang_display = if lang.is_empty() { "text" } else { &lang };
                self.lines.push(Line::from(vec![
                    Span::styled(
                        format!("╭─ {} ", lang_display),
                        Style::default().fg(self.theme.surface1()),
                    ),
                    Span::styled("─".repeat(30), Style::default().fg(self.theme.surface1())),
                ]));

                // Syntax highlight the code
                let highlighted = self.highlighter.highlight_code(&code, &lang, self.theme);
                for line in highlighted {
                    let mut prefixed = vec![Span::styled(
                        "│ ".to_string(),
                        Style::default().fg(self.theme.surface1()),
                    )];
                    prefixed.extend(line.spans.into_iter());
                    self.lines.push(Line::from(prefixed));
                }

                self.lines.push(Line::from(Span::styled(
                    format!("╰{}", "─".repeat(35)),
                    Style::default().fg(self.theme.surface1()),
                )));
                self.lines.push(Line::from(""));
            }
            TagEnd::List(_) => {
                self.list_depth = self.list_depth.saturating_sub(1);
                if self.list_depth == 0 {
                    self.flush_line();
                }
            }
            TagEnd::Item => {
                self.flush_line();
            }
            TagEnd::Emphasis | TagEnd::Strong | TagEnd::Strikethrough | TagEnd::Link => {
                self.pop_style();
            }
            _ => {}
        }
    }
}
