#!/usr/bin/env python
"""
patch-reference-docx.py — one-shot: take Gal's reference.docx (which is
already an excellent base) and adapt it for our project:

  1. Swap the body/header/footer font from "David" → "Arial"
     (per Adam's directive 2026-05-24).
  2. Replace Gal's header text with our project's header text.
  3. Keep everything else: blue headings (4F81BD), RTL defaults,
     header/footer borders, page-number field, table styles.

Run from the bookv3 directory:

    python _setup/patch-reference-docx.py

Idempotent — safe to run again any time. Reads and rewrites
bookv3/reference.docx in place.
"""

import os, sys, shutil, zipfile, tempfile, re, io
from pathlib import Path

# Force UTF-8 stdout so we can print arrows and Hebrew on Windows code pages.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent      # bookv3/
REF = ROOT / "reference.docx"

HEADER_TEXT_NEW = "אדם זבולון  |  עוקב לייזר אוטונומי מבוסס Raspberry Pi"
HEADER_TEXT_OLD_PAT = re.compile(
    r"<w:t>אדם זבולון[^<]*?</w:t>"
)

if not REF.exists():
    sys.exit(f"ERROR: {REF} not found. Did you forget to copy Gal's reference.docx in?")

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    with zipfile.ZipFile(REF, "r") as z:
        z.extractall(tmp)

    # ---- styles.xml: David → Arial ----
    styles_path = tmp / "word" / "styles.xml"
    styles = styles_path.read_text(encoding="utf-8")
    styles_before = styles
    styles = styles.replace('"David"', '"Arial"')
    styles_path.write_text(styles, encoding="utf-8")
    print(f"  styles.xml: David → Arial ({styles_before.count('David')} occurrences)")

    # ---- header1.xml: David → Arial, project text ----
    hdr_path = tmp / "word" / "header1.xml"
    hdr = hdr_path.read_text(encoding="utf-8")
    hdr = hdr.replace('"David"', '"Arial"')
    hdr_new, n = HEADER_TEXT_OLD_PAT.subn(f"<w:t>{HEADER_TEXT_NEW}</w:t>", hdr)
    if n == 0:
        print("  WARN: header text pattern not matched — leaving header text as-is")
    else:
        print(f"  header1.xml: David → Arial + header text updated ({n} replacement)")
    hdr_path.write_text(hdr_new, encoding="utf-8")

    # ---- footer1.xml: David → Arial (keep PAGE field as-is) ----
    ftr_path = tmp / "word" / "footer1.xml"
    ftr = ftr_path.read_text(encoding="utf-8")
    ftr = ftr.replace('"David"', '"Arial"')
    ftr_path.write_text(ftr, encoding="utf-8")
    print("  footer1.xml: David → Arial")

    # ---- Re-zip ----
    out = REF.with_suffix(".docx.new")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in tmp.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(tmp))
    shutil.move(str(out), str(REF))
    print(f"✓ Patched {REF}")
