#!/usr/bin/env python3
"""Generate whitepaper.pdf from pathram2 whitepaper sections via LaTeX + tectonic."""

import subprocess
import re
import os

SECTIONS = [
    ("wp-abstract", "Abstract"),
    ("wp-proof-graph", "The Proof Graph"),
    ("wp-graded-ring", "The Graded Ring and Lexical Morphism"),
    ("wp-operations", "The Operation Algebra"),
    ("wp-mantras", "Mantra Signatures"),
    ("wp-inversion", "Formula Inversion via Krama + Pratipaksha"),
    ("wp-pipeline", "Pipeline as Stratified Evaluation"),
    ("wp-signal-bus", "The Signal Bus"),
    ("wp-sexp", "S-Expression Syntax"),
    ("wp-panchaavayava", "Panchaavayava --- The Proof Structure"),
    ("wp-ontology", "Ontological Grounding"),
    ("wp-results", "Results and Capabilities"),
    ("wp-glossary", "Glossary"),
]


def pathram_body(node_id: str) -> str:
    r = subprocess.run(
        [".venv/bin/python3", "-m", "pathram2", "show", node_id],
        capture_output=True, text=True,
    )
    lines = r.stdout.splitlines()
    body_lines = []
    in_body = False
    for line in lines:
        if line.startswith("Edges:"):
            break
        if in_body:
            body_lines.append(line)
        if not in_body and re.match(r"^created:", line):
            in_body = True
    while body_lines and body_lines[0].strip() == "":
        body_lines.pop(0)
    return "\n".join(body_lines)


UNICODE_TO_LATEX = {
    "⊕": r"$\oplus$",
    "⊗": r"$\otimes$",
    "⊖": r"$\ominus$",
    "∈": r"$\in$",
    "∉": r"$\notin$",
    "⊆": r"$\subseteq$",
    "⊂": r"$\subset$",
    "∅": r"$\emptyset$",
    "∪": r"$\cup$",
    "∩": r"$\cap$",
    "×": r"$\times$",
    "→": r"$\to$",
    "←": r"$\leftarrow$",
    "↔": r"$\leftrightarrow$",
    "≡": r"$\equiv$",
    "≤": r"$\leq$",
    "≥": r"$\geq$",
    "≠": r"$\neq$",
    "⊢": r"$\vdash$",
    "∃": r"$\exists$",
    "∀": r"$\forall$",
    "⁻¹": r"$^{-1}$",
    "¹": r"$^{1}$",
    "²": r"$^{2}$",
    "³": r"$^{3}$",
    "∘": r"$\circ$",
    "✓": r"\checkmark{}",
    "✗": r"$\times$",
    "°": r"$^\circ$",
    "½": r"$\frac{1}{2}$",
    "…": r"\ldots{}",
    "δ": r"$\delta$",
    "Σ": r"$\Sigma$",
    "±": r"$\pm$",
    "∞": r"$\infty$",
    "α": r"$\alpha$",
    "β": r"$\beta$",
    "γ": r"$\gamma$",
    "π": r"$\pi$",
    "σ": r"$\sigma$",
    "ω": r"$\omega$",
    "—": "---",
    "–": "--",
    "\u2018": "`",
    "\u2019": "'",
    "\u201c": "``",
    "\u201d": "''",
}


def tex_safe(s: str) -> str:
    """Escape for table cells and text. Content already has $..$ LaTeX math from pathram."""
    for uni, latex in UNICODE_TO_LATEX.items():
        s = s.replace(uni, latex)

    # Escape special chars OUTSIDE of $...$ and $$...$$ blocks
    # Use regex to split on math regions, preserving delimiters
    tokens = re.split(r'(\$\$[^$]*\$\$|\$[^$]+\$)', s)
    for i, tok in enumerate(tokens):
        if not tok.startswith("$"):
            p = tok
            p = p.replace("&", r"\&")
            p = p.replace("%", r"\%")
            p = p.replace("#", r"\#")
            p = p.replace("_", r"\_")
            p = p.replace("~", r"\textasciitilde{}")
            tokens[i] = p
    return "".join(tokens)


