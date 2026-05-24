# פרק 6 — האלגוריתמים בפירוט

הפרק מציג את הליבה האלגוריתמית: המתמטיקה של זיהוי HSV, משוואות
PID, ומכונת המצבים של `tracker.py` עם Coast ו־Recenter. כל אלגוריתם
מתואר במונחים מתמטיים, בקוד, ובמורכבות זמן/זיכרון.

## 6.1 זיהוי המטרה (`detector.py`)

### 6.1.1 בעיה אלגוריתמית

בהינתן פריים BGR בגודל $W \times H$ (640×480 = 307,200 פיקסלים),
למצוא את מרכז המסה של האזור בעל גוון מסוים (כחול), או להחזיר
`None` אם אזור כזה לא קיים.

### 6.1.2 רקע — מרחבי צבע

#### RGB

הצבע מיוצג בשלושה ערכים $(R, G, B)$, כל אחד ב־$[0, 255]$. שינוי
תאורה משנה את שלושת הערכים יחד. פיקסל כחול בהיר יכול להיות
`(50, 100, 200)` בתאורה אחת ו־`(20, 50, 100)` באחרת. סף כמו
`R < 50, G < 100, B > 150` לא יתפוס את שני המצבים.

#### HSV

מרחב שמפריד **גוון** מ**רוויה** מ**ערך**. הצבע מקודד רק ב־Hue,
שיציב תחת שינויי תאורה.

- $H \in [0, 179]$ ב־OpenCV (חצי מ־$[0, 359]$ כדי להישמר ב־byte).
- $S \in [0, 255]$ (0 = אפור, 255 = רוויה מלאה).
- $V \in [0, 255]$ (0 = שחור, 255 = בהיר מלא).

#### המרה מ־BGR ל־HSV

הנוסחה המתועדת ב־OpenCV:

$$V = \max(R, G, B)$$

$$S = \begin{cases}
\dfrac{V - \min(R,G,B)}{V} & V > 0 \\
0 & V = 0
\end{cases}$$

$$H = \begin{cases}
60 \cdot \dfrac{G - B}{V - \min(R,G,B)} & V = R \\
120 + 60 \cdot \dfrac{B - R}{V - \min(R,G,B)} & V = G \\
240 + 60 \cdot \dfrac{R - G}{V - \min(R,G,B)} & V = B
\end{cases}$$

לאחר החישוב, $H$ ב־OpenCV מחולק ב־2 כדי להתאים ל־$[0, 179]$.

ה־H של פיקסל לא משתנה כאשר התאורה משתנה — רק ה־V משתנה. לכן סף
על H יציב יותר מסף על RGB.

### 6.1.3 הצינור המלא

#### שלב 1 — Gaussian Blur

לפני המרה ל־HSV, פילטר Gaussian בגודל 5×5 מוחל על הפריים. המטרה:
החלקת רעש פיקסל־בודד.

קרנל Gaussian בגודל $5 \times 5$ עם $\sigma = 1$:

$$G(x, y) = \frac{1}{2\pi\sigma^2} e^{-\frac{x^2 + y^2}{2\sigma^2}}$$

עבור כל פיקסל בתמונה החדשה:

$$I'(x, y) = \sum_{i=-2}^{2} \sum_{j=-2}^{2} G(i, j) \cdot I(x+i, y+j)$$

OpenCV מבצע זאת ב־$O(W \cdot H)$ (separable convolution).

#### שלב 2 — המרת BGR → HSV

`cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)` — $O(W \cdot H)$.

#### שלב 3 — סף בינארי

`mask = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)` בודק עבור כל פיקסל:

$$\text{mask}(x, y) = \begin{cases}
255 & H_{\min} \le H(x,y) \le H_{\max} \text{ AND } S_{\min} \le S(x,y) \le S_{\max} \text{ AND } V_{\min} \le V(x,y) \le V_{\max} \\
0 & \text{otherwise}
\end{cases}$$

ערכי הכיול (כחול, תאורת תקרה):

::: {dir=ltr}
```python
HSV_LOWER = [79, 76, 0]
HSV_UPPER = [105, 255, 255]
```
:::

מורכבות: $O(W \cdot H)$.

#### שלב 4 — מורפולוגיה

המסכה הראשונית מכילה בדרך כלל רעש: ספקלים בודדים שעוברים את הסף
בגלל קומפרסיה JPEG או רעש חיישן.

##### Erosion

עבור כל פיקסל לבן ב־mask, אם **לא** כל השכנים שלו ברדיוס $3 \times 3$
לבנים — הגדר אותו לשחור. מסיר ספקלים בודדים אבל גם מקצץ את גבולות
המטרה.

::: {dir=ltr}
```python
mask = cv2.erode(mask, None, iterations=2)
```
:::

##### Dilation

