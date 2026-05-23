# פרק 6 — האלגוריתמים בפירוט

פרק זה מציג את הפנים האלגוריתמיים של המערכת: מהמתמטיקה של זיהוי
מבוסס HSV, דרך משוואות בקרת PID, ועד למכונת המצבים של `tracker.py`
שכוללת Coast ו־Recenter. כל אלגוריתם מתואר במונחים מתמטיים, בקוד, וב־
מורכבות זמן/זיכרון.

## 6.1 אלגוריתם זיהוי המטרה (`detector.py`)

### 6.1.1 בעיה אלגוריתמית

בהינתן פריים BGR בגודל $W \times H$ (640×480 = 307,200 פיקסלים),
למצוא את **מרכז המסה** של האזור בעל גוון מסוים (כחול במקרה שלנו),
או להחזיר `None` אם אזור כזה לא קיים.

### 6.1.2 רקע — מרחבי צבע

#### RGB

הצבע של פיקסל מיוצג בשלושה ערכים — אדום (R), ירוק (G), כחול (B), כל
אחד ב־[0, 255]. **בעיה לזיהוי:** שלושת הערכים משתנים כולם כאשר התאורה
משתנה. פיקסל כחול בהיר יכול להיות `(50, 100, 200)` בתאורה אחת ו־
`(20, 50, 100)` בתאורה אחרת. סף כמו `R < 50, G < 100, B > 150` לא
ידע לעמוד בכל הוריאציות.

#### HSV (Hue, Saturation, Value)

מרחב צבע שמפריד **גוון** (אילו "אורך גל") מ**רוויה** ("עוצמת הצבע")
מ**ערך** ("בהירות"). הצבע עצמו מקודד רק ב־Hue, והוא **בלתי תלוי בתאורה**
ברוב המקרים.

- $H \in [0, 179]$ ב־OpenCV (חצי מ־[0, 359] כדי שיוכל להישמר ב־byte)
- $S \in [0, 255]$ (0 = אפור, 255 = רוויה מלאה)
- $V \in [0, 255]$ (0 = שחור, 255 = בהיר מלא)

#### המרה מ־BGR ל־HSV

הנוסחה (מתועדת ב־OpenCV):

$$V = \max(R, G, B)$$

$$S = \begin{cases}
\frac{V - \min(R,G,B)}{V} & \text{if } V > 0 \\
0 & \text{otherwise}
\end{cases}$$

$$H = \begin{cases}
60 \cdot \frac{G - B}{V - \min(R,G,B)} & \text{if } V = R \\
120 + 60 \cdot \frac{B - R}{V - \min(R,G,B)} & \text{if } V = G \\
240 + 60 \cdot \frac{R - G}{V - \min(R,G,B)} & \text{if } V = B
\end{cases}$$

(אחרי החישוב, $H$ ב־OpenCV מסולק ב־2 כדי להתאים ל־[0, 179]).

ה־H של פיקסל **לא משתנה** כאשר התאורה משתנה — רק ה־V משתנה. לכן סף
על H יציב יותר מסף על RGB.

### 6.1.3 הצינור המלא (Pipeline)

#### שלב 1 — Gaussian Blur

לפני המרה ל־HSV, מחילים פילטר Gaussian בגודל 5×5 על הפריים. המטרה:
להחליק רעש פיקסל־בודד (sensor noise) כך שספקלים קטנים לא יישברו את
המטרה.

הקרנל של Gaussian בגודל $5 \times 5$ עם $\sigma = 1$:

$$G(x, y) = \frac{1}{2\pi\sigma^2} e^{-\frac{x^2 + y^2}{2\sigma^2}}$$

עבור כל פיקסל בתמונה החדשה:

$$I'(x, y) = \sum_{i=-2}^{2} \sum_{j=-2}^{2} G(i, j) \cdot I(x+i, y+j)$$

OpenCV מבצע זאת ב־$O(W \cdot H)$ (קונבולוציה separable).

#### שלב 2 — המרת BGR → HSV

`cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)`. $O(W \cdot H)$.

#### שלב 3 — סף בינארי (Thresholding)

`mask = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)` בודק עבור כל פיקסל:

$$\text{mask}(x, y) = \begin{cases}
255 & \text{if } H_{\min} \le H(x,y) \le H_{\max} \text{ AND } S_{\min} \le S(x,y) \le S_{\max} \text{ AND } V_{\min} \le V(x,y) \le V_{\max} \\
0 & \text{otherwise}
\end{cases}$$

עם הערכים שלנו (כחול, תאורת תקרה):

```
HSV_LOWER = [79, 76, 0]
HSV_UPPER = [105, 255, 255]
```

$O(W \cdot H)$.

#### שלב 4 — חבילות מורפולוגיות (Morphological Operations)

המסכה הראשונית מכילה בדרך כלל **רעש**: ספקלים בודדים שעוברים את הסף
בגלל קומפרסיה JPEG או רעש חיישן.

##### Erosion (חיתוך)

עבור כל פיקסל לבן ב־mask, בדוק אם כל השכנים שלו ברדיוס 3×3 גם הם
לבנים. אם לא — הגדר אותו לשחור.

זה **מסיר ספקלים בודדים** אבל גם מקצץ את גבולות המטרה הלגיטימית.

```python
mask = cv2.erode(mask, None, iterations=2)
```

##### Dilation (הרחבה)

הפעולה ההפוכה — עבור כל פיקסל לבן ב־mask, צבע גם את כל השכנים שלו
ב־3×3. **משחזר את גבולות המטרה** שאיבדה בעת ה־Erosion.

```python
mask = cv2.dilate(mask, None, iterations=2)
```

הצירוף `erode → dilate` נקרא **Morphological Opening**. התוצאה: מסכה
נקייה שבה רעש כבר לא קיים, אבל המטרה עצמה שמרה על גודלה הקרוב למקור.

הסיבה ש־iterations=2: עם ערך 1 הספקלים הקטנים נסגרים, אבל ספקלים של
2 פיקסלים עוברים. עם 2 הסיכוי שיתפסו גדל.

$O(W \cdot H)$ לכל איטרציה — סה"כ $O(4 W \cdot H)$.

#### שלב 5 — מציאת קונטורים (Contour Finding)

```python
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

`findContours` מאתר את **חלקי הקצוות** של כל קבוצת פיקסלים לבנה
מחוברת.

- `RETR_EXTERNAL`: רק קונטורים חיצוניים (אם המטרה יוצרת בלוב עם חור
  פנימי, החור לא ייכלל כקונטור נפרד).
- `CHAIN_APPROX_SIMPLE`: שמירת רק נקודות הקצה של פילגי קווים ישרים,
  לא כל פיקסל. חיסכון משמעותי במקרה של קונטור מלבני.

$O(W \cdot H)$ + $O(\text{total contour length})$.

#### שלב 6 — בחירת הקונטור הגדול ביותר

```python
largest = max(contours, key=cv2.contourArea)
```

$O(N)$ כאשר $N$ הוא מספר הקונטורים — בדרך כלל 1–5.

`cv2.contourArea` משתמש בפורמולה של **Shoelace** (Surveyor's
Formula) לחישוב שטח רב־צלע סגור:

$$A = \frac{1}{2} \left| \sum_{i=0}^{n-1} (x_i \cdot y_{i+1} - x_{i+1} \cdot y_i) \right|$$

$O(n)$ כאשר $n$ הוא מספר הנקודות בקונטור.

#### שלב 7 — סינון לפי שטח

```python
if cv2.contourArea(largest) < MIN_CONTOUR_AREA:
    return None
