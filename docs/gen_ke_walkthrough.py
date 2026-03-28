#!/usr/bin/env python3
"""Generate ke-walkthrough.pdf from pathram2 sections via LaTeX + tectonic."""

import subprocess
import re
import os
import sys

# Reuse the core functions from generate_pdf.py
sys.path.insert(0, os.path.dirname(__file__))
from generate_pdf import pathram_body, md_to_latex_body, tex_safe, UNICODE_TO_LATEX

SECTIONS = [
    ("doc-37", "The Question"),
    ("doc-48", "What is a Triple"),
    ("doc-50", "The Graph and the Tensor"),
    ("doc-49", "Mapping, Not Matching"),
    ("doc-38", "The Minimal Node Set"),
    ("doc-39", "Step 1: build-question-graph"),
    ("doc-40", "Step 2: assertion-bandha"),
    ("doc-41", "Step 3: avrti-refine-v2"),
    ("doc-42", "Steps 4--5: grade-split and count-chain"),
    ("doc-43", "Step 6: kosha-expand (PPR)"),
    ("doc-44", "Step 7: detect-signals"),
    ("doc-45", "Step 8: dispatch-answer (derive path)"),
    ("doc-46", "The Complete Triple History"),
    ("doc-47", "Connecting to the Math Foundations"),
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
\fancyhead[C]{\small\textit{\color{gray}KE Pipeline Walkthrough --- Agent-X}}
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
\vspace*{5cm}
\begin{center}
{\Huge\bfseries KE Pipeline}\\[0.3cm]
{\Huge\bfseries Minimal Walkthrough}\\[0.8cm]
{\LARGE How Agent-X computes $\frac{1}{2}mv^2$}\\[1.5cm]
{\large\textit{A step-by-step trace through every tantra,\\with the minimal set of nodes defined.}}\\[4cm]
{\small\color{gray}Question: ``mass is 5 kg and velocity is 10 m/s. find kinetic energy''\\
Answer: kinetic-energy = 250\\[0.5cm]
Generated from pathram2 composable sections\\
doc-36 (ke-walkthrough) with 14 linked sections}
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

    tex_path = "docs/ke-walkthrough.tex"
    with open(tex_path, "w") as f:
        f.write(latex_src)
    print(f"Written: {tex_path} ({len(latex_src)} chars)")

    # Compile with tectonic
    tectonic = os.path.expanduser("~/.local/bin/tectonic")
    result = subprocess.run(
        [tectonic, "-o", "docs", tex_path],
        capture_output=True, text=True,
        timeout=60,
    )
    if result.returncode == 0:
        os.remove(tex_path)
        size = os.path.getsize("docs/ke-walkthrough.pdf")
        print(f"Generated: docs/ke-walkthrough.pdf ({size // 1024}KB)")
    else:
        print("Tectonic output:")
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)


if __name__ == "__main__":
    main()