הפעולה ההפוכה — עבור כל פיקסל לבן, צבע גם את כל השכנים. משחזר את
גבולות המטרה.

::: {dir=ltr}
```python
mask = cv2.dilate(mask, None, iterations=2)
```
:::

הצירוף `erode → dilate` נקרא **Morphological Opening**. התוצאה:
מסכה נקייה שהרעש סולק ממנה אבל המטרה שמרה על גודלה הקרוב למקור.

הסיבה ל־`iterations=2`: עם ערך 1 ספקלים של 1 פיקסל נסגרים, אבל
ספקלים של 2 פיקסלים עוברים. עם 2 איטרציות הם נתפסים.

מורכבות: $O(W \cdot H)$ לכל איטרציה — סך הכל $O(4 W H)$.

#### שלב 5 — מציאת קונטורים

::: {dir=ltr}
```python
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```
:::

`findContours` מאתר את חלקי הקצוות של כל קבוצת פיקסלים לבנה
מחוברת.

- **`RETR_EXTERNAL`** — רק קונטורים חיצוניים. אם המטרה כוללת חור,
  החור לא ייכלל.
- **`CHAIN_APPROX_SIMPLE`** — שמירת נקודות הקצה של פלגי קווים
  ישרים, לא כל פיקסל. חיסכון משמעותי לקונטור מלבני.

מורכבות: $O(W \cdot H)$ + $O(\text{total contour length})$.

#### שלב 6 — בחירת הגדול ביותר

::: {dir=ltr}
```python
largest = max(contours, key=cv2.contourArea)
```
:::

$O(N)$ כאשר $N$ הוא מספר הקונטורים — בדרך כלל 1–5.

`cv2.contourArea` משתמש ב־**Shoelace formula** לרב־צלע סגור:

$$A = \frac{1}{2} \left| \sum_{i=0}^{n-1} (x_i \cdot y_{i+1} - x_{i+1} \cdot y_i) \right|$$

מורכבות: $O(n)$ כאשר $n$ הוא מספר הנקודות בקונטור.

#### שלב 7 — סינון לפי שטח

::: {dir=ltr}
```python
if cv2.contourArea(largest) < MIN_CONTOUR_AREA:
    return None
```
:::

עם `MIN_CONTOUR_AREA = 200` — כל בלוב קטן יותר מ־~14×14 פיקסלים
נחשב לרעש. הסף תלוי במרחק הצפוי מהמטרה.

#### שלב 8 — חישוב מרכז המסה

באמצעות **moments**. ה־moment של תמונה בינארית:

$$m_{ij} = \sum_{x, y} x^i \cdot y^j \cdot I(x, y)$$

עבור $I(x, y) \in \{0, 1\}$ (מסכה):

- $m_{00}$ = שטח (סך הפיקסלים השווים ל־1).
- $m_{10}$ = סכום ה־x של כל הפיקסלים.
- $m_{01}$ = סכום ה־y.

מרכז המסה:

$$(c_x, c_y) = \left( \frac{m_{10}}{m_{00}}, \frac{m_{01}}{m_{00}} \right)$$

::: {dir=ltr}
```python
M = cv2.moments(largest)
cx = int(M["m10"] / M["m00"])
cy = int(M["m01"] / M["m00"])
return (cx, cy)
```
:::

מורכבות: $O(n)$.

### 6.1.4 מורכבות זמן כוללת

הצינור כולו:

$$T_{detect}(W, H) = O(W \cdot H)$$

ב־$W=640, H=480$ — ~307K פיקסלים. הקבועים בכל שלב נמוכים — בפועל
זמן ריצה ~5–8ms על Pi 4B, מאפשר 30 fps בנוחות.

### 6.1.5 מקרים מיוחדים

| מקרה | התנהגות |
|---|---|
| אין קונטורים אחרי `findContours` | החזרת `None` |
| הקונטור הגדול קטן מ־`MIN_CONTOUR_AREA` | החזרת `None` |
| `M["m00"] == 0` (גארד נוסף) | החזרת `None` |
| כמה קונטורים בגודל דומה | בחירת הגדול; הקטנים מתעלמים |

## 6.2 בקרת PID

### 6.2.1 פורמליזם

בקר PID הוא מעגל בקרה שמטרתו לצמצם את השגיאה $e(t)$ — ההפרש בין
ערך רצוי (setpoint) לבין ערך מדוד — לאפס:

$$u(t) = K_p \cdot e(t) + K_i \cdot \int_{0}^{t} e(\tau) d\tau + K_d \cdot \frac{de(t)}{dt}$$

- **$K_p$ — Proportional:** תיקון פרופורציוני לשגיאה הנוכחית.
- **$K_i$ — Integral:** מצטבר לאורך זמן. מסלק סטיות מתמידות
  שה־P לא יכול לסגור.
