/*
 * build.js — convert the 19 Hebrew Markdown chapters into a single .docx.
 *
 * Reads:  ../chapters/00-cover.md ... ../chapters/18-bibliography.md
 * Writes: ../export/laser-tracker-book.docx
 *
 * Spec (from the rubric in docs/מחוון.pdf):
 *   - RTL Hebrew throughout
 *   - Font: David (fallback Arial), 12pt body
 *   - Header on every page: "עוקב לייזר אוטונומי — אדם זבולון"
 *   - Footer on every page: page number (centered)
 *   - Auto-generated TOC at the start, 3 levels deep (H1/H2/H3)
 */

const fs = require("fs");
const path = require("path");
const MarkdownIt = require("markdown-it");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Header,
  Footer,
  PageNumber,
  AlignmentType,
  HeadingLevel,
  TableOfContents,
  PageBreak,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
  ShadingType,
  ExternalHyperlink,
  LevelFormat,
} = require("docx");

// ---------- Configuration -----------------------------------------------------

const CHAPTERS_DIR = path.join(__dirname, "..", "chapters");
const OUTPUT_PATH = path.join(__dirname, "..", "export", "laser-tracker-book.docx");

const FONT = "David";
const FONT_FALLBACK = "Arial";
const BODY_SIZE = 24; // half-points => 12pt
const HEADER_TEXT = "עוקב לייזר אוטונומי — אדם זבולון";

// ---------- Helpers -----------------------------------------------------------

const md = new MarkdownIt({ html: false, linkify: true });

function makeRun(text, opts = {}) {
  return new TextRun({
    text,
    font: { name: FONT },
    size: opts.size || BODY_SIZE,
    bold: !!opts.bold,
    italics: !!opts.italics,
    color: opts.color,
    rightToLeft: opts.rtl !== false,
    ...(opts.code ? { font: { name: "Consolas" } } : {}),
  });
}

function makePara(children, opts = {}) {
  return new Paragraph({
    bidirectional: opts.ltr ? false : true,
    alignment: opts.alignment || (opts.ltr ? AlignmentType.LEFT : AlignmentType.RIGHT),
    children,
    heading: opts.heading,
    spacing: opts.spacing || { before: 100, after: 100 },
    ...(opts.numbering ? { numbering: opts.numbering } : {}),
    ...(opts.indent ? { indent: opts.indent } : {}),
  });
}

