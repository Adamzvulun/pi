# פרק 5 — ארכיטקטורת התוכנה ומבנה המודולים

לאחר שפרק 4 הציג את הצד הפיזי, הפרק הזה מתמקד בקוד שמפעיל את
החומרה. שני העקרונות המרכזיים: **בעלות בלעדית של מודול על תת־מערכת
חומרה** (Single Responsibility) ו**ריכוז כל הקבועים הניתנים לכיול
במקום אחד** (Single Source of Truth). שני העקרונות מהווים את
התשובה לדרישות "קוד הנדסת תוכנה" של המחוון (עד 30% עונש על אי־עמידה).

## 5.1 רמת התוכנה — Top Level

תרשים יחסים בין המודולים:

![תרשים תוכנה Top-Down](software-topdown.png)

## 5.2 ארכיטקטורה Top-Down

### רמה 0 — האפליקציה

מערכת מעקב לייזר אוטונומי (Python 3.11 על Raspberry Pi OS).

### רמה 1 — שכבות

| שכבה | אחריות | קבצים |
|---|---|---|
| **Orchestration** | בקרת זרימה ראשית, ממשק משתמש, מחזור חיים | `main.py`, `control_panel.py`, `test_tracking.py` |
| **Logic** | אלגוריתמים, בקרת PID, זיהוי | `detector.py`, `tracker.py` |
| **Hardware Abstraction** | תרגום בין לוגיקה לפעולות חומרה | `servo.py`, `camera.py`, `laser.py` |
| **Configuration** | מקור־אמת לקבועים מכוילים | `config.py` |

### רמה 2 — מודולי בעלות בלעדית

ליבת עיצוב התוכנה. כל מודול אחראי על תת־מערכת חומרה אחת, ואף
מודול אחר אינו רשאי לייבא את ספריית הצד־השלישי השייכת לאותה
תת־מערכת:

| מודול | תת־מערכת | ספרייה אסורה לאחרים |
|---|---|---|
| `servo.py` | ServoKit + I²C + PCA9685 | `adafruit_servokit`, `adafruit_pca9685` |
| `camera.py` | LifeCam דרך `cv2.VideoCapture` | (cv2 לעיבוד תמונה ב־detector.py — בסדר) |
| `detector.py` | אלגוריתם זיהוי HSV | — |
| `tracker.py` | בקרי PID | `simple_pid` |
| `laser.py` | GPIO18 + gpiozero | `gpiozero` (לפין הזה) |
| `config.py` | כל הקבועים המכוילים | — |
| `control_panel.py` | ממשק משתמש tkinter | — |

בפועל: אם `test_tracking.py` רוצה להזיז סרוו, הוא חייב לקרוא ל־
`servo.move_pan(kit, 150.0)` ולא לכתוב `kit.servo[0].angle = 150.0`
ישירות, גם כשזה פשוט יותר. הסיבה — ה־clamping לטווח [50°, 220°]
מתבצע בתוך `servo.py`. עקיפת המודול מסכנת את הסרוו.

### רמה 3 — פונקציות פנימיות

כל מודול חושף API ציבורי קטן ושומר את הפנימיות פרטיות (קונבנציית
`_underscore_prefix` של Python). למשל ב־`servo.py`:

- API ציבורי: `init()`, `move_pan()`, `move_tilt()`, `center()`,
  `cleanup()`, `current_pan()`, `current_tilt()`.
- פנימי: `_configure_channel()`, `_ramp()`, ומשתני מצב
  `_pan_current`, `_tilt_current` שעוקבים אחר הזווית האחרונה
  ששלחה התוכנה.

## 5.3 עקרונות הנדסת תוכנה

### 5.3.1 Single Responsibility (SRP)

כל מודול עושה דבר אחד. `servo.py` לא יודע על OpenCV; `detector.py`
לא יודע על הסרוו. הם מתקשרים דרך טיפוסי נתונים פשוטים — frame
numpy array, tuple `(x, y)`, ערך angle.