```

עם `MIN_CONTOUR_AREA = 200` — כל בלוב קטן יותר מ־~14×14 פיקסלים נחשב
לרעש ולא למטרה. הסף הזה תלוי במרחק שלך הצפוי מהמטרה.

#### שלב 8 — חישוב מרכז המסה (Centroid)

באמצעות **moments**. ה־**moment** של תמונה בינארית מוגדר כך:

$$m_{ij} = \sum_{x, y} x^i \cdot y^j \cdot I(x, y)$$

עבור $I(x, y) \in \{0, 1\}$ (מסכה):

- $m_{00}$ = שטח (סך הפיקסלים השווים ל־1)
- $m_{10}$ = סכום ה־x של כל הפיקסלים = 0
- $m_{01}$ = סכום ה־y

**מרכז המסה:**

$$(c_x, c_y) = \left( \frac{m_{10}}{m_{00}}, \frac{m_{01}}{m_{00}} \right)$$

הקוד:

```python
M = cv2.moments(largest)
cx = int(M["m10"] / M["m00"])
cy = int(M["m01"] / M["m00"])
return (cx, cy)
```

$O(n)$ כאשר $n$ הוא מספר הנקודות בקונטור.

### 6.1.4 מורכבות זמן כוללת

הצינור כולו:

$$T_{detect}(W, H) = O(W \cdot H)$$

ב־$W = 640, H = 480$ זה ~307K פיקסלים. הקבועים בכל שלב נמוכים — בפועל
זמן ריצה ~5–8ms על Pi 4B, מאפשר 30fps בנוחות.

### 6.1.5 מקרים מיוחדים

| מקרה | התנהגות |
|---|---|
| אין קונטורים אחרי `findContours` | החזרת `None` |
| הקונטור הגדול קטן מ־`MIN_CONTOUR_AREA` | החזרת `None` |
| `M["m00"] == 0` (אסור — שטח חיובי כבר עברנו) | החזרת `None` (guard) |
| יש כמה קונטורים בגודל דומה | בחירת הגדול ביותר; הקטנים מתעלמים |

## 6.2 בקרת PID

### 6.2.1 פורמליזם

בקר PID (Proportional-Integral-Derivative) הוא מעגל בקרה שמטרתו
לצמצם את **השגיאה** $e(t)$ — ההבדל בין ערך הרצוי (setpoint) לבין הערך
המדוד — לאפס. הפלט שלו הוא תיקון $u(t)$:

$$u(t) = K_p \cdot e(t) + K_i \cdot \int_{0}^{t} e(\tau) d\tau + K_d \cdot \frac{de(t)}{dt}$$

- **$K_p$ — Proportional:** תיקון פרופורציוני לשגיאה הנוכחית.
  אם השגיאה גדולה, התיקון גדול.
- **$K_i$ — Integral:** מצטבר של השגיאה לאורך זמן. מסלק "סטיות
  מתמידות" שה־P לבד לא יכול לסגור.
- **$K_d$ — Derivative:** קצב השינוי של השגיאה. מבחין במגמות —
  אם השגיאה גוברת מהר, תוסיף תיקון משמעותי כדי להאט.

### 6.2.2 צורה דיסקרטית

המערכת שלנו דוגמת ב־30fps, כלומר $\Delta t \approx 33$ms. הצורה
הדיסקרטית של המשוואה:

$$u_k = K_p e_k + K_i \sum_{i=0}^{k} e_i \cdot \Delta t + K_d \cdot \frac{e_k - e_{k-1}}{\Delta t}$$

זו הצורה שמופיעה בתוך הספרייה `simple_pid`. אנחנו לא מימשנו אותה
ידנית — הקוד שלנו פשוט:

```python
pan_pid = PID(KP_PAN, KI_PAN, KD_PAN, setpoint=0, output_limits=(-LIM, LIM))
correction = pan_pid(error)  # מחשבת אוטומטית עם dt מובנה
```

### 6.2.3 ההגדרות שלנו

| פרמטר | ערך | משמעות |
|---|:---:|---|
| `setpoint` | 0 | אנחנו רוצים שהשגיאה (קואורדינטה - מרכז התמונה) תהיה אפס |
| `KP_PAN`, `KP_TILT` | 0.017 | תיקון פרופורציונלי |
| `KI_PAN`, `KI_TILT` | 0.0 | אינטגרל לא נחוץ — אין offset מתמיד |
| `KD_PAN`, `KD_TILT` | 0.0 | דריבטיב הגביר רעש — הוסר |
| `output_limits` | (-10°, +10°) | חיתוך תיקון לפר־פריים |

#### למה לא Ki?

ה־PID במצב P-only "מסיים" במצב סטטי שבו השגיאה הקטנה ביותר עדיין
נחוצה כדי שהבקר ימשיך לתקן. במערכות עם **חיכוך מתמיד** (כמו רובוט
שצריך לטפס בשיפוע), $K_i$ נחוץ למילוי הפער. אצלנו, ברגע שהשגיאה
מגיעה ל־0, הסרוו מפסיק לזוז ושום כוח חיצוני לא דוחף אותו לסטיה.
לכן אין צורך ב־Ki.

#### למה לא Kd?

$K_d$ מבחין בקצב השינוי של השגיאה. בעיה במקרה שלנו: **המקור של
השגיאה הוא detector** עם רעש פריים־לפריים של ~10 פיקסלים. הקצב המדומה
של הרעש הזה ($\Delta e = 10$ ב־$\Delta t = 33$ms) מתפרש על־ידי ה־
Kd כ"שגיאה משתנה במהירות" ומקבל תיקון מוגזם. התוצאה: רעידות.

אם הזרם של ה־detector היה נקי יותר (אולי אחרי פילטר Kalman עליו),
$K_d$ קטן יכול היה לעבוד. אבל עם הרעש שיש לנו — נקי יותר ויעיל יותר
בלי $K_d$.

### 6.2.4 חשיבות `output_limits`

ה־`output_limits` מצוקיים את התיקון של ה־PID לטווח [-10°, +10°] לכל
פריים. הסיבות:

1. **בטיחות מכאנית:** בלי הגבלה, בקר עם $K_p = 0.017$ ושגיאה של 300
   פיקסלים יבקש תיקון של 5.1°. עם שגיאה של 1000 פיקסלים (מטרה מחוץ
   לפריים, רק תיאורטית) — 17°. הגבלה מונעת קפיצות גדולות.

2. **חישוב יציבות (Stability):** קפיצה גדולה של 17° תעבור בפריים אחד
   את מרכז התמונה, ובפריים הבא PID יבקש תיקון של 17° בכיוון הפוך —
   אסילציה.

3. **Anti-windup:** עם $K_i > 0$, חישוב האינטגרל יכול לצבור ערכים
   גדולים. `output_limits` ב־`simple_pid` כולל **clamping של
   האינטגרל** כדי למנוע windup. אצלנו עם $K_i = 0$ לא רלוונטי, אבל
   טוב לדעת.

### 6.2.5 חישוב התיקון בפועל

הצעדים בפר־פריים:

```python
target_x, target_y = detector.detect(frame)  # למשל (400, 270)
pan_error  = target_x - FRAME_CENTER_X    # 400 - 320 = +80 (מטרה מימין למרכז)
tilt_error = target_y - FRAME_CENTER_Y    # 270 - 240 = +30 (מטרה מתחת למרכז)

