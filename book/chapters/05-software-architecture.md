# פרק 5 — ארכיטקטורת התוכנה ומבנה המודולים

לאחר שהוצג בפרק 4 הצד הפיזי של המערכת, פרק זה מתמקד בקוד שמפעיל את
החומרה הזו. שני העקרונות המרכזיים שמנחים את הארכיטקטורה הם **בעלות
בלעדית של מודול על תת־מערכת חומרה** (Single Responsibility) ו**ריכוז
כל הקבועים הניתנים לכיול במקום אחד** (Single Source of Truth). שני
העקרונות יחד מהווים את התשובה לדרישות "קוד הנדסת תוכנה" של המחוון
(שאליהן מצורף עונש של עד 30% במקרה של אי־עמידה).

## 5.1 רמת התוכנה — Top Level Diagram

```
                    ┌─────────────────────────────┐
   main.py / ────→ │  Orchestration Layer         │
   control_panel    │  (לולאה ראשית + GUI)         │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ↓                    ↓                    ↓
        ┌──────────┐         ┌──────────┐         ┌──────────┐
        │ camera.py │         │detector.py│         │tracker.py │
        └──────────┘         └──────────┘         └──────────┘
              │                    │                    │
              ↓                    ↓                    ↓
        cv2.VideoCapture     cv2 + numpy       simple_pid + servo.py
              │                    │                    │
                                   ↓
                              ┌──────────┐         ┌──────────┐
                              │ config.py│←────────│   ALL    │
                              └──────────┘         └──────────┘

        ┌──────────┐
        │ servo.py │ ←── adafruit_servokit / PCA9685 hardware
        └──────────┘

        ┌──────────┐
        │ laser.py │ ←── gpiozero / GPIO18 hardware
        └──────────┘
```

## 5.2 ארכיטקטורה Top-Down של התוכנה

### רמה 0 — האפליקציה
**מערכת מעקב לייזר אוטונומי (Python 3.11 על Raspberry Pi OS)**

### רמה 1 — שכבות (Layers)

| שכבה | אחריות | קבצים |
|---|---|---|
| **Orchestration** | בקרת זרימה ראשית, ממשק משתמש, מחזור חיים של המערכת | `main.py`, `control_panel.py`, `test_tracking.py` |
| **Logic** | אלגוריתמים, בקרת PID, זיהוי | `detector.py`, `tracker.py` |
| **Hardware Abstraction** | תרגום בין הלוגיקה לפעולות חומרה | `servo.py`, `camera.py`, `laser.py` |
| **Configuration** | מקור־אמת יחיד לקבועים מכוילים | `config.py` |

### רמה 2 — מודולים בעלי בעלות בלעדית

זוהי הליבה של עיצוב התוכנה. **כל מודול אחראי על תת־מערכת חומרה אחת
בלבד**, ו**אף מודול אחר אינו רשאי לייבא את ספריית הצד־השלישי השייכת
לאותה תת־מערכת**:

| מודול | תת־מערכת בבעלותו | ספרייה אסורה לאחרים |
|---|---|---|
| `servo.py` | ServoKit + I²C + PCA9685 | `adafruit_servokit`, `adafruit_pca9685` |
| `camera.py` | LifeCam דרך `cv2.VideoCapture` | (cv2 לעיבוד תמונה ב־detector.py — בסדר) |
| `detector.py` | אלגוריתם זיהוי HSV | — |
| `tracker.py` | בקרי PID | `simple_pid` |
| `laser.py` | GPIO18 + gpiozero לפין הלייזר | `gpiozero` (לפין זה ספציפית) |
| `config.py` | כל הקבועים המכוילים | — |
| `control_panel.py` | ממשק משתמש tkinter | — |

**מה זה אומר בפועל?** אם מודול `test_tracking.py` רוצה להזיז את הסרוו,
הוא **חייב** לקרוא ל־`servo.move_pan(kit, 150.0)` ולא לכתוב
`kit.servo[0].angle = 150.0` ישירות, גם אם זה נראה פשוט יותר. הסיבה:
ה־clamping לטווח הבטוח [50°, 220°] מתבצע בתוך `servo.py`. עקיפת המודול
תסכן את הסרוו.

### רמה 3 — פונקציות פנימיות

כל מודול חושף API ציבורי קטן ושומר את הפנימיות שלו פרטיות (תיעוד
`_underscore_prefix` קונבנציוני בפייתון). למשל ב־`servo.py`:

- API ציבורי: `init()`, `move_pan()`, `move_tilt()`, `center()`,
  `cleanup()`, `current_pan()`, `current_tilt()`.
- פנימי בלבד: `_configure_channel()`, `_ramp()`, וכן משתני מצב
  `_pan_current`, `_tilt_current` המעקבים אחר הזווית האחרונה שנשלחה.

## 5.3 עקרונות הנדסת תוכנה שיושמו

### 5.3.1 Single Responsibility (SRP)

כל מודול עושה דבר אחד — ועושה אותו טוב. `servo.py` לא יודע ולא צריך
לדעת על OpenCV; `detector.py` לא יודע על הסרוו. הם מתקשרים דרך טיפוסי
נתונים פשוטים (frame numpy array, tuple `(x, y)`, פלוט angle).

### 5.3.2 Single Source of Truth (SSOT)

`config.py` הוא המקור היחיד לקבועים מכוילים — HSV, מקדמי PID, גבולות
זווית, סף deadband, פרמטרי coast, וכו'. כל מודול אחר **מייבא** מכאן
ולא משכפל ערכים:

```python
# בתוך detector.py
mask = cv2.inRange(hsv, config.HSV_LOWER, config.HSV_UPPER)

# בתוך tracker.py
output_limits=(-config.PID_OUTPUT_LIMIT, config.PID_OUTPUT_LIMIT)
```

מה היתרון? אם רוצים לכוונן מחדש את HSV (אחרי שינוי בתאורה), מעדכנים
שורה אחת ב־`config.py` והכל "נופל למקום" — אין מקום נשכח אחר.

### 5.3.3 Layered Abstraction

מודולי החומרה (servo, camera, laser) מסתירים את כל מורכבות הספריות
הברמה נמוכה. שכבת הלוגיקה (detector, tracker) רואה רק פונקציות
מופשטות. שכבת ה־Orchestration (main, control_panel) רואה רק את שני
הצדדים.

זה מאפשר **החלפה אקוויולנטית של חומרה**: ביום שיוחלף ה־PCA9685
ב־דרייבר אחר, רק `servo.py` ייכתב מחדש; הקוד שמעליו לא ירגיש. בפועל
זה כבר קרה — כשהמצלמה הוחלפה מ־Pi CSI ל־USB, שיניתי רק את `camera.py`,
ו־`detector.py` לא ידע שמדובר במצלמה אחרת.

### 5.3.4 Defensive Programming / Fail-Safe

הקוד מבצע הגנות בכל נקודה שבה תקלה יכולה לפגוע בחומרה או במשתמש:

- **Clamping זוויות בכל פקודת סרוו** — לא ניתן לבקש זווית מחוץ לטווח
  הבטוח, גם אם בקר ה־PID יבקש בטעות.
- **Pulldown תכנותי במצב Idle של הלייזר** — `laser.init()` מצמיד
  GPIO18 ל־LOW במפורש, מעבר ל־Pulldown החיצוני של 100kΩ.
- **`try/finally` בכל סקריפט שמשתמש בחומרה** — מבטיח שלייזר ייסגר
  והסרוו יחזור למרכז גם אם הסקריפט נקטע ב־Ctrl+C.
- **שגיאות בתוך `cleanup()` נבלעות** — `cleanup()` נקרא בתוך
  `finally` בלוקים, ולכן אסור לו לזרוק חריגה שתסתיר את החריגה
  המקורית שהוביל למצב.

### 5.3.5 Type Hints

כל הפונקציות הציבוריות משתמשות ב־**Type Hints** של Python 3.11 כדי
לתעד את החתימה שלהן:

```python
def move_pan(kit: ServoKit, angle: float, ramp: bool = True) -> float:
    ...
```

זה מאפשר IDE לזהות שגיאות מסוג טיפוסים, ומתעד כוונה למפתח (מי שיקרא
את הפונקציה רואה מה היא מצפה לקבל ומה היא מחזירה).

### 5.3.6 Comments — WHY, Not WHAT

הקוד מתועד בכבדות, אבל ההנחיה היא שתגובות מסבירות **מדוע** קוד נראה
כפי שהוא נראה — לא **מה** הוא עושה. הקוד עצמו אמור להיות קריא־מעצמו.
למשל, ב־`tracker.py`:

```python
# ramp=False because the ramp's 50 ms/2° sleeps inside servo.py would
# block this loop for hundreds of milliseconds per correction. Without
# ramping, the PWM command changes instantly and the loop returns to
# capture the next frame immediately. The DS3225's own mechanical
# slew rate (~1°/12 ms) provides natural smoothing.
actual_pan = servo.move_pan(kit, new_pan, ramp=False)
```

התגובה לא אומרת "קריאה ל־move_pan עם ramp=False" — את זה הקוד
אומר. היא מסבירה **למה** ramp=False במקום True כברירת המחדל.

## 5.4 מבנה הספרייה (Project Layout)

```
pi/
├── main.py                  ⏸  פונקציית main של האפליקציה הסופית (Phase 8)
├── control_panel.py         ✅  ממשק משתמש tkinter
├── servo.py                 ✅  בעל בעלות על PCA9685 + DS3225
├── camera.py                ✅  בעל בעלות על LifeCam HD-3000
├── detector.py              ✅  אלגוריתם זיהוי HSV
├── tracker.py               ✅  בקרי PID + Coast + Recenter
├── laser.py                 ✅  בעל בעלות על GPIO18
├── config.py                ✅  מקור־אמת לכל הקבועים המכוילים
├── test_servo.py            ✅  בדיקת חוליית הסרוו
├── test_tracking.py         ✅  בדיקת לולאת הראייה מקצה לקצה (ללא לייזר)
├── test_laser.py            ✅  בדיקת רצף ירייה
├── calibrate_servo.py       ✅  כלי כיול אינטראקטיבי לגבולות
├── tune_detector.py         ✅  כיוון HSV עם trackbars חיים
├── boresight.py             ⏸  כיול היסט מצלמה–לייזר (Task 7B.4)
├── requirements.txt         ✅  תלויות pip
├── docs/                    ✅  כל התיעוד
└── scripts/install_desktop_shortcut.sh    ✅  התקנת קיצור־דרך לשולחן העבודה
```

✅ קיים ועובד; ⏸ עתיד / חסום.

## 5.5 פירוט פר־מודול (Class/Function Reference)

### 5.5.1 `config.py` — Single Source of Truth

**אין פונקציות.** רק קבועים. אסור לייבא משם דבר מלבד ערכים:

| קבוע | טיפוס | תפקיד |
|---|---|---|
| `FRAME_WIDTH` | int | רוחב התמונה (640) |
| `FRAME_HEIGHT` | int | גובה התמונה (480) |
| `FRAME_CENTER_X` | int | x של מרכז התמונה (320) |
| `FRAME_CENTER_Y` | int | y של מרכז התמונה (240) |
| `HSV_LOWER` | np.ndarray | סף תחתון לזיהוי [H, S, V] = [79, 76, 0] |
| `HSV_UPPER` | np.ndarray | סף עליון [H, S, V] = [105, 255, 255] |
| `MIN_CONTOUR_AREA` | int | סף שטח מינימלי לקבל קונטור כמטרה (200 פיקסלים) |
| `FIRE_PIXEL_THRESHOLD` | int | סף ירי — חייב להיות במרכז (15 px) |
| `KP_PAN`, `KP_TILT` | float | מקדמי P של PID (0.017 בשניהם) |
| `KI_*`, `KD_*` | float | אינטגרל/דריבטיב (0 לא נחוצים) |
| `PID_OUTPUT_LIMIT` | float | חסם תיקון לכל פריים (10°) |
| `TRACKING_DEADBAND_PX` | int | סף Deadband (15 px) |
| `COAST_MAX_FRAMES` | int | פריימים של Coast (30 = 1s ב־30fps) |
| `COAST_DECAY` | float | דעיכה לכל פריים Coast (0.95) |
| `COAST_MIN_CORRECTION_DEG` | float | סף הפעלת Coast (0.1°) |
| `RECENTER_AFTER_COAST` | bool | האם להפעיל Recenter |
| `RECENTER_STEP_DEG` | float | צעד תנועה ב־Recenter (2°) |
| `BORESIGHT_X_OFFSET` | int | היסט אופקי בין מצלמה ללייזר (עתידי) |
| `BORESIGHT_Y_OFFSET` | int | היסט אנכי בין מצלמה ללייזר (עתידי) |

### 5.5.2 `servo.py` — Owner של מערכת הסרוו

#### קבועים פנימיים