// Walk markdown-it tokens and convert each into docx elements.
function tokensToDocx(tokens) {
  const out = [];
  let i = 0;

  while (i < tokens.length) {
    const t = tokens[i];

    // ---- Headings ----
    if (t.type === "heading_open") {
      const level = parseInt(t.tag.slice(1), 10); // h1 -> 1
      const inline = tokens[i + 1]; // the inline tokens
      const text = inline ? inline.content : "";
      const headingLevel = [
        HeadingLevel.HEADING_1,
        HeadingLevel.HEADING_2,
        HeadingLevel.HEADING_3,
        HeadingLevel.HEADING_4,
        HeadingLevel.HEADING_5,
        HeadingLevel.HEADING_6,
      ][level - 1];

      out.push(
        makePara(
          [makeRun(text, { bold: true, size: BODY_SIZE + (4 - Math.min(level, 4)) * 4 })],
          {
            heading: headingLevel,
            spacing: { before: 320, after: 160 },
            alignment: AlignmentType.RIGHT,
          }
        )
      );
      i += 3; // heading_open, inline, heading_close
      continue;
    }

    // ---- Paragraph ----
    if (t.type === "paragraph_open") {
      const inline = tokens[i + 1];
      const runs = inlineToRuns(inline.children || []);
      if (runs.length > 0) {
        out.push(makePara(runs));
      }
      i += 3; // paragraph_open, inline, paragraph_close
      continue;
    }

    // ---- Code block (fenced) ----
    if (t.type === "fence" || t.type === "code_block") {
      const lines = t.content.replace(/\n$/, "").split("\n");
      for (const line of lines) {
        out.push(
          new Paragraph({
            bidirectional: false,
            alignment: AlignmentType.LEFT,
            spacing: { before: 0, after: 0 },
            shading: { fill: "F5F5F5", type: ShadingType.CLEAR, color: "auto" },
            children: [
              new TextRun({
                text: line || " ",
                font: { name: "Consolas" },
                size: 20, // 10pt
                rightToLeft: false,
              }),
            ],
          })
        );
      }
      // Add small spacing after the block
      out.push(makePara([makeRun("")], { spacing: { before: 0, after: 80 } }));
      i++;
      continue;
    }

    // ---- Bullet list ----
    if (t.type === "bullet_list_open") {
      const close = findClose(tokens, i, "bullet_list_close");
      const itemTokens = tokens.slice(i + 1, close);
      out.push(...listToDocx(itemTokens, "bullets"));
      i = close + 1;
      continue;
    }

    // ---- Ordered list ----
    if (t.type === "ordered_list_open") {
      const close = findClose(tokens, i, "ordered_list_close");
      const itemTokens = tokens.slice(i + 1, close);
      out.push(...listToDocx(itemTokens, "numbers"));
      i = close + 1;
      continue;
    }

    // ---- Table ----
    if (t.type === "table_open") {
      const close = findClose(tokens, i, "table_close");
      const tableTokens = tokens.slice(i + 1, close);
      out.push(tableToDocx(tableTokens));
      out.push(makePara([makeRun("")], { spacing: { before: 0, after: 80 } }));
      i = close + 1;
      continue;
    }

    // ---- Horizontal rule ----
    if (t.type === "hr") {
      out.push(
        new Paragraph({
          border: {
            bottom: { style: BorderStyle.SINGLE, size: 6, color: "999999", space: 1 },
          },
          spacing: { before: 120, after: 120 },
        })
      );
      i++;
      continue;
    }

    // ---- Blockquote ----
    if (t.type === "blockquote_open") {
      const close = findClose(tokens, i, "blockquote_close");
      const inner = tokensToDocx(tokens.slice(i + 1, close));
      // Indent and italicize each inner paragraph
      for (const p of inner) {
        out.push(p);
      }
      i = close + 1;
      continue;
    }

    // ---- HTML block (skip) ----
    if (t.type === "html_block") {
      i++;
      continue;
    }

    // Unknown — skip
    i++;
  }

  return out;
}

function findClose(tokens, startIdx, closeType) {
  let depth = 0;
  for (let j = startIdx; j < tokens.length; j++) {
    if (tokens[j].type === tokens[startIdx].type) depth++;
    else if (tokens[j].type === closeType) {
      depth--;
      if (depth === 0) return j;
    }
  }
  return tokens.length - 1;
}

function inlineToRuns(children) {
  const runs = [];
  let bold = false;
  let italic = false;
  let code = false;
  let linkHref = null;

  const flushLink = (text) => {
    if (linkHref) {
      runs.push(
        new ExternalHyperlink({
          link: linkHref,
          children: [
            new TextRun({
              text,
              font: { name: FONT },
              size: BODY_SIZE,
              color: "0563C1",
              underline: { type: "single" },
              rightToLeft: !looksLikeLatin(text),
            }),
          ],
        })
      );
    }
  };

  for (const c of children) {
    if (c.type === "text") {
      if (!c.content) continue;
      if (linkHref) {
        flushLink(c.content);
      } else {
        runs.push(
          makeRun(c.content, {
            bold,
            italics: italic,
            code,
            rtl: !looksLikeLatin(c.content),
          })
        );
      }
    } else if (c.type === "strong_open") bold = true;
    else if (c.type === "strong_close") bold = false;
    else if (c.type === "em_open") italic = true;
    else if (c.type === "em_close") italic = false;
    else if (c.type === "code_inline") {
      runs.push(
        new TextRun({
          text: c.content,
          font: { name: "Consolas" },
          size: 20,
          rightToLeft: false,
        })
      );
    } else if (c.type === "link_open") {
      const hrefAttr = c.attrs ? c.attrs.find((a) => a[0] === "href") : null;
      linkHref = hrefAttr ? hrefAttr[1] : null;
    } else if (c.type === "link_close") {
      linkHref = null;
    } else if (c.type === "softbreak" || c.type === "hardbreak") {
      runs.push(makeRun(" "));
    } else if (c.type === "image") {
      const alt = c.content || "[image]";
      runs.push(makeRun(`[${alt}]`, { italics: true, color: "888888" }));
    }
  }

  return runs;
}

