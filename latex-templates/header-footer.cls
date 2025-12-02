% header-footer.cls  — v0.1  (XeLaTeX)
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{header-footer}[2025/10/07 SJC header class]
\LoadClass[12pt]{article}

% ----- packages (XeLaTeX) -----
\RequirePackage{fontspec}   % Unicode fonts
\defaultfontfeatures{Ligatures=TeX,Scale=MatchLowercase}
% \setmainfont{Latin Modern Roman} % safe default; change if you like

\RequirePackage{graphicx}
\RequirePackage[includefoot,a4paper]{geometry}
\geometry{margin=1in, bottom=1.25in}   % override in your .tex with \geometry{...} if needed
\RequirePackage{fancyhdr}
\RequirePackage{xparse}

% ----- configurable defaults -----
\newcommand\sjcLogo{image.png}
\newcommand\sjcLogoWidth{1.2cm}
\newcommand\sjcInstitute{St John's College Junior Common Room Returning Officer}
\newcommand\sjcElectionInfo{GeneralElection}
\newcommand\sjcHeaderTitle{By-Elections Role Descriptions}
\newcommand\sjcFirstPageTitle{[Placeholder]}
\newcommand{\sjcFooterText}{[name], JCR Returning Officer}

% User API: \setSJCHeader[<logo width>]{<logo path>}{<institute line>}{<election line>}{<title line>}
\NewDocumentCommand{\setSJCHeader}{O{1.2cm} m m m m}{%
  \renewcommand\sjcLogoWidth{#1}%
  \renewcommand\sjcLogo{#2}%
  \renewcommand\sjcInstitute{#3}%
  \renewcommand\sjcElectionInfo{#4}%
  \renewcommand\sjcHeaderTitle{#5}%
}

\NewDocumentCommand{\setSJCFooter}{m}{\renewcommand{\sjcFooterText}{#1}}

% Internal: the reusable header block
\newcommand{\sjcHeader}{%
  \begin{minipage}{\textwidth}
    \centering
    \vspace*{-0.7em}%
    \includegraphics[width=\sjcLogoWidth]{\sjcLogo}\\[-0.3em]
    \textsc{\sjcInstitute}\\[-0.1em]
    \textsc{\sjcElectionInfo}\\[-0.1em]
    \textsc{\large \sjcHeaderTitle}%
  \end{minipage}%
}

\newcommand{\sjcFooter}{%
  {\sjcFooterText}
}

% Fancyhdr setup (applies to ALL pages, incl. page 1)
\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{\sjcHeader}
\fancyfoot[L]{\sjcFooter}
\setlength{\headheight}{75pt} % adjust if you see a warning
\setlength{\footskip}{20pt}
\renewcommand{\headrulewidth}{0pt}

% Ensure "plain" style (used on first page by article) matches
\fancypagestyle{plain}[fancy]{}

% Optional helper for a simple title block (header still shows)
\NewDocumentCommand{\SJCTitlePage}{m}{%
  \renewcommand{\sjcFirstPageTitle}{#1}%
  \begin{center}
    {\LARGE\MakeUppercase{\sjcFirstPageTitle}}\\[0.5em]
  \end{center}
}