- `PAN_MIN = 50.0`, `PAN_MAX = 220.0` — גבולות מכוילים
- `TILT_MIN = 115.0`, `TILT_MAX = 205.0`
- `PAN_CENTER`, `TILT_CENTER` — מחושבים מהגבולות (לא קבוע קשיח)
- `PULSE_MIN_US = 500`, `PULSE_MAX_US = 2500` — פרופיל ה־DS3225
- `ACTUATION_RANGE_DEG = 270` — טווח התנועה הזוויתי המלא
- `RAMP_RESOLUTION_DEG = 2.0`, `RAMP_DELAY_S = 0.05` — פרמטרי תנועה חלקה

#### API ציבורי

```python
init() -> ServoKit
```
מאתחל את PCA9685, מגדיר את שני הערוצים, ומזיז את הסרוו למרכז. **הראשונה
תהיה Snap** (אין מידע על מיקום קודם).

```python
move_pan(kit, angle: float, ramp: bool = True) -> float
move_tilt(kit, angle: float, ramp: bool = True) -> float
```
מזיז סרוו לזווית, **מצומצם תמיד לטווח הבטוח**. החזרה: הזווית בפועל
לאחר ה־clamp. עם `ramp=True` מתקיים `_ramp()` עם תנועה חלקה ב־2°
כל 50ms; עם `ramp=False` הפקודה PWM נשלחת מיד (לולאת המעקב משתמשת
בזה).

```python
center(kit) -> None
cleanup(kit) -> None
```
החזרה למרכז. `cleanup` בולע חריגות שלו (קריאה מ־`finally`).

```python
current_pan() -> Optional[float]
current_tilt() -> Optional[float]
```
מחזיר את הזווית האחרונה שנשלחה. `None` אם `init()` עוד לא רץ.

#### מורכבות אלגוריתמית

- `move_pan/tilt`: $O(|\Delta\theta| / 2°)$ צעדים ב־RAMP מצב, $O(1)$ ב־
  un-ramped. במצב tracking (un-ramped) זמן קריאה <1ms.

### 5.5.3 `camera.py` — Owner של המצלמה

#### API ציבורי

```python
init(width: int = 640, height: int = 480, device_index: int = 0) -> cv2.VideoCapture
```
פותח את ה־webcam, מגדיר רזולוציה, מחזיר ה־`VideoCapture` object.
זורק `RuntimeError` במקרה של תקלה (מצלמה לא מחוברת או תפוסה).

```python
capture_frame(cap) -> np.ndarray
```
דוגם פריים BGR אחד מהמצלמה. **לא מבצע BGR→RGB** — OpenCV עובד עם
BGR ילידית.

```python
release(cap) -> None
```
שחרור משאבי המצלמה (לקרוא תמיד מתוך `finally`).

#### מורכבות

- כל הפעולות $O(1)$ מבחינת לולאה (יציאה אחת לקרנל).
- שיהוי דגימה תלוי בקצב הפריים של המצלמה (~33ms ב־30fps).

### 5.5.4 `detector.py` — אלגוריתם זיהוי HSV

#### API ציבורי

```python
detect(frame: np.ndarray) -> Optional[Tuple[int, int]]
```
מחזיר `(cx, cy)` של מרכז המסה של המטרה, או `None` אם לא נמצאה.

```python
build_mask(frame: np.ndarray) -> np.ndarray
```
מחזיר את המסכה הבינארית — חשוף בנפרד כדי ש־`tune_detector.py` יציג
אותה למשתמש.

#### צינור (Pipeline)

1. `cv2.GaussianBlur(frame, (5,5), 0)` — חלקת רעש (5×5 קרנל)
2. `cv2.cvtColor(... , COLOR_BGR2HSV)` — המרה ל־HSV
3. `cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)` — סף → מסכה בינארית
4. `cv2.erode(mask, ..., iterations=2)` — מחיקת רעש קטן
5. `cv2.dilate(mask, ..., iterations=2)` — שחזור גודל הבלוב
6. `cv2.findContours(mask, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)`
7. `max(contours, key=cv2.contourArea)` — הגדול ביותר
8. דחייה אם השטח קטן מ־`MIN_CONTOUR_AREA`
9. `cv2.moments(largest)` → `(cx, cy) = (m10/m00, m01/m00)`

#### מורכבות

הצינור הוא **לינארי בגודל הפריים** — $O(W \cdot H)$ עבור כל שלב
(blur, cvtColor, inRange, erode, dilate). `findContours` ו־`moments`
לינאריים בסכום הפיקסלים של ה־mask, שזה גם $O(W \cdot H)$. לכן
מורכבות כוללת:

$$T_{detect}(W, H) = O(W \cdot H)$$