pan_correction  = pan_pid(pan_error)   # מחשב: K_p * 80 = 1.36°
tilt_correction = tilt_pid(tilt_error) # K_p * 30 = 0.51°

# שולחים את התיקון לסרוו (מצומצם לטווח הבטוח על־ידי `servo.move_*`)
servo.move_pan(kit, servo.current_pan() + pan_correction, ramp=False)
servo.move_tilt(kit, servo.current_tilt() + tilt_correction, ramp=False)
```

### 6.2.6 כיוון הסימן

ה־simple_pid מחשב $e = \text{setpoint} - \text{input}$. אנחנו מזינים
$\text{input} = \text{target} - \text{center}$ ו־$\text{setpoint} = 0$,
ולכן $e = -(\text{target} - \text{center}) = -(\Delta x)$.

עם $K_p > 0$, אם $\Delta x > 0$ (מטרה מימין), הבקר מחזיר תיקון
$u < 0$. נשלוף אותו לסרוו: `current_pan + u`. אם הסרוו "ימינה" מתאים
לזווית גדולה יותר, אז כדי לזוז ימינה נצטרך $u > 0$ — סימן שגוי, נהפוך
את ה־$K_p$.

בכיול הראשון של ה־PID בדקנו את הסימן אמפירית — הבכרת התקדמה לעבר
המטרה ולא ממנה, אז הסימן היה תקין מהתחלה. אם הוא לא היה תקין, היה
מספיק לשנות `KP_PAN = 0.017` ל־`KP_PAN = -0.017`.

## 6.3 לוגיקת ה־Deadband

### 6.3.1 בעיה

ה־detector מחזיר centroid עם רעש פריים־לפריים של ~10 פיקסלים. אם
מטרה סטטית ב־(320, 240) — בדיוק במרכז — תזוז בין (315, 238), (323, 242),
(318, 240) בפריימים עוקבים. ה־PID יראה כאילו השגיאה משתנה ויבקש
תיקון בכל פריים. הסרוו ירטוט.

### 6.3.2 פתרון

לפני שהפעולה החסום של ה־PID נחשבת, בודקים אם השגיאה בטווח deadband:

```python
in_deadband = (abs(pan_error) < TRACKING_DEADBAND_PX
               and abs(tilt_error) < TRACKING_DEADBAND_PX)
