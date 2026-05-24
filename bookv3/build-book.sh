#!/usr/bin/env bash
#
# build-book.sh — Build bookv3/export/laser-tracker-book.docx from all
# chapter Markdown files in bookv3/chapters/.
#
# Pipeline:
#   1. Concatenate the 19 chapters with raw-OpenXML page breaks
#   2. Generate a static TOC from chapter H1 titles
#   3. pandoc Markdown → Word with bookv3/reference.docx for styling
#   4. Python post-processor:
#        - wire up header/footer references into sectPr
#        - force LTR on code blocks (pandoc gives them bidi by default)
#        - strip pandoc's heading bookmarks (cleaner Google Docs view)
#        - add borders to every table
#        - shade first row of every table light blue (DCE6F1)
#
# Requirements (one-time install):
#   - pandoc (winget install --id JohnMacFarlane.Pandoc)
#   - python 3 with stdlib only
#   - bash (Git Bash on Windows, or any *nix shell)
#
# Style template: bookv3/reference.docx — Gal's reference.docx adapted
# for our project. To regenerate from a fresh copy of Gal's:
#   1. Copy Gal's reference.docx to bookv3/reference.docx
#   2. python _setup/patch-reference-docx.py   (Arial swap, header text)

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
CHAPTERS_DIR="$ROOT/chapters"
EXPORT_DIR="$ROOT/export"
OUTPUT="$EXPORT_DIR/laser-tracker-book.docx"
REFDOC="$ROOT/reference.docx"
TMP="$EXPORT_DIR/.book-merged.md"

# On Git Bash for Windows, `pwd` returns POSIX paths (/c/Projects/...) which
# Python (compiled for Windows) can't open. `pwd -W` returns a Windows-style
# path (C:/Projects/...). On *nix systems `pwd -W` is unsupported, so fall
# back to plain $ROOT there.
if pwd -W >/dev/null 2>&1; then
    CHAPTERS_DIR_PY="$(cd "$CHAPTERS_DIR" && pwd -W)"
    EXPORT_DIR_PY="$(cd "$EXPORT_DIR" && pwd -W)"
else
    CHAPTERS_DIR_PY="$CHAPTERS_DIR"
    EXPORT_DIR_PY="$EXPORT_DIR"
fi

mkdir -p "$EXPORT_DIR"

# Pick a python interpreter that exists. Windows installs land at `python`;
# *nix typically gives both. The Microsoft Store stub of "python3" can show
# up on Windows but bombs when invoked — prefer plain `python` if both exist.
if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "ERROR: no python interpreter found in PATH."
    exit 1
fi

if ! command -v pandoc >/dev/null 2>&1; then
    echo "ERROR: pandoc not found. Install with:"
    echo "  winget install --id JohnMacFarlane.Pandoc"
    echo "  (or download from https://pandoc.org/installing.html)"
    exit 1
fi

if [[ ! -f "$REFDOC" ]]; then
    echo "ERROR: $REFDOC not found. Re-run _setup/patch-reference-docx.py."
    exit 1
fi

# Chapter order — must match the rubric's 18 sections (we have 19 files
# because the cover is split out as 00-cover.md).
CHAPTERS=(
    "00-cover.md"
    "01-approved-proposal.md"
    "02-abstract.md"
    "03-declaration.md"
    "04-concepts.md"
    "05-topic.md"
    "06-problem.md"
    "07-alternatives.md"
    "08-selected-alternative.md"
    "09-controller.md"
    "10-components.md"
    "11-architecture.md"
    "12-protocols.md"
    "13-libraries.md"
    "14-development-process.md"
    "15-solution-documentation.md"
    "16-future.md"
    "17-summary.md"
    "18-bibliography.md"
)

for ch in "${CHAPTERS[@]}"; do
    if [[ ! -f "$CHAPTERS_DIR/$ch" ]]; then
        echo "ERROR: Missing chapter: $CHAPTERS_DIR/$ch"
        exit 1
    fi
done

