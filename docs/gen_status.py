#!/usr/bin/env python3
"""Generate status-analysis.pdf from pathram2 sections via LaTeX + tectonic."""

import subprocess
import re
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from generate_pdf import pathram_body, md_to_latex_body, tex_safe

SECTIONS = [
    ("doc-58", "Architecture Summary"),
    ("doc-52", "System Inventory"),
    ("doc-53", "Formula Coverage (Mantras)"),
    ("doc-54", "NLP Pattern Coverage"),
    ("doc-55", "Benchmark Coverage"),
    ("doc-56", "Missing Vocabulary and Mantras"),
    ("doc-57", "NLP Roadmap"),
]


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
\fancyhead[C]{\small\textit{\color{gray}Agent-X Status Analysis --- March 2026}}
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
{\Huge\bfseries Agent-X}\\[0.3cm]
{\Huge\bfseries Status Analysis}\\[1cm]
{\LARGE Where We Are, What We Need}\\[1.5cm]
{\large\textit{Graph inventory, formula coverage, NLP capabilities,\\benchmark readiness, and roadmap.}}\\[3cm]

\begin{tabular}{rl}
\textbf{Graph nodes:} & 1,649 across 4 layers \\
\textbf{Formulas:} & 23 mantras with automatic inversion \\
\textbf{Tests:} & 329/417 passing (79\%) \\
\textbf{Benchmark coverage:} & 21\% today $\to$ 93\% with roadmap \\
\textbf{NLP patterns:} & 16/23 working \\
\end{tabular}

\vspace{3cm}
{\small\color{gray}Generated from pathram2 composable sections\\
March 2026}
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

    for idx, (sid, title) in enumerate(SECTIONS, 1):
        body = pathram_body(sid)
        parts.append(f"\\section*{{{idx}. {tex_safe(title)}}}")
        parts.append(md_to_latex_body(body))
        if idx < len(SECTIONS):
            parts.append(r"\newpage")

    parts.append(r"\end{document}")
    return "\n".join(parts)


def main():
    latex_src = build_latex()

    tex_path = "docs/status-analysis.tex"
    with open(tex_path, "w") as f:
        f.write(latex_src)
    print(f"Written: {tex_path} ({len(latex_src)} chars)")

    tectonic = os.path.expanduser("~/.local/bin/tectonic")
    result = subprocess.run(
        [tectonic, "-o", "docs", tex_path],
        capture_output=True, text=True,
        timeout=60,
    )
    if result.returncode == 0:
        os.remove(tex_path)
        size = os.path.getsize("docs/status-analysis.pdf")
        print(f"Generated: docs/status-analysis.pdf ({size // 1024}KB)")
    else:
        print("Tectonic output:")
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)


if __name__ == "__main__":
    main()
