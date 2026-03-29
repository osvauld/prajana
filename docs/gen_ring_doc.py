#!/usr/bin/env python3
"""Generate graded-ring.pdf — how Agent-X decomposes language into algebra."""

import os
import subprocess
import tempfile


def build_latex() -> str:
    return r"""\documentclass[10pt,a4paper]{article}
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

% Colors
\definecolor{heading}{RGB}{30,30,120}
\definecolor{subheading}{RGB}{50,50,100}
\definecolor{gray}{RGB}{100,100,100}
\definecolor{headerrow}{RGB}{225,230,245}
\definecolor{lightgray}{RGB}{245,245,250}
\definecolor{dimbox}{RGB}{235,240,250}
\definecolor{exbox}{RGB}{240,248,240}

% Heading styles
\titleformat{\section}{\large\bfseries\sffamily\color{heading}}{}{0em}{}[\color{heading}\titlerule]
\titleformat{\subsection}{\normalsize\bfseries\sffamily\color{subheading}}{}{0em}{}
\titleformat{\subsubsection}{\small\bfseries\sffamily\color{gray}}{}{0em}{}

% Header/footer
\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{\small\textit{\color{gray}The Graded Ring --- Agent-X}}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% Compact spacing
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.4em}
\titlespacing*{\section}{0pt}{1.2em}{0.4em}
\titlespacing*{\subsection}{0pt}{0.8em}{0.2em}
\titlespacing*{\subsubsection}{0pt}{0.6em}{0.1em}
\renewcommand{\arraystretch}{1.2}

\begin{document}

% ===== TITLE =====
\thispagestyle{empty}
\vspace*{4cm}
\begin{center}
{\Huge\bfseries\sffamily The Graded Ring}\\[0.6cm]
{\LARGE\color{subheading} How Agent-X Decomposes Language into Algebra}\\[1.5cm]
{\large\textit{Dimensions, Relations, and Projections}}\\[3cm]
{\small\color{gray} Agent-X Project --- March 2026}
\end{center}
\newpage

% ===== SECTION 1: THE THREE DIMENSIONS =====
\section{The Three Dimensions}

Every paragraph entering Agent-X is decomposed into a \textbf{graded ring}---an algebraic structure with one static dimension (where facts live) and two dynamic dimensions (how facts combine). The formal definition:

\begin{quote}
A paragraph $P$ with $n$ sentences produces $R = \bigoplus_{i=0}^{n} R_i$, where each $R_i$ is the set of facts from sentence $i$. Facts combine by addition ($\oplus$, same-kind accumulation) and multiplication ($\otimes$, cross-kind transformation), with $\otimes$ distributing over $\oplus$.
\end{quote}

\noindent
\small
\begin{tabularx}{\textwidth}{|l|X|l|l|l|}
\hline
\rowcolor{headerrow}
\textbf{Dimension} & \textbf{What it does} & \textbf{Math} & \textbf{Identity} & \textbf{Sa\.{n}gati} \\ \hline
\textbf{Grade} (sthiti) & Splits sentences into layers. Each sentence is a grade $R_i$. Period boundary creates new grade. & Filtration: $R = \bigoplus_i R_i$ & --- & sthiti \\ \hline
$\oplus$ \textbf{Addition} (sa\.{n}khy\={a}) & Accumulates same-kind quantities within/across grades. ``3 apples + 2 apples = 5 apples.'' & Commutative group & 0 (\'{s}\={u}nya) & v\d{r}ddhi $\leftrightarrow$ k\d{s}aya \\ \hline
$\otimes$ \textbf{Multiplication} (kriy\={a}) & Transforms across kinds. ``mass $\times$ velocity$^2$ $\times$ $\frac{1}{2}$'' or ``3 bags $\times$ 4 apples/bag.'' & Monoid & 1 (eka) & spanda (impulse) \\ \hline
\end{tabularx}
\normalsize

\subsection*{The Binding Law}

Distributivity ($\otimes$ distributes over $\oplus$) is what makes this a \emph{ring}, not just two separate operations:
$$a \otimes (b \oplus c) = (a \otimes b) \oplus (a \otimes c)$$

\noindent
\colorbox{dimbox}{\parbox{0.96\textwidth}{\small
\textbf{Example}: ``3 children each have 2 apples and 1 orange.'' \\[0.2em]
$3 \otimes (2 \oplus 1) = (3 \otimes 2) \oplus (3 \otimes 1) = 6 \oplus 3 = 9$ total fruit.\\[0.2em]
The $\otimes$ (``each''/``per'') distributes over the $\oplus$ (``and'' joining apples + oranges).
}}

\subsection*{Grade Decomposition}

The period (\texttt{.}) emits a \texttt{[``.'', ``vir\={a}m'', ``.'']} triple---the grade boundary. Within a grade, comma/``and'' emits \texttt{dvandva}---an intra-grade $\oplus$ separator. The question sentence (containing ``find'', ``how many'', ``which'') is the \emph{projection grade}---it reads the ring, not the data.

\noindent
\colorbox{dimbox}{\parbox{0.96\textwidth}{\small
\textbf{Example}: ``Alice has 3 apples. Bob gave her 2 more. How many apples?'' \\[0.3em]
\begin{tabular}{lll}
$R_0$: & ``Alice has 3 apples'' & $\{(\text{apples},\; 3)\}$ \\
$R_1$: & ``Bob gave her 2 more'' & $\{(\text{apples},\; 2),\; \text{dir}=\text{v\d{r}ddhi}\}$ \\
$R_2$: & ``How many apples?'' & projection $=$ CARDINALITY \\
\end{tabular} \\[0.3em]
Fold: $\underbrace{0}_{\text{\'{s}\={u}nya}} \oplus \underbrace{3}_{R_0} \oplus \underbrace{2}_{R_1} = 5$
}}

% ===== SECTION 2: THE 10 RELATIONS =====
\section{The 10 Relations (Vi\'{s}e\d{s}a\d{n}am)}

The knowledge graph is a 3D boolean tensor $G \in \{0,1\}^{N \times N \times 62}$ with 1649 nodes and 62 relation types. The \textbf{10 vi\'{s}e\d{s}a\d{n}am} are the structural generators---every other relation is composed from them.

To see them at work, trace one question through the pipeline.

\subsection*{Input: ``A car has mass 1000 kg and velocity 20 m/s. What is the kinetic energy?''}

\subsubsection*{Phase 1: BQG --- sentence $\to$ triples}

Each word is resolved against the graph. The relations emitted form the raw ring elements:

\noindent
\small
\begin{tabularx}{\textwidth}{|l|l|X|l|}
\hline
\rowcolor{headerrow}
\textbf{Word} & \textbf{Triple emitted} & \textbf{Relation (math type)} & \textbf{Dim} \\ \hline
car & [car, mithya, car] & \textbf{mithya} (rejection): car $\notin$ Graph & --- \\ \hline
mass & [mass, satya, mass] & \textbf{satya} (assertion): mass $\in$ Graph & grade \\ \hline
1000 & [1000, asprista-sa\.{n}khy\={a}, 1000] & \textbf{asprista-sa\.{n}khy\={a}} (unbound qty): raw $v$ & $\oplus$ \\ \hline
kg & [mass, sa\.{n}khy\={a}, 1000] & \textbf{sa\.{n}khy\={a}} (binding): mass $\mapsto 1000$ & $\oplus$ \\ \hline
& [mass, m\={a}tr\={a}, kilogram] & \textbf{m\={a}tr\={a}} (unit): mass $\in$ kg & $\oplus$ \\ \hline
and & [and, dvandva, dvandva] & \textbf{dvandva} (compound): intra-grade $\oplus$ boundary & grade \\ \hline
velocity & [velocity, satya, velocity] & \textbf{satya}: velocity $\in$ Graph & grade \\ \hline
20 m/s & [velocity, sa\.{n}khy\={a}, 20] & \textbf{sa\.{n}khy\={a}}: velocity $\mapsto 20$ & $\oplus$ \\ \hline
\textbf{.} & [., vir\={a}m, .] & \textbf{vir\={a}m}: grade boundary $R_0 \to R_1$ & grade \\ \hline
What & [What, vidhi-k\={a}la, solve-for] & \textbf{vidhi-k\={a}la} (imperative): projection signal & proj \\ \hline
kinetic energy & [KE, satya, KE] & \textbf{satya} + \textbf{sandhi} (compound merge) & proj \\ \hline
\textbf{?} & [?, vir\={a}m, ?] & \textbf{vir\={a}m}: grade boundary & grade \\ \hline
\end{tabularx}
\normalsize

\subsubsection*{Phase 2: Expand --- graph walk discovers the 10 vi\'{s}e\d{s}a\d{n}am}

Starting from \texttt{kinetic-energy}, the PPR walk reads edges. Each of the 10 structural relations tells the pipeline something specific:

\noindent
\small
\begin{tabularx}{\textwidth}{|l|X|l|X|}
\hline
\rowcolor{headerrow}
\textbf{\#} & \textbf{Relation (sa\.{n}gati)} & \textbf{Math type} & \textbf{What the pipeline learns} \\ \hline
1 & \textbf{swar\={u}pa} (self-nature) \newline KE $\to$ KE & $\mathrm{id}: x \mapsto x$ & Concept exists as itself. The $\otimes$-identity: transforming by swar\={u}pa changes nothing. \\ \hline
2 & \textbf{abheda} (non-difference) \newline KE $\equiv$ ``$\frac{1}{2}mv^2$'' & Equivalence: $x \sim y$ & Alternative names/forms. KE and $\frac{1}{2}mv^2$ name the same thing. \\ \hline
3 & \textbf{d\d{r}\d{s}\d{t}h\={a}nta} (example) \newline KE $\leftarrow$ ``a moving ball'' & Witness: $\exists x$ & Concrete instance. Grounds the abstract concept. \\ \hline
4 & \textbf{sthita} (foundation) \newline KE $\leq$ energy & Partial order: $x \leq y$ & Taxonomy. KE is a kind of energy. Gives grade ordering. \\ \hline
5 & \textbf{yukta} (connection) \newline KE --- mass, velocity & Association: $x \sim y$ & Which quantities are involved. The $\oplus$-summands. \\ \hline
6 & \textbf{siddha} (established) \newline KE $\vdash$ conservation & Axiom: $\vdash x$ & What law guarantees this. Proof/verification. \\ \hline
7 & \textbf{kriy\={a}} (action) \newline KE-mantra $\to$ [sq, mul, half] & Composition: $f \circ g \circ h$ & The $\otimes$-chain. Operation sequence to compute result. \\ \hline
8 & \textbf{phala} (fruit) \newline KE-mantra $\to$ KE & Codomain: $f \to y$ & Output of computation. What the krama produces. \\ \hline
9 & \textbf{janya} (born-from) \newline KE-mantra $\leftarrow$ mass, velocity & Domain: $x, y \to f$ & Required inputs. What must be bound before computing. \\ \hline
10 & \textbf{pratipak\d{s}a} (opposite) \newline half $\leftrightarrow$ double, sq $\leftrightarrow$ $\sqrt{\phantom{x}}$ & Inverse: $f^{-1}$ & How to reverse each step. Enables inverse solving. \\ \hline
\end{tabularx}
\normalsize

\vspace{0.4em}
\noindent\textbf{Key pairs}: phala $\leftrightarrow$ janya (output $\leftrightarrow$ input), yukta $\leftrightarrow$ rahita (connection $\leftrightarrow$ absence), kriy\={a} $\leftrightarrow$ nirodha (action $\leftrightarrow$ cessation), abheda $\leftrightarrow$ vibheda (sameness $\leftrightarrow$ distinction).

\subsubsection*{Phase 3: Dispatch --- krama evaluation ($\otimes$ chain)}

The kriy\={a} relation gave us the krama: \texttt{square $\to$ mul $\to$ half}. Each step is a $\otimes$ operation that transforms the accumulator:

\noindent
\small
\begin{tabularx}{\textwidth}{|l|l|l|l|X|}
\hline
\rowcolor{headerrow}
\textbf{Step} & \textbf{Op} & \textbf{Input} & \textbf{Output} & \textbf{Inverse (pratipak\d{s}a)} \\ \hline
1 & square ($x^2$) & velocity $= 20$ & $400$ & $\sqrt{x}$ (square-root) \\ \hline
2 & mul ($x \times y$) & $400 \times \text{mass} = 400 \times 1000$ & $400000$ & $x / y$ (division) \\ \hline
3 & half ($x \times 0.5$) & $400000$ & $200000$ & $x \times 2$ (double) \\ \hline
\end{tabularx}
\normalsize

\vspace{0.3em}
\noindent Answer: kinetic-energy $= 200000$ J. To solve \emph{inversely} (``KE is 200000, find velocity''), the pipeline reverses the krama and applies each pratipak\d{s}a: double $\to$ div $\to$ sqrt.

% ===== SECTION 3: PROJECTIONS =====
\section{The 6 Projections}

The question grade determines how to read the ring result. Each question type is a projection function $\pi: R \to \text{Answer}$.

\noindent
\small
\begin{tabularx}{\textwidth}{|l|l|X|l|}
\hline
\rowcolor{headerrow}
\textbf{Projection} & \textbf{Trigger words} & \textbf{Operation} & \textbf{Ring dimension} \\ \hline
DERIVE & find, calculate, what is...given data & Evaluate krama $\otimes$-chain on bound values & $\otimes$ \\ \hline
CARDINALITY & how many, total & $\oplus$-fold across grades, return count & $\oplus$ \\ \hline
COMPARE & which, more, less, fastest & Build entity set, apply $\arg\max / \arg\min$ & $\oplus$ then viveka \\ \hline
LOGIC & is X a Y, does X have Y & Walk swar\={u}pa/sthita edges, $\wedge$-chain & boolean \\ \hline
TYPED & does X $\in$ S, is X subset of Y & Set membership/subset predicate & set-ring \\ \hline
DEFINITION & what is X (no data) & Graph walk: describe node's edges & graph read \\ \hline
\end{tabularx}
\normalsize

\vspace{0.3em}
Every question follows the same pattern: \textbf{build the ring from the paragraph} $\to$ \textbf{apply the projection}. The ring is the same structure regardless of question type---only the readout differs.

% ===== SECTION 4: TRACED EXAMPLES =====
\section{Traced Examples}

\subsection*{Example 1: Count Addition ($\oplus$ fold)}

\noindent\colorbox{exbox}{\parbox{0.96\textwidth}{\small
\textbf{Q}: ``Tom has 5 apples. He gave away 2 apples. How many apples does Tom have?''
}}

\noindent
\small
\begin{tabular}{llll}
\textbf{Grade} & \textbf{Content} & \textbf{Ring element} & \textbf{Direction} \\
$R_0$ & ``Tom has 5 apples'' & (apples, 5) & --- \\
$R_1$ & ``He gave away 2 apples'' & (apples, 2) & k\d{s}aya (subtraction) \\
$R_2$ & ``How many apples...'' & projection $=$ CARDINALITY & --- \\
\end{tabular}
\normalsize

\vspace{0.2em}
The word ``gave away'' resolves to k\d{s}aya---the $\oplus$-inverse (subtraction). The fold:
$$\underbrace{0}_{\text{\'{s}\={u}nya}} \oplus \underbrace{5}_{R_0} \ominus \underbrace{2}_{R_1} = 3$$

\noindent Relations active: \textbf{satya} (apples $\in$ Graph), \textbf{sa\.{n}khy\={a}} (5, 2), \textbf{vir\={a}m} ($R_0 \to R_1$), \textbf{vidhi-k\={a}la} (solve-for), \textbf{pratipak\d{s}a} (v\d{r}ddhi $\leftrightarrow$ k\d{s}aya).

\subsection*{Example 2: Multiplication ($\otimes$ across grades)}

\noindent\colorbox{exbox}{\parbox{0.96\textwidth}{\small
\textbf{Q}: ``Each of 3 bags has 4 apples. How many apples in total?''
}}

\noindent
\small
\begin{tabular}{llll}
\textbf{Grade} & \textbf{Content} & \textbf{Ring element} & \textbf{Operation} \\
$R_0$ & ``Each of 3 bags'' & (bags, 3) & $\otimes$ (``each'' = multiplication) \\
$R_0$ & ``has 4 apples'' & (apples, 4) & within same grade \\
$R_1$ & ``How many apples...'' & projection $=$ CARDINALITY & --- \\
\end{tabular}
\normalsize

\vspace{0.2em}
The word ``each'' triggers $\otimes$ (multiplication) instead of $\oplus$ (addition):
$$3 \otimes 4 = 12$$

\noindent This is distributivity in action: ``each'' means the 3 distributes over the 4. Compare with ``3 apples and 4 oranges'' where ``and'' gives $3 \oplus 4 = 7$ ($\oplus$, same-grade accumulation).

\subsection*{Example 3: Comparison (viveka projection)}

\noindent\colorbox{exbox}{\parbox{0.96\textwidth}{\small
\textbf{Q}: ``Ball-A has mass 5 kg. Ball-B has mass 3 kg. Which ball is heavier?''
}}

\noindent
\small
\begin{tabular}{llll}
\textbf{Grade} & \textbf{Content} & \textbf{Ring element} & \textbf{Entity} \\
$R_0$ & ``Ball-A has mass 5 kg'' & (mass, 5, kg) & Ball-A \\
$R_1$ & ``Ball-B has mass 3 kg'' & (mass, 3, kg) & Ball-B \\
$R_2$ & ``Which ball is heavier?'' & projection $=$ COMPARE & viveka-max \\
\end{tabular}
\normalsize

\vspace{0.2em}
Each grade builds a separate entity. The question grade triggers viveka (discrimination)---a projection that selects from the entity set:
$$\arg\max\{\text{Ball-A}: 5,\; \text{Ball-B}: 3\} = \text{Ball-A}$$

\noindent ``Heavier'' maps to \texttt{viveka-max} via the graph. ``Lighter'' would map to \texttt{viveka-min} and return Ball-B. The ring accumulates entities across grades; viveka projects one answer from the set.

\subsection*{Example 4: Inverse Solve (reversed $\otimes$ chain)}

\noindent\colorbox{exbox}{\parbox{0.96\textwidth}{\small
\textbf{Q}: ``Kinetic energy is 200 J and mass is 4 kg. Find the velocity.''
}}

\noindent
\small
\begin{tabular}{lll}
\textbf{Grade} & \textbf{Content} & \textbf{Ring element} \\
$R_0$ & ``KE is 200 J and mass is 4 kg'' & (KE, 200, J) $\oplus$ (mass, 4, kg) \\
$R_1$ & ``Find the velocity'' & projection $=$ DERIVE, target $=$ velocity \\
\end{tabular}
\normalsize

\vspace{0.2em}
Velocity is a \textbf{janya} (input) of KE-mantra, not the \textbf{phala} (output). The pipeline inverts the krama chain using \textbf{pratipak\d{s}a} edges:

\noindent
\small
\begin{tabular}{lllll}
\textbf{Step} & \textbf{Forward op} & \textbf{Inverse op} & \textbf{Input} & \textbf{Output} \\
1 & half & double & KE $= 200$ & $400$ \\
2 & mul (mass) & div (mass) & $400 / 4$ & $100$ \\
3 & square & $\sqrt{\phantom{x}}$ & $\sqrt{100}$ & $10$ \\
\end{tabular}
\normalsize

\vspace{0.2em}
\noindent Answer: velocity $= 10$ m/s. No inverse formula was hardcoded---the engine reads pratipak\d{s}a edges on each operation node and reverses the chain automatically.

\vspace{1em}
\begin{center}
\small\color{gray}\rule{0.4\textwidth}{0.4pt}\\[0.5em]
\textit{The ring is the paragraph. The projection is the question.\\Every answer is: build $\to$ fold $\to$ read.}
\end{center}

\end{document}
"""


def main():
    latex_src = build_latex()

    tex_path = "docs/graded-ring.tex"
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
        size = os.path.getsize("docs/graded-ring.pdf")
        print(f"Generated: docs/graded-ring.pdf ({size // 1024}KB)")
    else:
        print("Tectonic output:")
        print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
        print(result.stderr[-3000:] if len(result.stderr) > 3000 else result.stderr)


if __name__ == "__main__":
    main()
