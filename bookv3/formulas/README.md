# Formulas — Render-Then-Screenshot

The .docx pipeline doesn't render LaTeX. The three block formulas in the book live here as standalone files, you render each one, screenshot, and paste into the .docx at the marker that was left in the corresponding chapter (search for `[נוסחה NN]`).

## Fastest way to render

Click each `Preview` link below. It opens a CodeCogs URL that renders the equation as a high-DPI PNG with a white background. Right-click → "Save image as…" or just screenshot it, then paste into Word.

If CodeCogs is offline, alternatives:
- [QuickLaTeX](https://www.quicklatex.com/) — paste the LaTeX source, click "Render", screenshot
- [Overleaf](https://www.overleaf.com/) — paste into a new project with `\documentclass{standalone}`, compile to PDF, crop
- Local: `pdflatex` on the `.tex` file, then crop the PDF page

---

## Formula 01 — PID Equation

**Chapter:** §4 (מושגים) — appears right after the sentence "מחשבת תיקון פרופורציוני לשגיאה (P), לסכומה לאורך זמן (I), ולקצב השינוי שלה (D):"

**Marker in chapter:** `[נוסחה 01 — משוואת PID]`

**LaTeX source ([01-pid-equation.tex](01-pid-equation.tex)):**

```latex
u(t) = K_p \cdot e(t) + K_i \int e(t)\, dt + K_d \cdot \frac{de}{dt}
```

**Preview:** [Render in CodeCogs](https://latex.codecogs.com/png.latex?\dpi{300}\bg_white%20u(t)%20=%20K_p%20\cdot%20e(t)%20+%20K_i%20\int%20e(t)\,%20dt%20+%20K_d%20\cdot%20\frac{de}{dt})

---

## Formula 02 — Laser Current-Limiting Resistor

**Chapter:** §15.1 (תיעוד הפתרון — חישובי הנגדים) — appears right after "עם V_supply = 5V:"

**Marker in chapter:** `[נוסחה 02 — נגד הגבלת זרם ללייזר]`

**LaTeX source ([02-laser-resistor.tex](02-laser-resistor.tex)):**

```latex
R = \frac{V_{supply} - V_f}{I_d} = \frac{5 - 3}{0.020} = 100\,\Omega
```

**Preview:** [Render in CodeCogs](https://latex.codecogs.com/png.latex?\dpi{300}\bg_white%20R%20=%20\frac{V_{supply}%20-%20V_f}{I_d}%20=%20\frac{5%20-%203}{0.020}%20=%20100\,\Omega)

---

## Formula 03 — MOSFET Gate Resistor

**Chapter:** §15.1 (תיעוד הפתרון — חישובי הנגדים) — appears right after "עם V_GPIO = 3.3V ו־I_max ≈ 15mA:"

**Marker in chapter:** `[נוסחה 03 — נגד Gate של MOSFET]`

**LaTeX source ([03-gate-resistor.tex](03-gate-resistor.tex)):**

```latex
R = \frac{V_{GPIO}}{I_{max}} = \frac{3.3}{0.015} = 220\,\Omega
```

**Preview:** [Render in CodeCogs](https://latex.codecogs.com/png.latex?\dpi{300}\bg_white%20R%20=%20\frac{V_{GPIO}}{I_{max}}%20=%20\frac{3.3}{0.015}%20=%20220\,\Omega)

---

## How to insert into the .docx after rendering

1. Open `bookv3/export/laser-tracker-book.docx` in Word.
2. `Ctrl+F` → search for `[נוסחה 01` (or 02 or 03).
3. Highlight the marker line.
4. `Insert → Pictures → This Device` and pick the screenshot you just took.
5. Replace the marker; center the image; resize so the symbols are readable but the equation doesn't dominate the page.
6. Repeat for the other two markers.

If a future re-run of `node build.js` overwrites your inserted images, save your edited .docx under a different name (e.g. `laser-tracker-book-final.docx`) before rebuilding.