- **$K_d$ — Derivative:** קצב השינוי של השגיאה. מבחין במגמות
  ומגיב לפני שהן מתפתחות.

### 6.2.2 צורה דיסקרטית

המערכת דוגמת ב־30 fps, $\Delta t \approx 33$ms. הצורה הדיסקרטית:

$$u_k = K_p \cdot e_k + K_i \sum_{i=0}^{k} e_i \cdot \Delta t + K_d \cdot \frac{e_k - e_{k-1}}{\Delta t}$$

זו הצורה שמופיעה בספריית `simple_pid`. הקוד פשוט:

::: {dir=ltr}
```python
pan_pid = PID(KP_PAN, KI_PAN, KD_PAN, setpoint=0, output_limits=(-LIM, LIM))
correction = pan_pid(error)   # מחושב אוטומטית עם dt מובנה
```
:::

### 6.2.3 ההגדרות בפרויקט

| פרמטר | ערך | משמעות |
|---|:---:|---|
| `setpoint` | 0 | רוצים שהשגיאה (קואורדינטה - מרכז) תהיה אפס |
| `KP_PAN`, `KP_TILT` | 0.017 | תיקון פרופורציונלי |
| `KI_PAN`, `KI_TILT` | 0.0 | אינטגרל לא נחוץ — אין offset מתמיד |
| `KD_PAN`, `KD_TILT` | 0.0 | דריבטיב הגביר רעש — הוסר |
| `output_limits` | (-10°, +10°) | חיתוך תיקון לפר־פריים |

#### למה לא Ki

PID במצב P-only "מסיים" במצב שבו השגיאה הקטנה ביותר נחוצה כדי
שהבקר ימשיך לתקן. במערכות עם חיכוך מתמיד (רובוט שמטפס במדרון),
$K_i$ נחוץ למילוי הפער. כאן, ברגע שהשגיאה מגיעה ל־0, הסרוו עוצר
ושום כוח חיצוני לא דוחף אותו לסטייה.

#### למה לא Kd

$K_d$ מבחין בקצב השינוי של השגיאה. הבעיה: המקור של השגיאה הוא
detector עם רעש פריים־לפריים של ~10 פיקסלים. הקצב המדומה של הרעש
($\Delta e = 10$ ב־$\Delta t = 33$ms) מתפרש על־ידי $K_d$ כ"שגיאה
משתנה במהירות" ומקבל תיקון מוגזם. התוצאה: רעידות.

אם הזרם של ה־detector היה נקי יותר (אולי אחרי פילטר Kalman),
$K_d$ קטן יכול היה לעבוד. עם הרעש שיש כאן, נקי יותר ויעיל יותר
בלי $K_d$.

### 6.2.4 חשיבות `output_limits`

ה־`output_limits` מצמידים את התיקון לטווח $[-10°, +10°]$ לכל
פריים. הסיבות:

1. **בטיחות מכאנית:** בלי הגבלה, בקר עם $K_p = 0.017$ ושגיאה של
   300 פיקסלים יבקש תיקון של 5.1°. עם שגיאה של 1000 פיקסלים — 17°.
   הגבלה מונעת קפיצות גדולות.
2. **יציבות:** קפיצה של 17° עוברת בפריים אחד את מרכז התמונה,
   ובפריים הבא PID מבקש תיקון של 17° בכיוון הפוך — אסילציה.
3. **Anti-windup:** עם $K_i > 0$, חישוב האינטגרל יכול לצבור ערכים
   גדולים. `output_limits` ב־`simple_pid` כולל clamping של
   האינטגרל. כאן עם $K_i = 0$ זה לא רלוונטי, אבל הכלי קיים.

### 6.2.5 חישוב התיקון בפועל

::: {dir=ltr}
```python
target_x, target_y = detector.detect(frame)   # למשל (400, 270)
pan_error  = target_x - FRAME_CENTER_X        # 400 - 320 = +80
tilt_error = target_y - FRAME_CENTER_Y        # 270 - 240 = +30

pan_correction  = pan_pid(pan_error)          # K_p * 80 = 1.36°
tilt_correction = tilt_pid(tilt_error)        # K_p * 30 = 0.51°

servo.move_pan(kit, servo.current_pan() + pan_correction, ramp=False)
servo.move_tilt(kit, servo.current_tilt() + tilt_correction, ramp=False)
```
:::

### 6.2.6 כיוון הסימן

`simple_pid` מחשב $e = \text{setpoint} - \text{input}$. הקוד מזין
$\text{input} = \text{target} - \text{center}$ ו־$\text{setpoint} = 0$,
ולכן $e = -(\text{target} - \text{center}) = -\Delta x$.