עם $W=640, H=480$ זה ~307K פיקסלים. בקצב 30 fps זה ~9.2M פיקסלים
לשנייה. ה־Pi 4B מטפל בקלות (Cortex-A72 ב־1.5GHz, 4 ליבות).

### 5.5.5 `tracker.py` — בקרי PID + Coast + Recenter

#### API ציבורי

```python
init() -> Tuple[PID, PID]
```
יוצר שתי מופעי `simple_pid.PID` (אחד לכל ציר), עם `setpoint=0`
ו־`output_limits=(-PID_OUTPUT_LIMIT, PID_OUTPUT_LIMIT)`.

```python
update(pan_pid, tilt_pid, kit, target_pos: Optional[Tuple[int, int]]) -> Optional[Dict]
```
אטר אחד בלולאה. מקבל את הפלט של `detector.detect()`.

החזרה: dict עם `pan_error`, `tilt_error`, `pan_correction`,
`tilt_correction`, `pan_angle`, `tilt_angle`, `in_deadband`,
`coasting`, `recentering`. במקרה של אין־פעולה — `None`.

```python
stop(kit) -> None
```
פונקציית כיבוי (מאצילה ל־`servo.cleanup`).

#### לוגיקת `update()` — מכונת מצבים

```
target_pos = None?
│
├── YES → coast_remaining > 0 AND last correction meaningful?
│        ├── YES → coast frame (apply last correction × decay)
│        │        בדיקה: clamped on both axes? → cancel coast → recenter
│        └── NO → recenter enabled AND need to?
│                ├── YES → recenter step (2°/frame toward center)
│                └── NO → hold position (return None)
│
└── NO → error within deadband?
         ├── YES → hold position, reset coast state
         └── NO → PID update → servo.move_pan/tilt → save coast state
```

#### מצב פנימי (Module-Level State)

- `_last_pan_correction`, `_last_tilt_correction`: float — תיקוני
  PID האחרונים, נחוצים ל־Coast
- `_coast_frames_remaining`: int — מונה Coast
- `_recentering`: bool — האם בתהליך חזרה למרכז

#### מורכבות

`update()` הוא $O(1)$ — בקר ה־PID של `simple_pid` מבצע 3 חישובי
מספרים (P, I, D ולפי setpoint וה־input). כל החישוב מסתיים ב־
מיקרושניות.

### 5.5.6 `laser.py` — Owner של GPIO18

#### API ציבורי

```python
init() -> gpiozero.LED
```
מגדיר GPIO18 כיציאה, מצמיד ל־LOW (כלומר לייזר OFF), מחזיר את
הoutput object.

```python
fire(laser_dev) -> None
off(laser_dev) -> None
cleanup(laser_dev) -> None
```
שלוש פונקציות לוגיות עצמאיות. `cleanup` בולע חריגות.

#### חוזה בטיחות

- הלייזר OFF כאשר המודול אותחל;
- הלייזר OFF כאשר המודול נסגר;
- שם המשתנה המחזיק את ה־`laser_dev` חייב להיות `laser_dev` ולא
  `laser` (אחרת שמשתנה־שמודול־מקבילים מתנגשים, ראה `CLAUDE.md`).

#### מורכבות

`fire()` ו־`off()` — $O(1)$, יציאת syscall אחת לקרנל למיתוג ה־GPIO.

### 5.5.7 `control_panel.py` — Operator GUI

#### מבנה

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

המחלקה משתמשת ב־`threading.Thread` להרצת רענון הסטטוס ב־5Hz מבלי
לחסום את ה־GUI, ב־`subprocess.Popen` להפעלת `test_tracking.py` או
`tune_detector.py` בתהליכים חיצוניים (כדי לא לחסום את ה־GUI ולא לתפוס
את ה־PCA9685 בו־זמנית).

יש לוג־פיין שמרכז את כל פלט ה־`logging` של המערכת לחלון אחד באמצעות
`QueueHandler` של Python.

#### מורכבות

GUI Event-Driven, אין מורכבות לולאתית. כל handler $O(1)$.

### 5.5.8 `main.py` — נקודת הכניסה הסופית (Phase 8)

מבנה מתוכנן (placeholder כיום):

