#!/usr/bin/env bash
# build-pdf.sh — produce the combined Hebrew PDF of the project book.
#
# Usage (from anywhere):
#   bash book/export/build-pdf.sh
#
# Expects to be run on a system with:
#   - pandoc (`apt install pandoc`)
#   - texlive-xetex + Hebrew-capable fonts (e.g. `apt install texlive-xetex texlive-fonts-extra fonts-sil-ezra fonts-culmus`)
#   - mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`) — for rendering .mmd → .png
#
# On Raspberry Pi OS Bookworm, those packages are all available via apt + npm.
# On Windows, easiest is to run inside WSL2 with Ubuntu.

set -euo pipefail

# Locate the book directory regardless of where we're invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOK_DIR="$(dirname "$SCRIPT_DIR")"
CHAPTERS_DIR="$BOOK_DIR/chapters"
DIAGRAMS_DIR="$BOOK_DIR/diagrams"
RENDERED_DIR="$DIAGRAMS_DIR/rendered"
OUTPUT_PDF="$SCRIPT_DIR/laser-tracker-book.pdf"
TEMPLATE="$SCRIPT_DIR/pandoc-template.tex"

echo "[build-pdf] Book dir: $BOOK_DIR"

# ---- 1. Render mermaid diagrams to PNG --------------------------------------
# Each .mmd file under diagrams/ becomes a same-named .png under diagrams/rendered/.
# If mermaid-cli isn't installed, skip with a warning — the PDF will reference
# missing PNGs, which the chapters can also embed as code blocks instead.

mkdir -p "$RENDERED_DIR"

if command -v mmdc >/dev/null 2>&1; then
    echo "[build-pdf] Rendering mermaid diagrams..."
    for mmd in "$DIAGRAMS_DIR"/*.mmd; do
        [ -f "$mmd" ] || continue
        base="$(basename "$mmd" .mmd)"
        out="$RENDERED_DIR/$base.png"
        if [ ! -f "$out" ] || [ "$mmd" -nt "$out" ]; then
            echo "  - $base.mmd -> $base.png"
            mmdc -i "$mmd" -o "$out" --backgroundColor "white" 2>/dev/null || \
                echo "    (mmdc failed for $base — skipping)"
        fi
    done
else
    echo "[build-pdf] WARNING: mermaid-cli (mmdc) not found — skipping diagram rendering."
    echo "  Install with: npm install -g @mermaid-js/mermaid-cli"
fi

# ---- 2. Concatenate chapter sources in order --------------------------------
# Pandoc reads them as one logical document, preserving heading hierarchy.

CHAPTERS=(
    "$CHAPTERS_DIR/00-front-matter.md"
    "$CHAPTERS_DIR/01-introduction.md"
    "$CHAPTERS_DIR/02-theoretical-background.md"
    "$CHAPTERS_DIR/03-algorithm-survey-swot.md"
    "$CHAPTERS_DIR/04-hardware-architecture.md"
    "$CHAPTERS_DIR/05-software-architecture.md"
    "$CHAPTERS_DIR/06-algorithms-in-detail.md"
    "$CHAPTERS_DIR/07-new-tech-self-learning.md"
    "$CHAPTERS_DIR/08-user-guide.md"
    "$CHAPTERS_DIR/09-experiments-log.md"
    "$CHAPTERS_DIR/10-build-finish-quality.md"
    "$CHAPTERS_DIR/11-conclusions-future.md"
    "$BOOK_DIR/parts-list.md"
    "$BOOK_DIR/references.md"
)

for f in "${CHAPTERS[@]}"; do
    if [ ! -f "$f" ]; then
        echo "[build-pdf] ERROR: missing chapter file $f"
        exit 1
    fi
done

# ---- 3. Run pandoc with XeLaTeX + Hebrew (RTL) ------------------------------
# David CLM is a free Hebrew font common on Debian/Ubuntu via fonts-culmus.
# Fallback fonts handled by polyglossia / babel-hebrew.

echo "[build-pdf] Running pandoc -> $OUTPUT_PDF"

pandoc \
    --pdf-engine=xelatex \
    --variable=mainfont="David CLM" \
    --variable=dir:rtl \
    --variable=lang:he-IL \
    --variable=geometry:margin=2.5cm \
    --variable=fontsize:11pt \
    --variable=documentclass:report \
    --variable=linestretch:1.3 \
    --variable=toc-title:"תוכן עניינים" \
    --toc \
    --toc-depth=2 \
    --number-sections \
    --resource-path="$BOOK_DIR:$RENDERED_DIR:$BOOK_DIR/photos" \
    --output "$OUTPUT_PDF" \
    "${CHAPTERS[@]}"

echo "[build-pdf] Done. PDF at $OUTPUT_PDF"
echo "[build-pdf] Page count check:"
if command -v pdfinfo >/dev/null 2>&1; then
    pdfinfo "$OUTPUT_PDF" | grep "Pages"
fi