// Heuristic: latin-only text should not be marked RTL
function looksLikeLatin(s) {
  if (!s) return false;
  // If no Hebrew characters at all, treat as LTR
  return !/[֐-׿]/.test(s);
}

function listToDocx(itemTokens, reference) {
  const out = [];
  let i = 0;
  while (i < itemTokens.length) {
    const t = itemTokens[i];
    if (t.type === "list_item_open") {
      const close = findClose(itemTokens, i, "list_item_close");
      const inner = itemTokens.slice(i + 1, close);
      // Each list item may contain paragraph_open/inline/paragraph_close
      // Take the first paragraph's inline as the bullet text
      let bulletText = "";
      let extraParas = [];
      let j = 0;
      while (j < inner.length) {
        const x = inner[j];
        if (x.type === "paragraph_open") {
          const inl = inner[j + 1];
          if (!bulletText) {
            // First paragraph -> bullet text
            const runs = inlineToRuns(inl.children || []);
            out.push(
              new Paragraph({
                bidirectional: true,
                alignment: AlignmentType.RIGHT,
                numbering: { reference, level: 0 },
                children: runs,
                spacing: { before: 60, after: 60 },
              })
            );
          } else {
            // Subsequent paragraphs in same list item
            const runs = inlineToRuns(inl.children || []);
            extraParas.push(
              new Paragraph({
                bidirectional: true,
                alignment: AlignmentType.RIGHT,
                indent: { start: 720 },
                children: runs,
                spacing: { before: 40, after: 40 },
              })
            );
          }
          bulletText = "first done";
          j += 3;
        } else {
          j++;
        }
      }
      out.push(...extraParas);
      i = close + 1;
    } else {
      i++;
    }
  }
  return out;
}

function tableToDocx(tableTokens) {
  // Parse rows: each row is between tr_open and tr_close,
  // cells between th_open/td_open and th_close/td_close.
  const rows = [];
  let currentRow = null;
  let cellIsHeader = false;
  let i = 0;

  while (i < tableTokens.length) {
    const t = tableTokens[i];
    if (t.type === "tr_open") {
      currentRow = [];
    } else if (t.type === "tr_close") {
      rows.push({ cells: currentRow, isHeader: cellIsHeader });
      currentRow = null;
    } else if (t.type === "th_open" || t.type === "td_open") {
      cellIsHeader = t.type === "th_open" && rows.length === 0;
      const close = findClose(
        tableTokens,
        i,
        t.type === "th_open" ? "th_close" : "td_close"
      );
      const inner = tableTokens.slice(i + 1, close);
      // inner is an inline token
      let runs = [];
      for (const x of inner) {
        if (x.type === "inline") {
          runs = inlineToRuns(x.children || []);
        }
      }
      currentRow.push({ runs, isHeader: cellIsHeader });
      i = close;
    }
    i++;
  }

  // Determine column count from widest row
  const colCount = Math.max(...rows.map((r) => r.cells.length));
  if (colCount === 0) {
    return makePara([makeRun("[empty table]")]);
  }

  // Width: use 9000 DXA total, distributed evenly
  const totalWidth = 9000;
  const colWidth = Math.floor(totalWidth / colCount);
  const columnWidths = new Array(colCount).fill(colWidth);

  const tableRows = rows.map(
    (row) =>
      new TableRow({
        children: row.cells.map((cell) => {
          return new TableCell({
            width: { size: colWidth, type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            shading: cell.isHeader
              ? { fill: "E7E6E6", type: ShadingType.CLEAR, color: "auto" }
              : undefined,
            borders: {
              top: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
              bottom: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
              left: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
              right: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
            },
            children: [
              new Paragraph({
                bidirectional: true,
                alignment: AlignmentType.RIGHT,
                spacing: { before: 0, after: 0 },
                children:
                  cell.runs.length > 0
                    ? cell.runs.map((r) => {
                        // Re-wrap header runs as bold
                        if (cell.isHeader && r instanceof TextRun) {
                          // can't easily re-create with bold; create new TextRun
                          return new TextRun({
                            text: r.options?.text || "",
                            font: { name: FONT },
                            size: BODY_SIZE,
                            bold: true,
                            rightToLeft: true,
                          });
                        }
                        return r;
                      })
                    : [makeRun(" ")],
              }),
            ],
          });
        }),
      })
  );

  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths,
    rows: tableRows,
    visuallyRightToLeft: true,
  });
}