def md_table_to_latex(lines: list[str]) -> str:
    """Convert markdown table lines to LaTeX tabular."""
    if len(lines) < 2:
        return ""
    headers = [c.strip() for c in lines[0].split("|") if c.strip()]
    n = len(headers)
    rows = []
    for tl in lines[2:]:  # skip separator
        cells = [c.strip() for c in tl.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        while len(cells) < n:
            cells.append("")
        rows.append(cells[:n])

    if n == 1:
        col_spec = "|X|"
    elif n == 2:
        col_spec = "|l|X|"
    else:
        col_spec = "|l|" + "X|" * (n - 1)
    out = []
    out.append(r"\noindent")
    out.append(r"\small")
    out.append(r"\begin{tabularx}{\textwidth}{" + col_spec + "}")
    out.append(r"\hline")
    out.append(r"\rowcolor{headerrow}")
    out.append(" & ".join(r"\textbf{" + tex_safe(h) + "}" for h in headers) + r" \\ \hline")
    for row in rows:
        out.append(" & ".join(tex_safe(c) for c in row) + r" \\ \hline")
    out.append(r"\end{tabularx}")
    out.append(r"\normalsize")
    out.append(r"\vspace{0.3em}")
    return "\n".join(out)


def md_to_latex_body(body: str) -> str:
    """Convert markdown body to LaTeX content."""
    lines = body.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # H2
        if line.startswith("## "):
            title = line[3:].strip()
            out.append(r"\subsection*{" + tex_safe(title) + "}")
            i += 1
            continue

        # H3
        if line.startswith("### "):
            title = line[4:].strip()
            out.append(r"\subsubsection*{" + tex_safe(title) + "}")
            i += 1
            continue

        # Code block
        if line.strip().startswith("```"):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            out.append(r"\begin{verbatim}")
            out.extend(code_lines)
            out.append(r"\end{verbatim}")
            continue

        # Indented code block (4 spaces)
        if line.startswith("    ") and not line.strip().startswith("|"):
            code_lines = []
            while i < len(lines) and (lines[i].startswith("    ") or lines[i].strip() == ""):
                code_lines.append(lines[i])
                i += 1
            out.append(r"\begin{verbatim}")
            for cl in code_lines:
                if cl.strip():
                    out.append(cl[4:] if cl.startswith("    ") else cl)
            out.append(r"\end{verbatim}")
            continue

        # Table
        if line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            out.append(md_table_to_latex(table_lines))
            continue

        # Blank line
        if line.strip() == "":
            if not out or out[-1] != "":
                out.append("")
            i += 1
            continue

        # Regular paragraph
        para_lines = []
        while i < len(lines) and lines[i].strip() and not lines[i].startswith("#") and not lines[i].startswith("|") and not lines[i].startswith("```") and not (lines[i].startswith("    ") and not lines[i].strip().startswith("|")):
            para_lines.append(lines[i])
            i += 1

        text = " ".join(para_lines)
        text = tex_safe(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
        out.append(text)
        out.append("")

    return "\n".join(out)


def build_latex() -> str:
    parts = []

    parts.append(r"""\documentclass[10pt,a4paper]{article}
\usepackage{fontspec}
\setmainfont{Noto Serif}[
  Path=/usr/share/fonts/noto/,
  Extension=.ttf,
  UprightFont=NotoSerif-Regular,
  BoldFont=NotoSerif-SemiBold,
  ItalicFont=NotoSerif-Italic,
  BoldItalicFont=NotoSerif-SemiBoldItalic,
]
\setsansfont{DejaVu Sans}[
  Path=/usr/share/fonts/TTF/,
  Extension=.ttf,
  UprightFont=DejaVuSans,
  BoldFont=DejaVuSans-Bold,
]
\setmonofont{DejaVu Sans Mono}[
  Path=/usr/share/fonts/TTF/,
  Extension=.ttf,
  UprightFont=DejaVuSansMono,
  BoldFont=DejaVuSansMono-Bold,
]
\usepackage[margin=2cm]{geometry}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{enumitem}
\usepackage{parskip}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{xcolor}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{colortbl}
\usepackage{multicol}
\usepackage{newunicodechar}
\newunicodechar{✓}{\checkmark}

% Colors
\definecolor{heading}{RGB}{30,30,120}
\definecolor{subheading}{RGB}{50,50,100}
\definecolor{gray}{RGB}{100,100,100}
\definecolor{headerrow}{RGB}{225,230,245}

% Heading styles
\titleformat{\section}{\large\bfseries\sffamily\color{heading}}{}{0em}{}[\color{heading}\titlerule]
\titleformat{\subsection}{\normalsize\bfseries\sffamily\color{subheading}}{}{0em}{}
\titleformat{\subsubsection}{\small\bfseries\sffamily\color{gray}}{}{0em}{}

% Header/footer
\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{\small\textit{\color{gray}Agent-X Whitepaper}}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% Compact spacing
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.3em}
\titlespacing*{\section}{0pt}{1.5em}{0.5em}
\titlespacing*{\subsection}{0pt}{1em}{0.3em}
\titlespacing*{\subsubsection}{0pt}{0.8em}{0.2em}
\renewcommand{\arraystretch}{1.15}

\begin{document}

% Title page
\thispagestyle{empty}
\vspace*{4cm}
\begin{center}
{\Huge\bfseries Agent-X}\\[0.8cm]
{\LARGE\itshape A Proof Graph That Answers Questions\\by Walking Its Own Structure}\\[1.5cm]
{\large\textit{Dimensions, Relations, and Projections}}\\[4cm]
{\small\color{gray}Agent-X Project --- April 2026}\\[0.5cm]
{\small\color{gray}\texttt{github.com/osvauld/prajana}}
\end{center}
\newpage

% Table of contents
\thispagestyle{empty}
\section*{Table of Contents}
\begin{enumerate}[leftmargin=2em]
""")

    for idx, (sid, title) in enumerate(SECTIONS, 1):
        parts.append(f"  \\item {tex_safe(title)}")

    parts.append(r"""\end{enumerate}
\newpage
""")

    # Sections
    for idx, (sid, title) in enumerate(SECTIONS):
        body = pathram_body(sid)
        if idx == 0:
            # Abstract gets special treatment — no numbered section
            parts.append(r"\section*{Abstract}")
        else:
            parts.append(f"\\section*{{{tex_safe(title)}}}")
        parts.append(md_to_latex_body(body))

    parts.append(r"""
\vfill
\begin{center}
\rule{0.4\textwidth}{0.4pt}\\[0.5em]
{\small\itshape The ring is the paragraph. The projection is the question.\\
Every answer is: build $\to$ fold $\to$ read.}
\end{center}

\end{document}""")
    return "\n".join(parts)


def main():
    latex_src = build_latex()

    tex_path = "docs/whitepaper.tex"
    with open(tex_path, "w") as f:
        f.write(latex_src)
    print(f"Written: {tex_path} ({len(latex_src)} chars)")

    tectonic = os.path.expanduser("~/.local/bin/tectonic")
    result = subprocess.run(
        [tectonic, "-o", "docs", tex_path],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        os.remove(tex_path)
        size = os.path.getsize("docs/whitepaper.pdf")
        print(f"Generated: docs/whitepaper.pdf ({size // 1024}KB)")
    else:
        print("Tectonic output:")
        print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
        print(result.stderr[-3000:] if len(result.stderr) > 3000 else result.stderr)


if __name__ == "__main__":
    main()