### 5.3.2 Single Source of Truth (SSOT)

`config.py` הוא המקור היחיד לקבועים מכוילים — HSV, מקדמי PID,
גבולות זווית, סף deadband, פרמטרי coast. כל מודול אחר מייבא ולא
משכפל ערכים:

::: {dir=ltr}
```python
# detector.py
mask = cv2.inRange(hsv, config.HSV_LOWER, config.HSV_UPPER)

# tracker.py
output_limits=(-config.PID_OUTPUT_LIMIT, config.PID_OUTPUT_LIMIT)
```
:::

כיוון HSV מחדש (לאחר שינוי תאורה) הוא שינוי של שורה אחת ב־`config.py`,
והכל "נופל למקום" — אין מקום נשכח.

### 5.3.3 Layered Abstraction

מודולי החומרה (servo, camera, laser) מסתירים את מורכבות הספריות
ברמה הנמוכה. שכבת הלוגיקה (detector, tracker) רואה רק פונקציות
מופשטות. שכבת ה־Orchestration (main, control_panel) רואה רק את
שני הצדדים.

זה מאפשר **החלפה אקוויולנטית של חומרה**: אם יוחלף PCA9685 בדרייבר
אחר, רק `servo.py` ייכתב מחדש; הקוד שמעליו לא ירגיש. זה כבר קרה —
כשהוחלפה המצלמה מ־CSI ל־USB, רק `camera.py` השתנה, ו־`detector.py`
לא ידע על השינוי.

### 5.3.4 Defensive Programming / Fail-Safe

הקוד מבצע הגנות בכל נקודה שבה תקלה עלולה לפגוע בחומרה או במשתמש:

- **Clamping בכל פקודת סרוו** — לא ניתן לבקש זווית מחוץ לטווח הבטוח,
  גם אם PID יבקש בטעות.
- **Pulldown תכנותי במצב Idle של הלייזר** — `laser.init()` מצמיד
  GPIO18 ל־LOW במפורש, מעבר ל־Pulldown החיצוני 100kΩ.
- **`try/finally` בכל סקריפט שמשתמש בחומרה** — לייזר נסגר וסרוו
  חוזר למרכז גם אם הסקריפט נקטע ב־Ctrl+C.
- **שגיאות בתוך `cleanup()` נבלעות** — `cleanup` נקרא בתוך
  `finally`, ולכן אסור לו לזרוק חריגה שתסתיר את החריגה המקורית.

### 5.3.5 Type Hints

כל הפונקציות הציבוריות משתמשות ב־type hints של Python 3.11:

::: {dir=ltr}
```python
def move_pan(kit: ServoKit, angle: float, ramp: bool = True) -> float:
    ...
```
:::

זה מאפשר IDE לזהות שגיאות טיפוסים ומתעד כוונה.

### 5.3.6 Comments — WHY, Not WHAT

הקוד מתועד בכבדות, אבל ההנחיה — תגובות מסבירות **מדוע** הקוד נראה
כפי שהוא, לא **מה** הוא עושה. הקוד עצמו אמור להיות קריא־מעצמו.
דוגמה מתוך `tracker.py`:

::: {dir=ltr}
```python
# ramp=False because the ramp's 50 ms/2° sleeps inside servo.py would
# block this loop for hundreds of milliseconds per correction. Without
# ramping, the PWM command changes instantly and the loop returns to
# capture the next frame immediately. The DS3225's own mechanical
# slew rate (~1°/12 ms) provides natural smoothing.
actual_pan = servo.move_pan(kit, new_pan, ramp=False)
```
:::

התגובה לא אומרת "קריאה ל־move_pan עם ramp=False" — את זה הקוד אומר.
היא מסבירה למה ramp=False במקום ברירת המחדל True.

## 5.4 מבנה הספרייה