if in_deadband:
    # המטרה במרכז — לא לזוז, החזר 0 לתיקון, אפס את coast state
    _reset_coast()
    return {..., "in_deadband": True}
```

עם `TRACKING_DEADBAND_PX = 15` — שווה בערך לרעש המקסימלי של ה־detector
שמדדנו (~10–12 פיקסלים פריים־לפריים).

### 6.3.3 אינטראקציה עם Coast

חשוב מאוד: כאשר נכנסים ל־deadband, **מאפסים את coast state**. הסיבה:
אם המטרה עומדת במקום במרכז ואז נעלמת (היד שמחזיקה הזיזה אותה מחוץ
לפריים פתאומית), אסור ל־`tracker.update()` לעשות coast לאיזה כיוון
שהוא — אין כיוון בכלל. השמירה על המקום היא ההתנהגות הנכונה.

## 6.4 מכונת מצבים של `tracker.update()`

### 6.4.1 חמשת המצבים

```
┌─────────────┐         ┌─────────────┐
│   Tracking   │ ── target reaches deadband ──→ │    Locked    │
│  (active PID) │ ←── target leaves deadband ── │  (deadband)  │
└──────────────┘                                └──────────────┘
       │                                                │
       │ target lost                          target lost (was in deadband)
       │ (last correction meaningful)                   │
       ↓                                                ↓
┌──────────────┐                                ┌──────────────┐
│   Coasting   │                                │   Holding    │
│ (apply last  │                                │   (no info,  │
│ correction × │                                │   no change) │
│ decay)        │                                └──────────────┘
└──────┬───────┘
       │
       │ coast frames exhausted OR both axes clamped
       ↓
┌──────────────┐
│ Recentering  │
│ (return to    │
│  PAN_CENTER,  │
│  TILT_CENTER) │
└──────┬───────┘
       │
       │ reached center OR target re-acquired
       ↓
   Tracking / Locked
```

### 6.4.2 פסאודו־קוד מלא

```python
def update(pan_pid, tilt_pid, kit, target_pos):
    # state עולמי של המודול
    global _last_pan_correction, _last_tilt_correction
    global _coast_frames_remaining, _recentering

    # --- TARGET LOST BRANCH ---
    if target_pos is None:
        # 1. נסה Coast
        last_was_meaningful = (
            abs(_last_pan_correction) >= COAST_MIN_CORRECTION_DEG
            or abs(_last_tilt_correction) >= COAST_MIN_CORRECTION_DEG
        )
        if _coast_frames_remaining > 0 and last_was_meaningful:
            # Apply last correction + decay
            requested_pan = servo.current_pan() + _last_pan_correction
            requested_tilt = servo.current_tilt() + _last_tilt_correction
            actual_pan = servo.move_pan(kit, requested_pan, ramp=False)
            actual_tilt = servo.move_tilt(kit, requested_tilt, ramp=False)

            # אם שני הצירים מצומצמים בו זמנית — יציאה מ־coast מיידית
            pan_clamped  = abs(actual_pan - requested_pan) > 0.5
            tilt_clamped = abs(actual_tilt - requested_tilt) > 0.5
            if pan_clamped and tilt_clamped:
                _coast_frames_remaining = 0
            else:
                _last_pan_correction *= COAST_DECAY
                _last_tilt_correction *= COAST_DECAY
                _coast_frames_remaining -= 1
                return {"coasting": True, ...}

        # 2. נסה Recenter (אם Coast נכשל ו־ recenter מופעל)
        if RECENTER_AFTER_COAST and not _recentering:
            if last_was_meaningful and not already_centered():
                _recentering = True
            _reset_coast()

        if _recentering:
            # צעד אחד לכיוון מרכז
            pan_step = clamp(PAN_CENTER - current_pan, -STEP_DEG, STEP_DEG)
            tilt_step = clamp(TILT_CENTER - current_tilt, -STEP_DEG, STEP_DEG)
            servo.move_pan(kit, current_pan + pan_step, ramp=False)
            servo.move_tilt(kit, current_tilt + tilt_step, ramp=False)
            if reached_center:
                _recentering = False
            return {"recentering": True, ...}

        # 3. Holding — אין יותר מה לעשות
        return None

    # --- TARGET ACQUIRED BRANCH ---
    if _recentering:
        # המטרה חזרה באמצע recenter — חזרה לבקרה רגילה
        _recentering = False

    pan_error  = target_pos[0] - FRAME_CENTER_X
    tilt_error = target_pos[1] - FRAME_CENTER_Y
    pan_correction  = pan_pid(pan_error)
    tilt_correction = tilt_pid(tilt_error)

    if in_deadband(pan_error, tilt_error):
        _reset_coast()  # לא לעשות coast מהפסקת מטרה במצב סטטי
        return {"in_deadband": True, ...}

    # תיקון רגיל
    servo.move_pan(kit, servo.current_pan() + pan_correction, ramp=False)
    servo.move_tilt(kit, servo.current_tilt() + tilt_correction, ramp=False)

    # שמירת מצב לפריים הבא
    _last_pan_correction = pan_correction
    _last_tilt_correction = tilt_correction
    _coast_frames_remaining = COAST_MAX_FRAMES

    return {"pan_error": ..., "pan_correction": ..., "pan_angle": ..., ...}
