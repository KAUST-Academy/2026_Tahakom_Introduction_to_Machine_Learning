# Lecture sources for Day 4

The Day 4 decks are built from this folder. Change a slide by editing a
module here and rebuilding, not by editing the PDF in `Slides/`.

The modules are a fork of the LaTeX in
[`Artificial-Intelligence-Courses`](https://github.com/KAUST-Academy/Artificial-Intelligence-Courses),
taken so that Tahakom-specific changes do not leak into the other courses that
share those modules. Days 1 to 3 still come from `Tahakom_Early_Careers` (see the
top-level README).

```bash
LaTeX/build.sh                                       # every deck
LaTeX/build.sh Day_4/01_RL_Foundations.tex          # one deck (path relative to LaTeX/)
LaTeX/build.sh --keep-logs ...                       # keep .log/.aux for debugging
```

Each deck builds into `Slides/Day_N/` under its own file name, so `course.toml`
does not change when a deck is rebuilt. A failing deck keeps its log in
`LaTeX/build/logs/`; the script exits non-zero.

---

## Toolchain

pdfLaTeX through `latexmk`, the same as the upstream `build.sh`. The published
decks were built with pdfTeX 1.40.29; TinyTeX 2026 matches it.

On macOS, install [TinyTeX](https://yihui.org/tinytex/) into `~/Library/TinyTeX`
(about 360 MB) and add the packages these decks use:

```bash
curl -sL https://yihui.org/tinytex/install-bin-unix.sh | sh
~/Library/TinyTeX/bin/*/tlmgr install beamer translator media9 ocgx2 animate zref \
  fontawesome physics algorithm2e ifoddpage relsize glossaries mfirstuc xfor datatool \
  tracklang biblatex biber biblatex-ieee logreq pgfplots tcolorbox environ trimspaces \
  units cancel multirow caption parskip psnfss ragged2e newunicodechar booktabs \
  lastpage listings enumitem pgf xcolor etoolbox xstring oberdiek
```

`build.sh` uses `latexmk` from `PATH`, or finds it in `~/Library/TinyTeX`,
`~/.TinyTeX` or `/Library/TeX/texbin`, so the install does not have to touch
your shell profile. On Windows, run the script from Git Bash with MiKTeX or
TeX Live installed.

No `-shell-escape`: every image is committed under `images/`, so the
`\fetchconvertimage` download path in `preamble/commands.tex` is never taken.

---

## Layout

```
LaTeX/
├── build.sh
├── Day_4/01_RL_Foundations.tex                   # one file per deck: the list of modules, in order
├── Day_4/02_Policy_Gradients_and_RL_in_the_Real_World.tex
├── preamble/  style_files/  beamer*.sty         # theme, unchanged from upstream
├── sections/<module>/*.tex                      # the slides
└── images/<module>/                             # only images some module references
```

A deck file is a preamble plus a list of `\input{sections/<module>/<part>}`
lines. To drop or reorder slides, edit that list.

**Splitting a module.** When a deck needs only some of a module, split the
module into parts by line range and turn the original file into a wrapper that
`\input`s every part in the original order. The parts concatenate back to the
original byte for byte, and any deck that still inputs the original is
unchanged. Upstream did the same for `responsible-ai` in commit `1089afa`.

Modules that no deck inputs are kept on purpose (for example
`rl-real-world/rlhf_dpo_derivation.tex`): adding one `\input` line puts the
slides back.

---

## Provenance

| What | From |
|---|---|
| Theme, preamble, and the `rl-foundations`, `rl-real-world`, `vanilla-policy-gradient` and `policy-optimization` modules | `Artificial-Intelligence-Courses` `main` at `696f2e0` (4 October 2026) |
| `tahakom-rl` | written here: Day 4 agenda, part dividers, outcomes, the morning-to-afternoon hand-over, the advantage bridge, the Lab 3 map, summary |

Before any edit, the copied tree rebuilt both upstream RL decks with the same
page counts and the same extracted text as the published PDFs. Each split was
then checked twice: the parts concatenate to the original, and the upstream
deck rebuilt through the wrapper is unchanged.

**What differs from upstream.**

- **Day 4** is one day in three parts across two decks, matching the morning
  and afternoon sessions. The morning deck is *RL Foundations* (Part I, before
  Labs 1 and 2), ending on a hand-over slide instead of the RL course's road
  map. The afternoon deck opens with a one-slide recap, then adds the
  policy-gradient path (Part II: REINFORCE, PPO, GRPO, from the
  `vanilla-policy-gradient` and `policy-optimization` modules, before Lab 3),
  then *RL in the Real World* (Part III: RLHF, RLAIF and RLVR, the DPO
  overview without its derivation, multi-agent RL and robotics).
- **Wording.** References to lectures this course does not have ("Day 9",
  "the PPO lab", "earlier lectures") now point at the right place in this
  course. There are also two corrections, which are worth sending upstream:
  "GT Sophy" (was "GTSophie"), and a tabular learning rate of about 0.1 (was
  0.001).

To see exactly how a module differs from upstream:

```bash
diff LaTeX/sections/<module>/<file>.tex \
     ../Artificial-Intelligence-Courses/LaTeX/sections/<module>/<file>.tex
```