::: {dir=ltr}
```
pi/
├── main.py                  ✅  פונקציית main של האפליקציה הסופית
├── control_panel.py         ✅  ממשק משתמש tkinter
├── servo.py                 ✅  Owner על PCA9685 + DS3225
├── camera.py                ✅  Owner על LifeCam HD-3000
├── detector.py              ✅  אלגוריתם זיהוי HSV
├── tracker.py               ✅  בקרי PID + Coast + Recenter
├── laser.py                 ✅  Owner על GPIO18
├── config.py                ✅  מקור־אמת לכל הקבועים המכוילים
├── test_servo.py            ✅  בדיקת חוליית הסרוו
├── test_tracking.py         ✅  בדיקת לולאת הראייה מקצה לקצה
├── test_laser.py            ✅  בדיקת רצף ירייה
├── calibrate_servo.py       ✅  כלי כיול אינטראקטיבי לגבולות
├── tune_detector.py         ✅  כיוון HSV עם trackbars חיים
├── boresight.py             ✅  כיול היסט מצלמה–לייזר
├── requirements.txt         ✅  תלויות pip
├── docs/                    ✅  כל התיעוד
└── scripts/install_desktop_shortcut.sh    ✅  התקנת קיצור־דרך
```
:::

## 5.5 פירוט פר־מודול

### 5.5.1 `config.py` — Single Source of Truth

אין פונקציות, רק קבועים:

| קבוע | טיפוס | תפקיד |
|---|---|---|
| `FRAME_WIDTH` | int | רוחב הפריים (640) |
| `FRAME_HEIGHT` | int | גובה הפריים (480) |
| `FRAME_CENTER_X` | int | x של מרכז הפריים (320) |
| `FRAME_CENTER_Y` | int | y של מרכז הפריים (240) |
| `HSV_LOWER` | np.ndarray | סף תחתון [79, 76, 0] |
| `HSV_UPPER` | np.ndarray | סף עליון [105, 255, 255] |
| `MIN_CONTOUR_AREA` | int | סף שטח מינימלי (200 פיקסלים) |
| `FIRE_PIXEL_THRESHOLD` | int | סף ירייה (15 px) |
| `KP_PAN`, `KP_TILT` | float | מקדמי P (0.017) |
| `KI_*`, `KD_*` | float | אינטגרל/דריבטיב (0) |
| `PID_OUTPUT_LIMIT` | float | חסם תיקון לכל פריים (10°) |
| `TRACKING_DEADBAND_PX` | int | סף Deadband (15 px) |
| `COAST_MAX_FRAMES` | int | פריימי Coast (30) |
| `COAST_DECAY` | float | דעיכה לפריים (0.95) |
| `COAST_MIN_CORRECTION_DEG` | float | סף הפעלת Coast (0.1°) |
| `RECENTER_AFTER_COAST` | bool | האם להפעיל Recenter |
| `RECENTER_STEP_DEG` | float | צעד Recenter (2°) |
| `BORESIGHT_X_OFFSET` | int | היסט אופקי מצלמה ↔ לייזר |
| `BORESIGHT_Y_OFFSET` | int | היסט אנכי מצלמה ↔ לייזר |

### 5.5.2 `servo.py`

#### קבועים פנימיים

- `PAN_MIN = 50.0`, `PAN_MAX = 220.0` — גבולות מכוילים
- `TILT_MIN = 115.0`, `TILT_MAX = 205.0`
- `PAN_CENTER`, `TILT_CENTER` — מחושבים מהגבולות
- `PULSE_MIN_US = 500`, `PULSE_MAX_US = 2500` — פרופיל DS3225
- `ACTUATION_RANGE_DEG = 270` — טווח מלא
- `RAMP_RESOLUTION_DEG = 2.0`, `RAMP_DELAY_S = 0.05` — תנועה חלקה

#### API ציבורי

::: {dir=ltr}
```python
init() -> ServoKit
```
:::

מאתחל את PCA9685, מגדיר את שני הערוצים, ומזיז את הסרוו למרכז.
הראשונה תהיה Snap (אין מידע על מיקום קודם).