```

### 6.4.3 חישוב Coast Decay

ה־decay לאחר $n$ פריימים:

$$c_n = c_0 \cdot (\text{COAST\_DECAY})^n$$

עם $\text{COAST\_DECAY} = 0.95$ ו־$n = 30$:

$$c_{30} = c_0 \cdot 0.95^{30} \approx c_0 \cdot 0.215$$

כלומר אחרי 30 פריימים התיקון יורד ל־~22% מהמקדם המקורי. **הברקט לא
נעצר חד** — הוא נעצר באופן הדרגתי. זה מאפשר שיא משוער של ~1 שנייה
של "אינרציה" שמדמה את התנהגות הראייה האנושית.

### 6.4.4 חישוב Recenter Time

עם $\text{RECENTER\_STEP\_DEG} = 2°$ ו־30fps:
- מהירות recenter: 60°/sec
- זמן לחזרה ממקסימום הסטייה (פאן): 170° / 60 = ~2.83s
- מקסימום סטייה (טילט): 90° / 60 = 1.5s

ב־real-world זה לרוב פחות (לא מגיעים לקצוות לעיתים קרובות).

## 6.5 מורכבות כוללת של לולאת המעקב

לסיכום, כל הפעולות ב־`tracker.update()`:

| פעולה | מורכבות |
|---|---|
| `camera.capture_frame()` | $O(1)$ syscall (תלוי בקצב המצלמה ולא ב־W×H) |
| `detector.detect()` | $O(W \cdot H)$ — דומיננטי |
| `tracker.update()` PID computation | $O(1)$ |
| `servo.move_pan/tilt` עם `ramp=False` | $O(1)$ syscall I²C |

**סך הכל לפר־פריים:** $O(W \cdot H)$ עם קבוע נמוך.

ב־$W = 640, H = 480$ — ~5–8ms פעולה רציפה. הפנאי שנותר בתוך 33ms של
פריים מאפשר לוגיקה עתידית (multi-target tracking, depth processing,
overlay rendering) ללא דאגה לקצב.

## 6.6 סיכום פרק

המתמטיקה של המערכת מתחלקת לארבעה חלקים: זיהוי מבוסס HSV ב־$O(W \cdot H)$,
בקרת PID ב־P-only עם output limits, פילטר deadband למניעת רעידות,
ומכונת מצבים ל־5 מצבים שונים של `tracker.update()` (Tracking, Locked,
Coasting, Recentering, Holding). כל אחד מהמרכיבים האלה מנוצל בהיגיון
מסוים — ולא רק "כי הוא קיים בספרייה". ההחלטות נומקו מנקודת המבט של
המאפיינים הספציפיים של המערכת שלנו: רעש detector של ~10 פיקסלים,
מהירות מטרה מוגבלת, גבולות סרוו פיזיים, ועוצמת CPU של Pi 4B.