עם $K_p > 0$, אם $\Delta x > 0$ (מטרה מימין), הבקר מחזיר תיקון
$u < 0$. הקוד שולח לסרוו: `current_pan + u`. אם "ימינה" מתאים
לזווית גדולה יותר, אז כדי לזוז ימינה צריך $u > 0$ — סימן שגוי
יחייב היפוך של $K_p$.

בכיול הראשון בדקנו את הסימן אמפירית — הברקט התקדם לעבר המטרה ולא
ממנה, אז הסימן היה תקין מההתחלה. אילו היה לא תקין, היה מספיק לשנות
`KP_PAN = 0.017` ל־`KP_PAN = -0.017`.

## 6.3 לוגיקת ה־Deadband

### 6.3.1 בעיה

ה־detector מחזיר centroid עם רעש פריים־לפריים של ~10 פיקסלים. מטרה
סטטית ב־(320, 240) — בדיוק במרכז — תזוז בין (315, 238), (323, 242),
(318, 240) בפריימים עוקבים. PID יראה כאילו השגיאה משתנה ויבקש תיקון
בכל פריים. הסרוו ירטוט.

### 6.3.2 פתרון

לפני שפעולת PID מבוצעת, בודקים אם השגיאה בתוך deadband:

::: {dir=ltr}
```python
in_deadband = (abs(pan_error) < TRACKING_DEADBAND_PX
               and abs(tilt_error) < TRACKING_DEADBAND_PX)
if in_deadband:
    # המטרה במרכז — לא לזוז, החזר 0 לתיקון, אפס את coast state
    _reset_coast()
    return {..., "in_deadband": True}
```
:::

עם `TRACKING_DEADBAND_PX = 15` — שווה בערך לרעש המקסימלי של
ה־detector שנמדד (~10–12 פיקסלים פריים־לפריים).

### 6.3.3 אינטראקציה עם Coast

כאשר נכנסים ל־deadband, מאפסים את coast state. הסיבה: אם המטרה
עומדת במקום במרכז ואז נעלמת פתאומית (היד הזיזה אותה מחוץ לפריים),
אסור ל־`tracker.update()` לעשות coast לאיזה כיוון — אין כיוון.
השמירה על המקום היא ההתנהגות הנכונה.

## 6.4 מכונת מצבים של `tracker.update()`

### 6.4.1 חמשת המצבים

::: {dir=ltr}
```
Tracking (active PID)   →  target reaches deadband  →  Locked (deadband)
       ↑                                                      ↓
       └────  target leaves deadband ────────────────────────┘
       │
       │  target lost (last correction meaningful)
       ↓
   Coasting (apply last correction × decay)
       │
       │  coast frames exhausted OR both axes clamped
       ↓
   Recentering (return to PAN_CENTER, TILT_CENTER)
       │
       │  reached center OR target re-acquired
       ↓
   Tracking / Locked

Holding ← target lost while in deadband (no direction to coast)
```
:::

### 6.4.2 חישוב Coast Decay

יהי $d$ מקדם הדעיכה לפריים (`COAST_DECAY = 0.95`). ה־decay לאחר
$n$ פריימים:

$$c_n = c_0 \cdot d^{\,n}$$

עם $d = 0.95$ ו־$n = 30$:

$$c_{30} = c_0 \cdot 0.95^{30} \approx c_0 \cdot 0.215$$

אחרי 30 פריימים התיקון יורד ל־~22% מהמקדם המקורי. הברקט לא נעצר
חד אלא הדרגתי. שיא של ~1 שנייה של "אינרציה" שמדמה ראייה אנושית.

### 6.4.3 חישוב Recenter Time

יהי $s$ צעד ה־Recenter לפריים (`RECENTER_STEP_DEG = 2°`). עם $s = 2°$
ו־30 fps:

- מהירות recenter: $60°/\mathrm{sec}$
- זמן לחזרה ממקסימום סטיית פאן: $170° / 60 = 2.83\,\mathrm{s}$
- מקסימום סטיית טילט: $90° / 60 = 1.5\,\mathrm{s}$

בפועל זה לרוב פחות (לא מגיעים לקצוות לעיתים קרובות).

## 6.5 מורכבות לולאת המעקב

| פעולה | מורכבות |
|---|---|
| `camera.capture_frame()` | $O(1)$ syscall (תלוי בקצב המצלמה) |
| `detector.detect()` | $O(W \cdot H)$ — דומיננטי |
| `tracker.update()` PID | $O(1)$ |
| `servo.move_*` עם `ramp=False` | $O(1)$ syscall I²C |

סך הכל לפר־פריים: $O(W \cdot H)$ עם קבוע נמוך.

ב־$W=640, H=480$ — ~5–8ms פעולה רציפה. הפנאי הנותר בתוך 33ms מאפשר
לוגיקה עתידית (multi-target, depth, overlay) בלי דאגה לקצב.