::: {dir=ltr}
```python
move_pan(kit, angle: float, ramp: bool = True) -> float
move_tilt(kit, angle: float, ramp: bool = True) -> float
```
:::

מזיז סרוו לזווית, מצומצם תמיד לטווח הבטוח. החזרה: הזווית בפועל
לאחר ה־clamp. עם `ramp=True` תנועה חלקה ב־2° כל 50ms; עם `ramp=False`
PWM נשלח מיד (הלולאה משתמשת בזה).

::: {dir=ltr}
```python
center(kit) -> None
cleanup(kit) -> None
```
:::

חזרה למרכז. `cleanup` בולע חריגות (קריאה מתוך `finally`).

::: {dir=ltr}
```python
current_pan() -> Optional[float]
current_tilt() -> Optional[float]
```
:::

מחזיר את הזווית האחרונה ששלחה התוכנה. `None` אם `init()` עוד לא רץ.

#### מורכבות

- `move_pan/tilt`: $O(|\Delta\theta| / 2°)$ צעדים ב־ramp, $O(1)$ ב־
  un-ramped. במצב tracking (un-ramped) זמן קריאה <1ms.

### 5.5.3 `camera.py`

#### API ציבורי

::: {dir=ltr}
```python
init(width: int = 640, height: int = 480, device_index: int = 0) -> cv2.VideoCapture
```
:::

פותח את ה־webcam, מגדיר רזולוציה, מחזיר `VideoCapture`. זורק
`RuntimeError` במקרה של תקלה.

::: {dir=ltr}
```python
capture_frame(cap) -> np.ndarray
```
:::

דוגם פריים BGR אחד. לא מבצע BGR→RGB — OpenCV עובד עם BGR ילידית.

::: {dir=ltr}
```python
release(cap) -> None
```
:::

שחרור משאבי המצלמה (נקרא מתוך `finally`).

#### מורכבות

- כל הפעולות $O(1)$ מבחינת לולאה (syscall אחד לקרנל).
- שיהוי דגימה תלוי בקצב המצלמה (~33ms ב־30fps).

### 5.5.4 `detector.py`

#### API ציבורי

::: {dir=ltr}
```python
detect(frame: np.ndarray) -> Optional[Tuple[int, int]]
```
:::

מחזיר `(cx, cy)` של מרכז המסה, או `None` אם לא נמצאה מטרה.

::: {dir=ltr}
```python
build_mask(frame: np.ndarray) -> np.ndarray
```
:::

מחזיר את המסכה הבינארית — חשוף בנפרד כדי ש־`tune_detector.py` יציג
אותה למשתמש.

#### צינור

1. `cv2.GaussianBlur(frame, (5,5), 0)` — חלקת רעש
2. `cv2.cvtColor(... , COLOR_BGR2HSV)` — המרה ל־HSV
3. `cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)` — מסכה בינארית
4. `cv2.erode(mask, ..., iterations=2)` — מחיקת רעש
5. `cv2.dilate(mask, ..., iterations=2)` — שחזור הגודל
6. `cv2.findContours(mask, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)`
7. `max(contours, key=cv2.contourArea)` — הגדול ביותר
8. דחייה אם השטח קטן מ־`MIN_CONTOUR_AREA`
9. `cv2.moments(largest)` → `(cx, cy) = (m10/m00, m01/m00)`

#### מורכבות

הצינור לינארי בגודל הפריים — $O(W \cdot H)$ עבור כל שלב.
`findContours` ו־`moments` לינאריים בסכום הפיקסלים של ה־mask —
גם $O(W \cdot H)$. סך הכל:

$$T_{detect}(W, H) = O(W \cdot H)$$

ב־$W=640, H=480$ — ~307K פיקסלים. בקצב 30 fps זה ~9.2M פיקסלים
לשנייה. Pi 4B מטפל בקלות.

### 5.5.5 `tracker.py`

#### API ציבורי

::: {dir=ltr}
```python
init() -> Tuple[PID, PID]
```
:::

