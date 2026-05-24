# ספר הפרויקט — עוקב לייזר אוטונומי (גרסה v3)

מקור הגרסה השלישית של ספר הפרויקט. המבנה נשמר 1:1 לפי המחוון של שאלון 714916 ([`docs/מחוון.pdf`](../docs/מחוון.pdf)), אבל הסגנון נכתב מחדש בהתאם לשני ספרי דוגמה משנים קודמות (גלב שורין, דניאל אלוש — נמצאים ב־[`examples/`](examples/)): פרוזה קצרה ולעניין, מעט טבלאות, יעד של כ־50 עמודים מודפסים.

כל פרק קיים כקובץ Markdown נפרד תחת [`chapters/`](chapters/), תרשימי מרמייד תחת [`diagrams/`](diagrams/), נוסחאות מתמטיות תחת [`formulas/`](formulas/), ותמונות תחת [`photos/`](photos/). בניית קובץ ה־.docx הסופי נעשית דרך [`build-book.sh`](build-book.sh) שמרכיב את כל ה־19 הפרקים לקובץ אחד ב־[`export/laser-tracker-book.docx`](export/laser-tracker-book.docx).

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

תלויות (התקנה חד־פעמית):

- **pandoc** — `winget install --id JohnMacFarlane.Pandoc`
- **python 3** (stdlib בלבד, לא דורש pip install)
- **bash** — Git Bash על Windows, או shell תקני על Linux/macOS

הרצה:

```bash
cd bookv3
bash build-book.sh
```

הסקריפט מבצע:

1. יוצר תוכן עניינים סטטי מכותרות ה־H1 של כל פרק.
2. משרשר את 19 הפרקים לקובץ markdown אחד, עם שבירות עמוד בין הפרקים (raw OpenXML `<w:br w:type="page"/>`).
3. מריץ `pandoc` עם [`reference.docx`](reference.docx) כתבנית עיצובית — קובע פונט, צבעים, header, footer.
4. Post-processor ב־Python מבצע ניקוי על ה־OpenXML:
   - חיבור header/footer ל־sectPr (pandoc משכפל את ה־XML אך לא מקשר את ה־references).
   - אילוץ LTR על בלוקי קוד (אחרת הם יורשים את ה־bidi של הסעיף).
   - הסרת `<w:bookmarkStart>` ו־`<w:bookmarkEnd>` (Google Docs מציג אותם כסרטים כחולים מציקים).
   - הוספת גבולות לכל הטבלאות (במידה ו־pandoc לא הוסיף).
   - הצללת השורה הראשונה של כל טבלה בכחול בהיר (`DCE6F1`).

הפלט: [`export/laser-tracker-book.docx`](export/laser-tracker-book.docx) — כ־80KB, פותח ב־Word, Google Docs, או LibreOffice.

## תבנית העיצוב — `reference.docx`

[`reference.docx`](reference.docx) הוא עותק מותאם של reference.docx של גלב שורין מפרויקט קודם. השינויים שעשינו:

- פונט: David → **Arial** (לכל המסמך — body, headings, header, footer).
- טקסט ה־header עודכן ל"אדם זבולון | עוקב לייזר אוטונומי מבוסס Raspberry Pi".

כל שאר הסגנון נשמר זהה לזה של גלב: כותרות בכחול (`4F81BD`), Body 12pt, header עם קו תחתון, footer עם מספר עמוד וקו עליון, יישור RTL ברירת מחדל.

אם מצרפים מחדש את reference.docx של גלב (למשל אחרי שדרוג):

```bash
cp "C:/path/to/gal/reference.docx" bookv3/reference.docx
python _setup/patch-reference-docx.py
```

הסקריפט אידמפוטנטי — אפשר להריץ אותו שוב ושוב בלי לפגוע.

## נוסחאות מתמטיות

ה־.docx pipeline לא מרנדר LaTeX. שלוש נוסחאות הבלוק שבספר נמצאות תחת [`formulas/`](formulas/) כקבצי `.tex` נפרדים, ובמקום בו הן צריכות להופיע ב־.docx נשאר marker בצורה `[נוסחה NN — תיאור]`. ראה [`formulas/README.md`](formulas/README.md) להוראות רינדור (קישור CodeCogs לכל נוסחה) והדבקה ידנית.

## הבדל מ־v1 ו־v2

- **v1** ([`book/chapters/_old/`](../book/chapters/_old/)) — 12 פרקים לפי חלוקה נושאית חופשית. הטקסט היה אקדמי וצפוף, כ־100 עמודים.
- **v2** ([`book/chapters/`](../book/chapters/)) — אותם 19 קבצים לפי 18 סעיפי המחוון, אבל סגנון עמוס בטבלאות וצ׳קליסטים, ~5,600 שורות (גם הוא קרוב ל־100 עמודים). הבנייה הייתה עם `docx.js` של Node.
- **v3** (כאן) — אותו מבנה 19 קבצים, פרוזה קצרה לפי הדוגמאות של שורין ואלוש. יעד 50 עמודים. הבנייה עברה ל־pandoc + Python post-processor (זהה לפייפליין של פרויקט "גל").

הקוד הישן של docx.js נשמר תחת [`_docx_build_legacy/`](_docx_build_legacy/) למקרה שצריך לחזור אליו.

## ספרי הדוגמה

תיקיית [`examples/`](examples/) מכילה את שני ספרי הפרויקט המקוריים ששימשו כמדריך לסגנון, יחד עם חילוץ הטקסט שלהם (`pdftotext`):

- **גלב שורין (325913580)** — כפפה רובוטית עם MPU6050 + flex sensors → Bluetooth → זרוע רובוטית 6-DOF. ~33 עמודים.
- **דניאל אלוש (215176850)** — graphic equalizer חמש־רצועתי על ESP32-S3 עם DSP biquad IIR. ~30 עמודים.