// ---------- Build the document -----------------------------------------------

console.log("Reading chapters...");
const chapterFiles = fs
  .readdirSync(CHAPTERS_DIR)
  .filter((f) => /^\d{2}-.*\.md$/.test(f))
  .sort();

console.log(`Found ${chapterFiles.length} chapters.`);

const docChildren = [];

// --- Cover page (built programmatically, since 00-cover.md is LaTeX-only) ---
const coverLine = (text, opts = {}) =>
  new Paragraph({
    bidirectional: true,
    alignment: AlignmentType.CENTER,
    spacing: { before: opts.before || 0, after: opts.after || 120 },
    children: [
      new TextRun({
        text,
        font: { name: FONT },
        size: opts.size || BODY_SIZE,
        bold: !!opts.bold,
        rightToLeft: !looksLikeLatin(text),
      }),
    ],
  });

docChildren.push(coverLine("", { before: 1200 }));
docChildren.push(coverLine("מקיף ה' רוגוזין, אשקלון", { bold: true, size: 48 }));
docChildren.push(coverLine("סמל מוסד: 644450", { size: 28, after: 800 }));
docChildren.push(coverLine("עוקב לייזר אוטונומי", { bold: true, size: 56, after: 60 }));
docChildren.push(coverLine("מבוסס Raspberry Pi", { bold: true, size: 36, after: 400 }));
docChildren.push(coverLine("ספר פרויקט מעבדה במערכות אוטונומיות", { size: 26 }));
docChildren.push(
  coverLine("שאלון 714916 — כיתה י\"ד — הנדסאי הנדסת תוכנה", { size: 24, after: 800 })
);

// Field rows
const coverField = (label, value) =>
  new Paragraph({
    bidirectional: true,
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 80 },
    children: [
      new TextRun({
        text: label + ": ",
        font: { name: FONT },
        size: 26,
        bold: true,
        rightToLeft: true,
      }),
      new TextRun({
        text: value,
        font: { name: FONT },
        size: 26,
        rightToLeft: !looksLikeLatin(value),
      }),
    ],
  });

docChildren.push(coverField("שם הסטודנט", "אדם זבולון"));
docChildren.push(coverField("ת.ז.", "329441273"));
docChildren.push(coverField("שם המנחה", "משה זזק"));
docChildren.push(coverField("תאריך הגשה", "מאי 2026"));
docChildren.push(
  new Paragraph({
    bidirectional: false,
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 80 },
    children: [
      new TextRun({
        text: "מאגר קוד פתוח: ",
        font: { name: FONT },
        size: 22,
        bold: true,
        rightToLeft: true,
      }),
    ],
  })
);
docChildren.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 800 },
    children: [
      new ExternalHyperlink({
        link: "https://github.com/Adamzvulun/pi",
        children: [
          new TextRun({
            text: "https://github.com/Adamzvulun/pi",
            font: { name: FONT },
            size: 22,
            color: "0563C1",
            underline: { type: "single" },
          }),
        ],
      }),
    ],
  })
);
docChildren.push(
  coverLine("משרד החינוך — מנהל תקשוב טכנולוגיה ומערכות מידע", { size: 18 })
);

docChildren.push(new Paragraph({ children: [new PageBreak()] }));

// --- TOC after cover ---
docChildren.push(
  makePara([makeRun("תוכן עניינים", { bold: true, size: 36 })], {
    alignment: AlignmentType.RIGHT,
    spacing: { before: 0, after: 240 },
  })
);
docChildren.push(
  new TableOfContents("Table of Contents", {
    hyperlink: true,
    headingStyleRange: "1-3",
  })
);
docChildren.push(new Paragraph({ children: [new PageBreak()] }));