```python
def main():
    servo.init() → kit
    camera.init() → cam
    tracker.init() → (pan_pid, tilt_pid)
    laser.init() → laser_dev

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

חוזה הירייה: רק אם המטרה במצב `in_deadband` (כלומר סטיית פיקסלים < 15
בשני הצירים) — אחרת הירייה תיפול בצד.

## 5.6 ניהול תלויות (Dependencies)

### תלויות ניהול (pip — `requirements.txt`)

```
adafruit-circuitpython-pca9685
adafruit-circuitpython-servokit
adafruit-blinka
simple-pid
```

ארבעת אלה הם הספריות **שלא נמצאות באפסטרים של Bookworm** — חייבות
להותקן בתוך הסביבה הוירטואלית.

### תלויות מערכת (apt — מותקנות מעבר ל־venv)

```
python3-opencv      → cv2
python3-numpy       → numpy
python3-gpiozero    → gpiozero
```

הסביבה הוירטואלית נוצרה עם הדגל `--system-site-packages` כדי לראות
את אלה. החיסכון: לא לחזור על קומפילציית OpenCV בתוך כל venv (זה לוקח
שעות על Pi).

### גרף תלויות בתוך הקוד

```
main / control_panel  →  servo, camera, detector, tracker, laser, config
tracker               →  servo, config (+ simple_pid)
detector              →  config (+ cv2, numpy)
camera                →  (cv2)
servo                 →  (adafruit_servokit)
laser                 →  (gpiozero)
config                →  (numpy)
```

אין מעגלים (כדאי) — `config.py` הוא העלים של העץ.

## 5.7 ניהול שגיאות וביצועי בטיחות

### מקור החריגות הנפוץ

| חריגה | סיבה | תגובה |
|---|---|---|
| `OSError: [Errno 121] Remote I/O error` | I²C לא מגיב — כבל לא מחובר או PCA9685 ללא חשמל | מסתורי לוגי, יציאה נקייה (`servo.cleanup`) |
| `RuntimeError: Cannot open camera` | USB לא מחובר / מצלמה תפוסה | יציאה נקייה |
| `RuntimeError: servo.init() must be called before move_pan()` | שגיאת קוד פנימית — כיוון של הזמנה | יציאה |
| `KeyboardInterrupt` | Ctrl+C על־ידי המשתמש | `finally` block מבצע cleanup |

### דפוס Try / Finally

כל סקריפט שמשתמש בחומרה עוטף את הלוגיקה ב־`try/finally`:

```python
def main():
    kit = servo.init()
    cam = camera.init()
    laser_dev = laser.init()
    try:
        # ... לולאה ראשית ...
    finally:
        laser.cleanup(laser_dev)   # תמיד יבוצע
        camera.release(cam)
        servo.cleanup(kit)
```

זה מבטיח שגם אם החלק "לולאה ראשית" ייכשל בכל שלב — הלייזר ייסגר,
הסרוו יחזור למרכז, ומשאבי המצלמה ישוחררו.

## 5.8 דפוסי עיצוב משמשים

- **Owner Module** — כל מודול בעלים בלעדי על משאב חומרה. דומה ל־
  Façade + Single Responsibility.
- **Singleton State** (ב־`servo.py`, `tracker.py`) — מצב מודולרי
  לפי המודול עצמו ולא לפי instance, כי הסרוו פיזית אחד והבקר אחד.
- **Strategy** (גמיש) — `tracker.update()` בוחר בין PID/Coast/
  Recenter/Hold לפי המצב הנוכחי. מימוש קל ל־refactor אם תצורות
  בקרה חדשות יתווספו.
- **Resource Management** (`try/finally`) — מבטיח שחרור משאבים
  מובטח.

## 5.9 סיכום פרק

הקוד מאורגן לפי שתי דרישות־עיקריות: כל מודול אחראי על תת־מערכת אחת,
וכל קבועי הכיול חיים במקום אחד. המודולים מתפצלים לארבע שכבות (קונפיג,
אבסטרקציית חומרה, לוגיקה, אורקסטרציה), עם תלויות מנותבות מלמטה
למעלה ללא מעגלים. כל פונקציה ציבורית מתועדת ב־Type Hint, כל בלוק
לא־טריוויאלי מקבל תגובה שמסבירה "למה" ולא "מה", וכל סקריפט שעובד
עם חומרה עטוף ב־`try/finally` להבטחת שחרור משאבים. שלושת המנגנונים
המתקדמים של `tracker.py` — PID, Coast, ו־Recenter — מודגמים בפרק 6
בפירוט מתמטי. את הצינור הזה ה־GUI ב־`control_panel.py` עוטף עבור
משתמש שלא צריך להריץ פקודות שורה ידנית.
