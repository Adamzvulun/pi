# ספר הפרויקט — עוקב לייזר אוטונומי

מקור הספר של הפרויקט. כל פרק קיים כקובץ Markdown נפרד תחת `chapters/`,
תרשימי מרמייד תחת `diagrams/` (יוצאים ל־PNG ב־`diagrams/rendered/`),
תמונות תחת `photos/`, ורשימת חלקים מלאה ב־`parts-list.md`. בניית
ה־PDF המאוחד נעשית דרך `export/build-pdf.sh`.

---

## תוכן עניינים

| # | פרק | קובץ |
|---|-----|------|
| 0 | שער ותקציר | [`chapters/00-front-matter.md`](chapters/00-front-matter.md) |
| 1 | מבוא והצגת הבעיה האלגוריתמית | [`chapters/01-introduction.md`](chapters/01-introduction.md) |
| 2 | רקע תיאורטי | [`chapters/02-theoretical-background.md`](chapters/02-theoretical-background.md) |
| 3 | סקירת אלגוריתמים וניתוח SWOT | [`chapters/03-algorithm-survey-swot.md`](chapters/03-algorithm-survey-swot.md) |
| 4 | ארכיטקטורת החומרה | [`chapters/04-hardware-architecture.md`](chapters/04-hardware-architecture.md) |
| 5 | ארכיטקטורת התוכנה ומבנה המודולים | [`chapters/05-software-architecture.md`](chapters/05-software-architecture.md) |
| 6 | האלגוריתמים בפירוט | [`chapters/06-algorithms-in-detail.md`](chapters/06-algorithms-in-detail.md) |
| 7 | נושאים חדשים ולמידה עצמאית | [`chapters/07-new-tech-self-learning.md`](chapters/07-new-tech-self-learning.md) |
| 8 | מדריך הפעלה למשתמש | [`chapters/08-user-guide.md`](chapters/08-user-guide.md) |
| 9 | יומן ניסויים ותיעוד תהליך | [`chapters/09-experiments-log.md`](chapters/09-experiments-log.md) |
| 10 | ביצוע וגימור הפרויקט | [`chapters/10-build-finish-quality.md`](chapters/10-build-finish-quality.md) |
| 11 | סיכום ומבטים קדימה | [`chapters/11-conclusions-future.md`](chapters/11-conclusions-future.md) |
| — | רשימת חלקים מלאה (Bill of Materials) | [`parts-list.md`](parts-list.md) |
| — | מקורות וקישורים | [`references.md`](references.md) |

---

## איך להפיק את ה־PDF

```bash
bash export/build-pdf.sh
```

הסקריפט מריץ Pandoc + XeLaTeX עם פונט עברי תומך־RTL (David CLM)
על כל פרקי `chapters/` ויוצר את `export/laser-tracker-book.pdf`.

תלויות:
- `pandoc`
- `texlive-xetex` (או הפצת LaTeX כוללת, עם פונט David CLM זמין)
- `mermaid-cli` (`@mermaid-js/mermaid-cli`) — להמרת `diagrams/*.mmd` ל־PNG

---

## מבנה תיקיות

```
book/
├── README.md            ← זה הקובץ
├── chapters/            ← פרקי הספר, אחד לכל פרק
├── diagrams/            ← מקורות מרמייד + תיקיית rendered/ עם PNG
├── photos/              ← תמונות מהבנייה (הסטודנט מוסיף)
├── parts-list.md        ← רשימת חלקים מלאה
├── references.md        ← מקורות
└── export/              ← סקריפט בנייה + תבנית LaTeX + ה־PDF הסופי
```