יוצר שתי מופעי `simple_pid.PID` (אחד לכל ציר), עם `setpoint=0`
ו־`output_limits=(-PID_OUTPUT_LIMIT, PID_OUTPUT_LIMIT)`.

::: {dir=ltr}
```python
update(pan_pid, tilt_pid, kit, target_pos: Optional[Tuple[int, int]]) -> Optional[Dict]
```
:::

איטרציה אחת בלולאה. מקבל את הפלט של `detector.detect()`.

החזרה: dict עם `pan_error`, `tilt_error`, `pan_correction`,
`tilt_correction`, `pan_angle`, `tilt_angle`, `in_deadband`,
`coasting`, `recentering`. ב־no-op מחזיר `None`.

::: {dir=ltr}
```python
stop(kit) -> None
```
:::

פונקציית כיבוי (מאצילה ל־`servo.cleanup`).

#### לוגיקת `update()` — מכונת מצבים

::: {dir=ltr}
```
target_pos = None?
│
├── YES → coast_remaining > 0 AND last correction meaningful?
│        ├── YES → coast frame (apply last correction × decay)
│        │        clamped on both axes? → cancel coast → recenter
│        └── NO → recenter enabled AND need to?
│                ├── YES → recenter step (2°/frame toward center)
│                └── NO → hold position (return None)
│
└── NO → error within deadband?
         ├── YES → hold position, reset coast state
         └── NO → PID update → servo.move_pan/tilt → save coast state
```
:::

#### מצב פנימי

- `_last_pan_correction`, `_last_tilt_correction`: float — תיקוני
  PID האחרונים, ל־Coast.
- `_coast_frames_remaining`: int — מונה Coast.
- `_recentering`: bool — האם בתהליך חזרה למרכז.

#### מורכבות

`update()` הוא $O(1)$ — `simple_pid` מבצע 3 חישובים מספריים. כל
החישוב מסתיים במיקרושניות.

### 5.5.6 `laser.py`

#### API ציבורי

::: {dir=ltr}
```python
init() -> gpiozero.LED
```
:::

מגדיר GPIO18 כיציאה, מצמיד ל־LOW (לייזר OFF), מחזיר את ה־output
object.

::: {dir=ltr}
```python
fire(laser_dev) -> None
off(laser_dev) -> None
cleanup(laser_dev) -> None
```
:::

שלוש פונקציות עצמאיות. `cleanup` בולע חריגות.

#### חוזה בטיחות

- הלייזר OFF כאשר המודול אותחל.
- הלייזר OFF כאשר המודול נסגר.
- שם המשתנה חייב להיות `laser_dev` ולא `laser` (אחרת
  משתנה־שמודול־מקבילים מתנגשים — ראו `CLAUDE.md`).

#### מורכבות

`fire()` ו־`off()` — $O(1)$, syscall אחד לקרנל למיתוג ה־GPIO.

### 5.5.7 `control_panel.py`

#### מבנה

::: {dir=ltr}
```python
class ControlPanel(tk.Tk):
    def __init__(self): ...
    def init_hardware(self): ...    # lazy init של ServoKit + LED
    def center_servos(self): ...
    def move_to_sliders(self): ...
    def fire_laser_one_sec(self): ...
    def emergency_stop(self): ...
    def start_tracking_test(self): ...
    def tune_hsv(self): ...
    def reload_config(self): ...
    def shutdown_pi(self): ...
    def on_close(self): ...           # cleanup קומפליט
```
:::

המחלקה משתמשת ב־`threading.Thread` לרענון סטטוס ב־5Hz בלי לחסום את
ה־GUI, וב־`subprocess.Popen` להפעלת `test_tracking.py` או
`tune_detector.py` בתהליכים חיצוניים (כדי לא לחסום את ה־GUI ולא לתפוס
את PCA9685 בו־זמנית).

לוג־פיין מרכז את כל פלט ה־`logging` של המערכת לחלון אחד באמצעות
`QueueHandler` של Python.

#### מורכבות