// --- Each chapter (skip 00-cover.md since we built the cover programmatically) ---
for (const filename of chapterFiles) {
  if (filename === "00-cover.md") {
    console.log(`  - ${filename}: skipped (cover built programmatically)`);
    continue;
  }
  const filepath = path.join(CHAPTERS_DIR, filename);
  let content = fs.readFileSync(filepath, "utf8");

  // Strip YAML frontmatter
  if (content.startsWith("---\n")) {
    const endIdx = content.indexOf("\n---", 4);
    if (endIdx !== -1) {
      content = content.slice(endIdx + 4).trimStart();
    }
  }

  // Drop any literal LaTeX titlepage block from the cover chapter
  content = content.replace(/\\begin\{titlepage\}[\s\S]*?\\end\{titlepage\}/g, "");
  content = content.replace(/\\newpage/g, "");

  // Strip ::: {dir=ltr} fence wrappers (pandoc-specific syntax)
  content = content.replace(/^:::\s*\{[^}]*\}\s*$/gm, "");
  content = content.replace(/^:::\s*$/gm, "");

  const tokens = md.parse(content, {});
  const chapterParas = tokensToDocx(tokens);
  docChildren.push(...chapterParas);

  // Page break between chapters
  docChildren.push(new Paragraph({ children: [new PageBreak()] }));
  console.log(`  + ${filename}: ${chapterParas.length} elements`);
}

// Cover page: special handling — read the cover separately and replace TOC ordering.
// Actually the cover content was already included as the first chapter (00-cover.md)
// so it appears BEFORE the TOC. To honor "TOC at start" properly we need to put
// the cover first, then the TOC. Let's rebuild docChildren in correct order.

console.log("Reordering for cover-first, TOC-second layout...");

// Strategy: take the cover chapter (which is the first chapter rendered above),
// keep it at the start, then insert the TOC AFTER it.

// Find the first PageBreak (end of cover chapter)
const coverEnd = docChildren.findIndex(
  (el, idx) => idx > 0 && el instanceof Paragraph && el.options?.children?.some?.((c) => c instanceof PageBreak)
);

// Simplification: we already pushed TOC first (3 elements), then cover content + page break,
// then the other chapters. Let's not reorder — keep TOC at the very start, cover as ch 0.
// Actually the cover provides title page info; having TOC after it would be fine too.
// For now, leave as: TOC → cover → ch1 → ch2 → ...
// Reset:
const finalChildren = docChildren;

// ---------- Document creation -------------------------------------------------

console.log("Building document...");

const doc = new Document({
  creator: "אדם זבולון",
  title: "עוקב לייזר אוטונומי — ספר פרויקט",
  description: "Project book for laser tracker — שאלון 714916",
  styles: {
    default: {
      document: { run: { font: { name: FONT }, size: BODY_SIZE } },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 36, bold: true, font: { name: FONT } },
        paragraph: {
          spacing: { before: 360, after: 200 },
          outlineLevel: 0,
          alignment: AlignmentType.RIGHT,
        },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 30, bold: true, font: { name: FONT } },
        paragraph: {
          spacing: { before: 280, after: 160 },
          outlineLevel: 1,
          alignment: AlignmentType.RIGHT,
        },
      },
      {
        id: "Heading3",
        name: "Heading 3",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 26, bold: true, font: { name: FONT } },
        paragraph: {
          spacing: { before: 240, after: 120 },
          outlineLevel: 2,
          alignment: AlignmentType.RIGHT,
        },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.RIGHT,
            style: { paragraph: { indent: { start: 720, hanging: 360 } } },
          },
        ],
      },
      {
        reference: "numbers",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.RIGHT,
            style: { paragraph: { indent: { start: 720, hanging: 360 } } },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 }, // A4
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
        bidi: true,
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              bidirectional: true,
              alignment: AlignmentType.RIGHT,
              children: [
                new TextRun({
                  text: HEADER_TEXT,
                  font: { name: FONT },
                  size: 20,
                  rightToLeft: true,
                }),
              ],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({
                  text: "עמוד ",
                  font: { name: FONT },
                  size: 20,
                  rightToLeft: true,
                }),
                new TextRun({
                  children: [PageNumber.CURRENT],
                  font: { name: FONT },
                  size: 20,
                }),
                new TextRun({
                  text: " מתוך ",
                  font: { name: FONT },
                  size: 20,
                  rightToLeft: true,
                }),
                new TextRun({
                  children: [PageNumber.TOTAL_PAGES],
                  font: { name: FONT },
                  size: 20,
                }),
              ],
            }),
          ],
        }),
      },
      children: finalChildren,
    },
  ],
});

console.log(`Packing ${finalChildren.length} top-level elements...`);
Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(OUTPUT_PATH, buffer);
  console.log(`✓ Wrote ${OUTPUT_PATH} (${(buffer.length / 1024).toFixed(1)} KB)`);
});
