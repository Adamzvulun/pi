# ספר הפרויקט — עוקב לייזר אוטונומי (גרסה v3)

מקור הגרסה השלישית של ספר הפרויקט. המבנה נשמר 1:1 לפי המחוון של שאלון 714916 ([`docs/מחוון.pdf`](../docs/מחוון.pdf)), אבל הסגנון נכתב מחדש בהתאם לשני ספרי דוגמה משנים קודמות (גלב שורין, דניאל אלוש — נמצאים ב־[`examples/`](examples/)): פרוזה קצרה ולעניין, מעט טבלאות, יעד של כ־50 עמודים מודפסים.

כל פרק קיים כקובץ Markdown נפרד תחת [`chapters/`](chapters/), תרשימי מרמייד תחת [`diagrams/`](diagrams/), ותמונות תחת [`photos/`](photos/). בניית קובץ ה־.docx הסופי נעשית דרך [`_docx_build/build.js`](_docx_build/build.js) שמרכיב את כל ה־19 פרקים לקובץ אחד ב־[`export/laser-tracker-book.docx`](export/laser-tracker-book.docx).

## תוכן עניינים — 19 קבצים לפי 18 סעיפי המחוון

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
| 10 | הסבר רכיבים | [`chapters/10-components.md`](chapters/10-components.md) |
| 11 | תיאור הארכיטקטורה | [`chapters/11-architecture.md`](chapters/11-architecture.md) |
| 12 | תיאור פרוטוקולי תקשורת | [`chapters/12-protocols.md`](chapters/12-protocols.md) |
| 13 | הסבר ספריות (Self-Written + BB) | [`chapters/13-libraries.md`](chapters/13-libraries.md) |
| 14 | תהליך הפיתוח | [`chapters/14-development-process.md`](chapters/14-development-process.md) |
| 15 | תיעוד הפתרון | [`chapters/15-solution-documentation.md`](chapters/15-solution-documentation.md) |
| 16 | פיתוחים עתידיים | [`chapters/16-future.md`](chapters/16-future.md) |
| 17 | סיכום ומסקנות | [`chapters/17-summary.md`](chapters/17-summary.md) |
| 18 | ביבליוגרפיה | [`chapters/18-bibliography.md`](chapters/18-bibliography.md) |

## איך להפיק את הקובץ הסופי (.docx)

```bash
cd bookv3/_docx_build
npm install     # פעם ראשונה בלבד
node build.js   # יוצר export/laser-tracker-book.docx
```

הסקריפט קורא את כל קבצי [`chapters/`](chapters/) לפי הסדר, מקבץ אותם לקובץ Word אחד עם:
- פונט David (גיבוי Arial), 12pt לכל הטקסט
- כיווניות RTL לעברית
- כותרת עליונה: "עוקב לייזר אוטונומי — אדם זבולון"
- כותרת תחתונה: מספרי עמודים מרכזיים
- תוכן עניינים אוטומטי (3 רמות עומק)
- כותרות בכחול (H1/H2/H3) לקריאות

## הבדל מ־v1 ו־v2

- **v1** ([`book/chapters/_old/`](../book/chapters/_old/)) — 12 פרקים לפי חלוקה נושאית חופשית. הטקסט היה אקדמי וצפוף, כ־100 עמודים.
- **v2** ([`book/chapters/`](../book/chapters/)) — אותם 19 קבצים לפי 18 סעיפי המחוון, אבל סגנון עמוס בטבלאות וצ׳קליסטים, ~5,600 שורות (גם הוא קרוב ל־100 עמודים).
- **v3** (כאן) — אותו מבנה 19 קבצים, אבל פרוזה עוקבת לפי הדוגמאות של שורין ואלוש. יעד 50 עמודים מודפסים. טבלאות נשמרות איפה שהן באמת עוזרות (מטריצות חיווט, חלופות עם השוואה).

## ספרי הדוגמה

תיקיית [`examples/`](examples/) מכילה את שני ספרי הפרויקט המקוריים ששימשו כמדריך לסגנון, יחד עם חילוץ הטקסט שלהם (`pdftotext`):

- **גלב שורין (325913580)** — כפפה רובוטית עם MPU6050 + flex sensors → Bluetooth → זרוע רובוטית 6-DOF. ~33 עמודים.
- **דניאל אלוש (215176850)** — graphic equalizer חמש־רצועתי על ESP32-S3 עם DSP biquad IIR. ~30 עמודים.