GUI Event-Driven, ללא לולאה מתמשכת. כל handler $O(1)$.

### 5.5.8 `main.py`

נקודת הכניסה לאינטגרציה הסופית:

::: {dir=ltr}
```python
def main():
    kit = servo.init()
    cam = camera.init()
    pan_pid, tilt_pid = tracker.init()
    laser_dev = laser.init()

    try:
        while True:
            frame = camera.capture_frame(cam)
            target = detector.detect(frame)
            result = tracker.update(pan_pid, tilt_pid, kit, target)

            if 'f' pressed and result and result['in_deadband']:
                laser.fire(laser_dev)
                time.sleep(0.5)
                laser.off(laser_dev)

            if 'q' pressed: break
    finally:
        laser.cleanup(laser_dev)
        servo.cleanup(kit)
        camera.release(cam)
```
:::

חוזה הירייה: הירייה מתבצעת רק כאשר `in_deadband` (סטיית פיקסלים <
15 בשני הצירים) — אחרת היא תיפול לצד.

## 5.6 ניהול תלויות

### תלויות pip (`requirements.txt`)

::: {dir=ltr}
```
adafruit-circuitpython-pca9685
adafruit-circuitpython-servokit
adafruit-blinka
simple-pid
```
:::

ארבעת אלה לא נמצאים באפסטרים של Bookworm — חייבים להותקן ב־venv.

### תלויות מערכת (apt, מותקנות מעבר ל־venv)

::: {dir=ltr}
```
python3-opencv      → cv2
python3-numpy       → numpy
python3-gpiozero    → gpiozero
```
:::

ה־venv נוצר עם הדגל `--system-site-packages` כדי לראות אותן.
החיסכון — לא חוזרים על קומפילציית OpenCV בתוך כל venv (זה לוקח שעות
על Pi).

### גרף תלויות בקוד

::: {dir=ltr}
```
main / control_panel  →  servo, camera, detector, tracker, laser, config
tracker               →  servo, config (+ simple_pid)
detector              →  config (+ cv2, numpy)
camera                →  (cv2)
servo                 →  (adafruit_servokit)
laser                 →  (gpiozero)
config                →  (numpy)
```
:::

אין מעגלים. `config.py` הוא העלים של העץ.

## 5.7 ניהול שגיאות

### מקור חריגות נפוץ

| חריגה | סיבה | תגובה |
|---|---|---|
| `OSError: [Errno 121] Remote I/O error` | I²C לא מגיב | logging, יציאה נקייה (`servo.cleanup`) |
| `RuntimeError: Cannot open camera` | USB לא מחובר / תפוסה | יציאה נקייה |
| `RuntimeError: servo.init() must be called before move_pan()` | שגיאת קוד פנימית | יציאה |
| `KeyboardInterrupt` | Ctrl+C | `finally` block מבצע cleanup |

### דפוס Try / Finally

כל סקריפט שמשתמש בחומרה עוטף את הלוגיקה ב־`try/finally`:

::: {dir=ltr}
```python
def main():
    kit = servo.init()
    cam = camera.init()
    laser_dev = laser.init()
    try:
        # ... לולאה ראשית ...
    finally:
        laser.cleanup(laser_dev)
        camera.release(cam)
        servo.cleanup(kit)
```
:::

גם אם החלק "לולאה ראשית" ייכשל באמצע — הלייזר ייסגר, הסרוו יחזור
למרכז, ומשאבי המצלמה ישוחררו.

## 5.8 דפוסי עיצוב

- **Owner Module** — כל מודול בעלים בלעדי על משאב חומרה. דומה
  ל־Façade + SRP.
- **Singleton State** (ב־`servo.py`, `tracker.py`) — מצב לפי מודול
  ולא לפי instance, כי הסרוו פיזית אחד והבקר אחד.
- **Strategy** — `tracker.update()` בוחר בין PID/Coast/Recenter/Hold
  לפי המצב.
- **Resource Management** (`try/finally`) — שחרור מובטח.