PAGEBREAK='
```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
'

# ---- Step 1: Static TOC -----------------------------------------------------
# Pandoc's TOC field doesn't render in Google Docs viewer (only Word). A
# static bullet list with the chapter titles works everywhere.
echo "Generating static TOC..."
"$PY" - << PYEOF
import os, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CHAPTERS = [
    "01-approved-proposal.md", "02-abstract.md", "03-declaration.md",
    "04-concepts.md", "05-topic.md", "06-problem.md", "07-alternatives.md",
    "08-selected-alternative.md", "09-controller.md", "10-components.md",
    "11-architecture.md", "12-protocols.md", "13-libraries.md",
    "14-development-process.md", "15-solution-documentation.md",
    "16-future.md", "17-summary.md", "18-bibliography.md",
]

out = ["# תוכן עניינים", ""]
for ch in CHAPTERS:
    path = r"$CHAPTERS_DIR_PY" + "/" + ch
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^# +(.+?)\s*$", line)
            if m:
                out.append(f"- {m.group(1).strip()}")
                break

with open(r"$EXPORT_DIR_PY/.toc.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")

print(f"  TOC contains {len(out) - 2} chapter entries")
PYEOF

# ---- Step 2: Concatenate ---------------------------------------------------
echo "Merging ${#CHAPTERS[@]} chapters..."
: > "$TMP"
cat "$CHAPTERS_DIR/${CHAPTERS[0]}" >> "$TMP"
echo "$PAGEBREAK" >> "$TMP"
cat "$EXPORT_DIR/.toc.md" >> "$TMP"
for ch in "${CHAPTERS[@]:1}"; do
    echo "$PAGEBREAK" >> "$TMP"
    cat "$CHAPTERS_DIR/$ch" >> "$TMP"
done

# ---- Step 3: pandoc --------------------------------------------------------
echo "Running pandoc..."
pandoc \
    "$TMP" \
    --from markdown \
    --to docx \
    --output "$OUTPUT" \
    --reference-doc="$REFDOC" \
    --top-level-division=chapter \
    --metadata lang=he \
    --metadata dir=rtl \
    --highlight-style=tango \
    --wrap=preserve 2>/dev/null

rm -f "$TMP" "$EXPORT_DIR/.toc.md"

# ---- Step 4: Post-process the docx -----------------------------------------
echo "Post-processing docx..."
OUTPUT_DOCX="$OUTPUT" "$PY" - << 'PYEOF'
import os, re, zipfile, shutil, tempfile, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DOCX = os.environ["OUTPUT_DOCX"]

with tempfile.TemporaryDirectory() as tmp_dir:
    with zipfile.ZipFile(DOCX, "r") as z:
        z.extractall(tmp_dir)

    doc_path = os.path.join(tmp_dir, "word", "document.xml")
    rels_path = os.path.join(tmp_dir, "word", "_rels", "document.xml.rels")

    with open(doc_path, "r", encoding="utf-8") as f:
        doc = f.read()

    # ---- 1. Wire up header/footer (refs into sectPr) ----
    with open(rels_path, "r", encoding="utf-8") as f:
        rels = f.read()
    hdr_match = re.search(r'<Relationship Id="(rId\d+)"[^>]*Target="header1\.xml"', rels)
    ftr_match = re.search(r'<Relationship Id="(rId\d+)"[^>]*Target="footer1\.xml"', rels)
    if hdr_match and ftr_match:
        hdr_id, ftr_id = hdr_match.group(1), ftr_match.group(1)
        hdr_ref = f'<w:headerReference xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" w:type="default" r:id="{hdr_id}"/>'
        ftr_ref = f'<w:footerReference xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" w:type="default" r:id="{ftr_id}"/>'
        new_sect = f'<w:sectPr>{hdr_ref}{ftr_ref}</w:sectPr>'
        doc = re.sub(r"<w:sectPr\s*/>", new_sect, doc)
        def inject(m):
            inner = m.group(1)
            if "headerReference" in inner:
                return m.group(0)
            return f"<w:sectPr>{hdr_ref}{ftr_ref}{inner}</w:sectPr>"
        doc = re.sub(r"<w:sectPr>(.*?)</w:sectPr>", inject, doc, flags=re.DOTALL)
        print(f"  Wired up header={hdr_id}, footer={ftr_id}")
    else:
        print("  WARN: header/footer relationships not found in document.xml.rels")

    # ---- 2. Force LTR on SourceCode paragraphs ----
    def force_ltr(match):
        para = match.group(0)
        para = re.sub(r"<w:bidi\s*/>", "", para)
        para = re.sub(r"<w:rtl\s*/>", "", para)
        para = re.sub(
            r'(<w:pStyle w:val="SourceCode"\s*/>)',
            r'\1<w:bidi w:val="0"/>',
            para, count=1)
        return para
    doc = re.sub(
        r'<w:p>(?:(?!</w:p>).)*?<w:pStyle w:val="SourceCode"\s*/>(?:(?!</w:p>).)*?</w:p>',
        force_ltr, doc, flags=re.DOTALL)
    print("  Forced LTR on SourceCode paragraphs")

    # ---- 3. Remove bookmarks (cleaner Google Docs display) ----
    before_marks = doc.count("<w:bookmarkStart")
    doc = re.sub(r"<w:bookmarkStart[^/]*/>", "", doc)
    doc = re.sub(r"<w:bookmarkEnd[^/]*/>", "", doc)
    print(f"  Removed {before_marks} bookmarks")

    # ---- 4. Add borders to every table ----
    def add_borders(match):
        pr = match.group(0)
        if "<w:tblBorders>" in pr:
            return pr
        borders = (
            "<w:tblBorders>"
            '<w:top w:val="single" w:sz="6" w:space="0" w:color="333333"/>'
            '<w:left w:val="single" w:sz="6" w:space="0" w:color="333333"/>'
            '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="333333"/>'
            '<w:right w:val="single" w:sz="6" w:space="0" w:color="333333"/>'
            '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
            '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
            "</w:tblBorders>"
        )
        return pr.replace("</w:tblPr>", borders + "</w:tblPr>")
    doc = re.sub(r"<w:tblPr>.*?</w:tblPr>", add_borders, doc, flags=re.DOTALL)
    print("  Added borders to all tables")

    # ---- 5. Highlight first row of each table (header) ----
    def highlight_first_row(match):
        table = match.group(0)
        def shade_first_tr(tr_match):
            tr = tr_match.group(0)
            shade_xml = '<w:shd w:val="clear" w:color="auto" w:fill="DCE6F1"/>'
            tr = re.sub(r"<w:tcPr\s*/>", f"<w:tcPr>{shade_xml}</w:tcPr>", tr)
            def add_shade(tcpr_match):
                inner = tcpr_match.group(1)
                if "<w:shd" in inner:
                    return tcpr_match.group(0)
                return f"<w:tcPr>{shade_xml}{inner}</w:tcPr>"
            tr = re.sub(r"<w:tcPr>((?:(?!</w:tcPr>).)*)</w:tcPr>", add_shade, tr, flags=re.DOTALL)
            return tr
        table_new = re.sub(r"<w:tr>.*?</w:tr>", shade_first_tr, table, count=1, flags=re.DOTALL)
        return table_new
    doc = re.sub(r"<w:tbl>.*?</w:tbl>", highlight_first_row, doc, flags=re.DOTALL)
    shaded = doc.count('fill="DCE6F1"')
    print(f"  Highlighted {shaded} header cells (first row, light blue)")

    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(doc)

    # Re-zip
    new_docx = DOCX + ".new"
    with zipfile.ZipFile(new_docx, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(tmp_dir):
            for file in files:
                full = os.path.join(root, file)
                arc = os.path.relpath(full, tmp_dir)
                z.write(full, arc)
    shutil.move(new_docx, DOCX)
    print("  Post-processing complete.")
PYEOF

echo "Done: $OUTPUT"
ls -lh "$OUTPUT"
