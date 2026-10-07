#!/bin/bash
# Build the lecture decks in LaTeX/Day_N/ into Slides/Day_N/, and those in LaTeX/Day_N/Optional/
# into Slides/Day_N/Optional/.
#
#   LaTeX/build.sh                                   # every deck
#   LaTeX/build.sh Day_4/01_Reinforcement_Learning.tex   # one deck (path relative to LaTeX/)
#   LaTeX/build.sh --keep-logs ...                   # keep .log/.aux next to the sources
#
# Adapted from build.sh in Artificial-Intelligence-Courses: same latexmk/pdflatex
# passes and the same error check, so a deck that builds there builds here.
# Exits non-zero if any deck fails, and keeps the .log of every failing deck
# under LaTeX/build/logs/.
#
# No -shell-escape: every image is committed under images/, so the
# \fetchconvertimage download path in preamble/commands.tex is never taken.
# A module that references an image which is not committed fails loudly.

set -uo pipefail

LATEX_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_DIR="$( dirname "$LATEX_DIR" )"
KEEP_LOGS=0
DECKS=()

for arg in "$@"; do
  case $arg in
    --keep-logs) KEEP_LOGS=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) DECKS+=("$arg") ;;
  esac
done

# Use latexmk from PATH, or a TinyTeX / MacTeX install that is not on PATH.
if ! command -v latexmk > /dev/null; then
  for bin in "$HOME"/Library/TinyTeX/bin/* "$HOME"/.TinyTeX/bin/* /Library/TeX/texbin; do
    if [ -x "$bin/latexmk" ]; then PATH="$bin:$PATH"; break; fi
  done
fi
command -v latexmk > /dev/null || { echo "latexmk not found: install TinyTeX (see LaTeX/README.md)"; exit 1; }

cd "$LATEX_DIR" || exit 1

if [ ${#DECKS[@]} -eq 0 ]; then
  for f in Day_*/*.tex Day_*/Optional/*.tex; do [ -f "$f" ] && DECKS+=("$f"); done
fi
[ ${#DECKS[@]} -gt 0 ] || { echo "No decks found in LaTeX/Day_*/"; exit 1; }

# Same error patterns as the upstream build.sh.
ERR_RE='^!|\.tex:[0-9]+:.*(Error|Undefined control sequence|Misplaced|Runaway|Illegal parameter|You can'"'"'t use)'
FAILED=()

for f in "${DECKS[@]}"; do
  [ -f "$f" ] || { echo "No such deck: LaTeX/$f"; FAILED+=("$f"); continue; }
  base="$(basename "${f%.tex}")"
  day="$(dirname "$f")"
  echo "--- $f"

  # Two passes so references, the TOC and the bibliography resolve.
  latexmk -pdf -interaction=nonstopmode -file-line-error -bibtex -use-make "$f" > /dev/null 2>&1
  latexmk -pdf -interaction=nonstopmode -file-line-error -bibtex -use-make "$f" > /dev/null 2>&1
  status=$?

  log="$base.log"
  errs=0
  [ -f "$log" ] && errs=$(grep -cE "$ERR_RE" "$log" || true)

  if [ ! -f "$base.pdf" ] || [ "$status" -ne 0 ] || [ "$errs" -ne 0 ]; then
    FAILED+=("$f")
    mkdir -p build/logs
    [ -f "$log" ] && cp "$log" "build/logs/$base.log"
    echo "  FAILED  ($errs error line(s); log kept at LaTeX/build/logs/$base.log)"
    [ -f "$log" ] && grep -nE "$ERR_RE" "$log" | head -5 | sed 's/^/      /'
    continue
  fi

  pages=$(sed -n 's/^Output written on .*(\([0-9]*\) page.*/\1/p' "$log" | tail -1)
  over=$(grep -c 'Overfull \\vbox' "$log" || true)
  miss=$(grep -c 'LaTeX Warning: File .* not found' "$log" || true)
  mkdir -p "$REPO_DIR/Slides/$day"
  mv "$base.pdf" "$REPO_DIR/Slides/$day/$base.pdf"
  echo "  ok  pages=${pages:-?}  overfull_vbox=$over  missing_images=$miss  -> Slides/$day/$base.pdf"
done

if [ "$KEEP_LOGS" -eq 0 ]; then
  rm -f ./*.aux ./*.bbl ./*.bcf ./*.blg ./*.fdb_latexmk ./*.fls ./*.log ./*.nav ./*.out \
        ./*.run.xml ./*.snm ./*.synctex.gz ./*.toc ./*.vrb ./*.glo ./*.ist ./*.acn
fi

if [ ${#FAILED[@]} -ne 0 ]; then
  echo
  echo "BUILD FAILED for ${#FAILED[@]} deck(s): ${FAILED[*]}"
  exit 1
fi
echo "Built ${#DECKS[@]} deck(s)."
