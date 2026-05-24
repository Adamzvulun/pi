# ספר הפרויקט — עוקב לייזר אוטונומי

מקור הספר של הפרויקט. המבנה והתוכן עוקבים אחר ההנחיות לכתיבת ספר
פרויקט במערכות אוטונומיות (שאלון 714916) ב־
[`docs/מחוון.pdf`](../docs/מחוון.pdf).

כל פרק קיים כקובץ Markdown נפרד תחת `chapters/`, תרשימי מרמייד
תחת `diagrams/` (יוצאים ל־PNG ב־`diagrams/rendered/` על־ידי
`build-pdf.sh`), תמונות תחת `photos/`. בניית ה־PDF המאוחד נעשית
דרך `export/build-pdf.sh`.

---

## תוכן עניינים (18 פרקים — לפי המחוון)

| # | פרק | קובץ |
|:---:|-----|------|
| 0 | שער (Cover) | [`chapters/00-cover.md`](chapters/00-cover.md) |
| 1 | הצעת הפרויקט שאושרה | [`chapters/01-approved-proposal.md`](chapters/01-approved-proposal.md) |
| 2 | תקציר | [`chapters/02-abstract.md`](chapters/02-abstract.md) |
| 3 | תצהיר חתום | [`chapters/03-declaration.md`](chapters/03-declaration.md) |
| 4 | מושגים | [`chapters/04-concepts.md`](chapters/04-concepts.md) |
| 5 | תיאור הנושא | [`chapters/05-topic.md`](chapters/05-topic.md) |
| 6 | תיאור הבעיה / הצורך בשוק | [`chapters/06-problem.md`](chapters/06-problem.md) |
| 7 | ניתוח חלופות מערכתי | [`chapters/07-alternatives.md`](chapters/07-alternatives.md) |
| 8 | תיאור החלופה הנבחרת | [`chapters/08-selected-alternative.md`](chapters/08-selected-alternative.md) |
| 9 | הסבר על הבקר | [`chapters/09-controller.md`](chapters/09-controller.md) |
| 10 | הסבר רכיבים (חיישנים + אופן הפעולה) | [`chapters/10-components.md`](chapters/10-components.md) |
| 11 | תיאור הארכיטקטורה | [`chapters/11-architecture.md`](chapters/11-architecture.md) |
| 12 | תיאור פרוטוקולי התקשורת | [`chapters/12-protocols.md`](chapters/12-protocols.md) |
| 13 | הסבר ספריות (Self-written + BB) | [`chapters/13-libraries.md`](chapters/13-libraries.md) |
| 14 | תהליך הפיתוח | [`chapters/14-development-process.md`](chapters/14-development-process.md) |
| 15 | תיעוד הפתרון (a–g) | [`chapters/15-solution-documentation.md`](chapters/15-solution-documentation.md) |
| 16 | פיתוחים עתידיים | [`chapters/16-future.md`](chapters/16-future.md) |
| 17 | סיכום ומסקנות | [`chapters/17-summary.md`](chapters/17-summary.md) |
| 18 | ביבליוגרפיה | [`chapters/18-bibliography.md`](chapters/18-bibliography.md) |

---

## איך להפיק את ה־PDF

```bash
bash export/build-pdf.sh
```

הסקריפט מריץ Pandoc + XeLaTeX עם פונט עברי תומך־RTL (David CLM)
על כל פרקי `chapters/` ויוצר את `export/laser-tracker-book.pdf`.

תלויות:

- `pandoc`
- `texlive-xetex` (או הפצת LaTeX כוללת)
- פונט David CLM זמין (חבילת `fonts-culmus` ב־Debian/Ubuntu)
- `mermaid-cli` (`@mermaid-js/mermaid-cli`) — להמרת `diagrams/*.mmd`
  ל־PNG

על Raspberry Pi OS Bookworm כל החבילות זמינות:

```bash
sudo apt install pandoc texlive-xetex texlive-fonts-extra fonts-culmus
sudo npm install -g @mermaid-js/mermaid-cli
```

ב־Windows הדרך הקלה ביותר היא להריץ את הסקריפט ב־WSL2 + Ubuntu.

---

## עמידה בהנחיות המחוון

| דרישה מהמחוון | מימוש |
|---|---|
| גופן David או Arial, מקסימום 12 | LaTeX template עם `David CLM` ב־12pt |
| כותרת עליונה בכל דף (שם תלמיד / שם פרויקט) | `fancyhdr` ב־template |
| כותרת תחתונה עם מספר עמוד | `\fancyfoot[C]{\thepage}` ב־template |
| תוכן עניינים אוטומטי | `--toc --toc-depth=3` ב־pandoc |
| מבנה 18 פרקים | תואם בדיוק ל־`chapters/` |
| שער עם לוגו/שם מוסד/סמל מוסד/שם פרויקט/סטודנט/ת.ז./מנחה/תאריך | `00-cover.md` |
| תצהיר מקוריות | `03-declaration.md` |
| ביבליוגרפיה | `18-bibliography.md` |

---

## מבנה התיקייה

```
book/
├── README.md            ← הקובץ הזה
├── chapters/            ← 19 פרקים (00-cover עד 18-bibliography)
│   └── _old/            ← הגרסה הקודמת של הפרקים (לפני המעבר ל־18-section)
├── diagrams/            ← מקורות מרמייד + תיקיית rendered/ עם PNG
│   ├── *.mmd            ← מקורות
│   └── rendered/        ← נוצר ע"י build-pdf.sh
├── photos/              ← תמונות מהבנייה (לא ב־git כרגע — יתווסף ע"י אדם)
├── parts-list.md        ← רשימת חלקים מלאה (משמש כנספח)
├── references.md        ← (פנימי, הוחלף ע"י §18)
└── export/              ← סקריפט בנייה + תבנית LaTeX + ה־PDF הסופי
```
