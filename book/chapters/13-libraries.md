# 13. הסבר ספריות

המחוון דורש: "סקירה מפורטת על כל ספריה (אילו שנכתבו על ידי הסטודנט,
ואלו שנלקחו כ־BB), הפונקציות העיקריות, ייעוד מרכזי, תקלות נפוצות
(אם ידוע) וכו'". הפרק מחולק לפי המקור: **ספריות שנכתבו על־ידי
הסטודנט** (§13.2) ו**ספריות צד־שלישי (BB — Building Blocks)** (§13.3).

---

## 13.1 ההבחנה — Self-Written vs BB

| מקור | משמעות | דוגמה |
|---|---|---|
| **Self-Written** | קוד שנכתב ע"י הסטודנט במהלך הפרויקט; קיים במאגר; שינוי מותאם פתוח | `servo.py`, `detector.py`, `tracker.py` |
| **BB (Building Block)** | ספרייה חיצונית בקוד פתוח שיובאה כתלות; הוטמעה ב־`requirements.txt` או הותקנה כ־apt; השימוש דרך ה־API הציבורי בלבד | `cv2`, `simple-pid`, `gpiozero` |

ההבחנה חשובה לבחינה — המחוון מתעקש על הזדהות ברורה של מה שאינו
מקורי, כדי למנוע מצג שווא של "כל הקוד שלי" כאשר חלק נשען על תשתית
שמישהו אחר בנה.

---

## 13.2 ספריות שנכתבו על־ידי הסטודנט

המודולים האלה הם **לב הפרויקט**. נכתבו במלואם במסגרת העבודה.
מספר השורות, סוג הקובץ, וההצדקה לקיומו מצוינים לכל אחד.

### 13.2.1 `config.py`

| תכונה | ערך |
|---|---|
| מקור | **Self-Written** |
| ייעוד | Single Source of Truth — כל הקבועים המכוילים של הפרויקט במקום אחד |
| גודל | ~50 שורות |
| תלויות | numpy (לאריי של HSV) |

**אין פונקציות — רק קבועים:**

| קבוע | טיפוס | תפקיד |
|---|---|---|
| `FRAME_WIDTH`, `FRAME_HEIGHT` | int | 640, 480 |
| `FRAME_CENTER_X`, `FRAME_CENTER_Y` | int | 320, 240 |
| `HSV_LOWER`, `HSV_UPPER` | np.ndarray | סף תחתון ועליון לזיהוי כחול |
| `MIN_CONTOUR_AREA` | int | 200 — סף שטח מינימלי לקונטור |
| `FIRE_PIXEL_THRESHOLD` | int | 15 — סף ירייה |
| `KP_PAN`, `KP_TILT` | float | 0.017 — מקדמי P |
| `KI_*`, `KD_*` | float | 0.0 — אינטגרל/דריבטיב |
| `PID_OUTPUT_LIMIT` | float | 10.0 — חסם תיקון לפר־פריים |
| `TRACKING_DEADBAND_PX` | int | 15 — Deadband |
| `COAST_MAX_FRAMES` | int | 30 — Coast |
| `COAST_DECAY` | float | 0.95 |
| `COAST_MIN_CORRECTION_DEG` | float | 0.1 |
| `RECENTER_AFTER_COAST` | bool | True |
| `RECENTER_STEP_DEG` | float | 2.0 |
| `BORESIGHT_X_OFFSET`, `BORESIGHT_Y_OFFSET` | int | היסט מצלמה ↔ לייזר |

**תקלות נפוצות:** שינוי קבוע ב־`config.py` לא נכנס לתוקף מיד כאשר
GUI כבר רץ — צריך ללחוץ "Reload Config" ב־control panel או להפעיל
מחדש את הסקריפט.

### 13.2.2 `servo.py` — Owner Module ל־PCA9685 + DS3225

| תכונה | ערך |
|---|---|
| מקור | **Self-Written** |
| ייעוד | בעלות בלעדית על המעגל סרוו — קוד אחר חייב לקרוא לפונקציות שלו |
| גודל | ~180 שורות |
| תלויות חיצוניות (BB) | `adafruit-circuitpython-servokit`, `adafruit-blinka` |

**API ציבורי:**

| פונקציה | חתימה | תפקיד |
|---|---|---|
| `init()` | `() -> ServoKit` | מאתחל את PCA9685, מגדיר את 2 הערוצים, מצמיד למרכז |
| `move_pan(kit, angle, ramp=True)` | `(ServoKit, float, bool) -> float` | מזיז סרוו הפאן לזווית; מצומצם לטווח [PAN_MIN, PAN_MAX]; מחזיר את הזווית בפועל |
| `move_tilt(kit, angle, ramp=True)` | `(ServoKit, float, bool) -> float` | כנ"ל לטילט |
| `center(kit)` | `(ServoKit,) -> None` | החזרה ל־(PAN_CENTER, TILT_CENTER) |
| `cleanup(kit)` | `(ServoKit,) -> None` | החזרה למרכז + שחרור — נקרא מ־`finally` |
| `current_pan()`, `current_tilt()` | `() -> Optional[float]` | מחזיר את הזווית האחרונה ששלחה התוכנה |

**שימוש בפרויקט:** כל קוד שעובד עם הסרוו מחויב לעבור דרך `servo.py`.
ה־`clamping` של גבולות הזווית מתבצע פנימית — `tracker.py` או
`control_panel.py` יכולים לבקש זווית מחוץ לטווח בלי שיינזק.

**תקלות נפוצות:**
- **קריאת `move_pan/tilt` לפני `init()`** — זורק `RuntimeError`.
- **שכחה של `cleanup`** — הסרוו נשאר במצב לא־מוגדר; ההפעלה הבאה
  תקפץ.
- **שימוש ב־`ramp=True` בלולאת tracking** — חוסם את הלולאה
  ל־250 ms בכל תיקון; חובה `ramp=False` בלולאת PID.

### 13.2.3 `camera.py` — Owner Module ל־LifeCam

| תכונה | ערך |
|---|---|
| מקור | **Self-Written** |
| ייעוד | בעלות בלעדית על המצלמה |
| גודל | ~60 שורות |
| תלויות חיצוניות (BB) | `cv2` (`cv2.VideoCapture`) |

**API ציבורי:**

| פונקציה | חתימה | תפקיד |
|---|---|---|
| `init(width=640, height=480, device_index=0)` | `(int, int, int) -> cv2.VideoCapture` | פותח את ה־webcam, מגדיר רזולוציה, מחזיר VideoCapture |
| `capture_frame(cap)` | `(cv2.VideoCapture,) -> np.ndarray` | דוגם פריים BGR אחד |
| `release(cap)` | `(cv2.VideoCapture,) -> None` | שחרור משאבי המצלמה (`finally`) |

**שימוש בפרויקט:** `detector.py` ו־`tracker.py` עובדים עם פריים
שמתקבל מ־`camera.capture_frame()`. הם לא יודעים שמדובר ב־UVC או
ב־OpenCV.

**תקלות נפוצות:**
- **`Cannot open camera`** — המצלמה תפוסה (תהליך אחר רץ עם cv2)
  או לא מחוברת. הריצו `pgrep -fa python` לאיתור.
- **`Cannot query video position`** warning — שפיר, v4l2 fallback
  עובד.

### 13.2.4 `detector.py` — אלגוריתם זיהוי HSV

| תכונה | ערך |
|---|---|
| מקור | **Self-Written** |
| ייעוד | זיהוי המטרה הצבעונית בפריים |
| גודל | ~90 שורות |
| תלויות חיצוניות (BB) | `cv2`, `numpy`, `config` |

**API ציבורי:**

| פונקציה | חתימה | תפקיד |
|---|---|---|
| `detect(frame)` | `(np.ndarray,) -> Optional[Tuple[int, int]]` | מחזיר `(cx, cy)` של מרכז המסה, או `None` |
| `build_mask(frame)` | `(np.ndarray,) -> np.ndarray` | מחזיר את המסכה הבינארית (נחשף ל־tune_detector.py) |

**הצינור הפנימי** (פרטים ב־§15.3):

1. Gaussian blur 5×5.
2. BGR → HSV.
3. `cv2.inRange` עם הגבולות מ־config.
4. Morphological opening (erode → dilate, iterations=2).
5. `findContours` (RETR_EXTERNAL).
6. בחירת הקונטור הגדול ביותר.
7. סינון לפי שטח מינימלי.
8. חישוב moments → centroid.

**תקלות נפוצות:**
- **מטרה לא מזוהה** — HSV לא מכויל לתאורה הנוכחית; הפעילו את
  `tune_detector.py`.
- **רעש מזהה אובייקטים שגויים** — הגדילו את `MIN_CONTOUR_AREA`
  ב־config.

### 13.2.5 `tracker.py` — בקרי PID + מצבי קצה

| תכונה | ערך |
|---|---|
| מקור | **Self-Written** |
| ייעוד | המרת זיהוי מ־detector לתיקון סרוו; מכונת מצבים של 5 מצבים |
| גודל | ~250 שורות |
| תלויות חיצוניות (BB) | `simple_pid` |
| תלות פנימית | `servo.py`, `config.py` |

**API ציבורי:**

| פונקציה | חתימה | תפקיד |
|---|---|---|
| `init()` | `() -> Tuple[PID, PID]` | יוצר 2 instances של PID |
| `update(pan_pid, tilt_pid, kit, target_pos)` | `(PID, PID, ServoKit, Optional[Tuple[int,int]]) -> Optional[Dict]` | איטרציה אחת בלולאה |
| `stop(kit)` | `(ServoKit,) -> None` | כיבוי, מאציל ל־`servo.cleanup` |

**מצב פנימי:**

- `_last_pan_correction`, `_last_tilt_correction`: float — תיקוני PID
  האחרונים, ל־Coast.
- `_coast_frames_remaining`: int — מונה Coast.
- `_recentering`: bool — בתהליך Recenter?

**מבנה `update()`:** מכונת מצבים של 5 מצבים (פירוט ב־§11.8).

**תקלות נפוצות:**
- **הברקט רוטט** — `KD > 0` מגביר רעש; וודאו `KD_PAN = KD_TILT = 0`.
- **הברקט לא מגיע למטרה** — `Kp` נמוך מדי; אופציה: הגדלת ל־0.02–0.025.
- **קפיצות חדות** — `PID_OUTPUT_LIMIT` גבוה מדי; הקטינו ל־5.

### 13.2.6 `laser.py` — Owner Module ל־GPIO18

| תכונה | ערך |
|---|---|
| מקור | **Self-Written** |
| ייעוד | בעלות בלעדית על GPIO18; הפעלה/כיבוי בטוחים של הלייזר |
| גודל | ~40 שורות |
| תלויות חיצוניות (BB) | `gpiozero` |

**API ציבורי:**

| פונקציה | חתימה | תפקיד |
|---|---|---|
| `init()` | `() -> gpiozero.LED` | מגדיר GPIO18 כפלט, מצמיד ל־OFF, מחזיר LED object |
| `fire(laser_dev)` | `(LED,) -> None` | מדליק הלייזר |
| `off(laser_dev)` | `(LED,) -> None` | מכבה |
| `cleanup(laser_dev)` | `(LED,) -> None` | מכבה + משחרר GPIO; נקרא מ־`finally`; בולע חריגות |

**חוזה בטיחות:**
- הלייזר OFF כאשר המודול אותחל.
- הלייזר OFF כאשר המודול נסגר.
- **שם המשתנה חייב להיות `laser_dev` ולא `laser`** — אחרת
  משתנה־שמודול־מקבילים מתנגשים (תועד ב־`CLAUDE.md`).

**תקלות נפוצות:**
- **הלייזר נדלק בעת הפעלה** — Pulldown 100kΩ לא מחובר; ראו §10.5.
- **`AttributeError: 'NoneType' object`** — נקרא `fire()` לפני `init()`.

### 13.2.7 `control_panel.py` — GUI tkinter

| תכונה | ערך |
|---|---|
| מקור | **Self-Written** |
| ייעוד | ממשק משתמש אחד שעוטף את כל פונקציות הבדיקה והכיול |
| גודל | ~600 שורות |
| תלויות חיצוניות (BB) | `tkinter` (stdlib) |
| תלות פנימית | `servo`, `camera`, `laser`, `config` |

**מחלקה ראשית:**

```python
class ControlPanel(tk.Tk):
    def __init__(self): ...
    def init_hardware(self): ...
    def center_servos(self): ...
    def move_to_sliders(self): ...
    def fire_laser_one_sec(self): ...
    def emergency_stop(self): ...
    def start_tracking_test(self): ...
    def tune_hsv(self): ...
    def reload_config(self): ...
    def shutdown_pi(self): ...
    def on_close(self): ...
```

**טכניקות חשובות:**

- **`threading.Thread`** לרענון סטטוס ב־5Hz בלי לחסום ה־GUI.
- **`subprocess.Popen`** להפעלת `test_tracking.py` או
  `tune_detector.py` בתהליכים נפרדים (להימנע מהתנגשות חלונות OpenCV
  עם tkinter).
- **`QueueHandler` של Python's logging** לתעלת `logging` של כל
  המערכת לחלון אחד.
- **`WM_DELETE_WINDOW`** לטיפול בסגירה — `cleanup` בטוח.

**תקלות נפוצות:**
- **הכפתורים לא עובדים** — לא נלחץ "Initialize hardware" עוד.
- **חלון OpenCV לא נראה ב־VNC** — `export DISPLAY=:0`.
- **PCA9685 תפוס** — בדיקת tracking פעילה; לחיצה על Emergency Stop.

### 13.2.8 `main.py` — אינטגרציה סופית

| תכונה | ערך |
|---|---|
| מקור | **Self-Written** |
| ייעוד | נקודת הכניסה האולטימטיבית — מצלמה → גלאי → PID → סרוו → לייזר |
| גודל | ~120 שורות |
| תלויות פנימיות | `servo`, `camera`, `detector`, `tracker`, `laser`, `config` |

**מבנה:**

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
            handle_keypress(result, laser_dev)  # 'f' → fire if locked
            if 'q' pressed: break
    finally:
        laser.cleanup(laser_dev)
        servo.cleanup(kit)
        camera.release(cam)
```

**חוזה הירייה:** הירייה מתבצעת רק כאשר `result['in_deadband'] == True`.

### 13.2.9 סקריפטי בדיקה וכיול

| קובץ | מקור | ייעוד |
|---|---|---|
| `test_servo.py` | Self-Written | בדיקת חוליית הסרוו — מעבר דרך זוויות סטנדרטיות |
| `test_tracking.py` | Self-Written | בדיקת לולאת הראייה מקצה לקצה עם overlay חזותי |
| `test_laser.py` | Self-Written | בדיקת רצף ירייה — `init`, ספירה לאחור, `fire`, `off`, `cleanup` |
| `calibrate_servo.py` | Self-Written | כלי כיול אינטראקטיבי לגבולות מכאניים |
| `tune_detector.py` | Self-Written | כיוון HSV עם 6 trackbars חיים |
| `boresight.py` | Self-Written | כיול היסט מצלמה ↔ לייזר |

כולם כתובים כסקריפטים עצמאיים (`if __name__ == "__main__"`), משתמשים
ב־Owner Modules, ועוטפים ב־`try/finally`.

---

## 13.3 ספריות צד שלישי (BB — Building Blocks)

הספריות האלה הן בקוד פתוח, לא נכתבו על־ידי הסטודנט, אבל הוטמעו
כתלות. השימוש בהן נעשה דרך ה־API הציבורי המתועד שלהן; לא נלקח קוד
מתוכן והועתק למודולי הפרויקט.

### 13.3.1 OpenCV (`cv2`)

| תכונה | ערך |
|---|---|
| מקור | **BB** — Intel/Itseez/OpenCV.org |
| התקנה | apt: `python3-opencv` |
| גרסה | ~4.6.x (Bookworm) |
| רישיון | Apache 2.0 |
| גודל | ~70 MB מקומפל |

**ייעוד בפרויקט:** כל ה־computer vision — קליטת וידאו, המרת מרחבי
צבע, סף, מורפולוגיה, contours, moments, תצוגה.

**פונקציות עיקריות בשימוש:**

| פונקציה | שימוש |
|---|---|
| `cv2.VideoCapture(0)` | פתיחת המצלמה |
| `cv2.cvtColor(frame, COLOR_BGR2HSV)` | המרת מרחב צבע |
| `cv2.inRange(hsv, lower, upper)` | סף בינארי |
| `cv2.GaussianBlur(frame, (5,5), 0)` | החלקת רעש |
| `cv2.erode`, `cv2.dilate` | מורפולוגיה |
| `cv2.findContours(mask, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)` | מציאת קונטורים |
| `cv2.contourArea(c)` | חישוב שטח קונטור |
| `cv2.moments(c)` | חישוב moments → centroid |
| `cv2.imshow`, `cv2.waitKey` | תצוגה במחזור |
| `cv2.circle`, `cv2.putText` | overlay על הפריים |

**תקלות נפוצות:**
- **`Cannot query video position`** — warning מ־v4l2 backend; שפיר.
- **חלון לא נראה ב־SSH ללא X11** — חובה VNC או `DISPLAY` מוגדר.
- **גרסת apt לא עדכנית** — בדרך כלל מספיק; אם נדרשת גרסה חדשה
  צריך לקמפל ידנית (לא בשימוש בפרויקט).

### 13.3.2 NumPy

| תכונה | ערך |
|---|---|
| מקור | **BB** — NumPy Foundation |
| התקנה | apt: `python3-numpy` |
| גרסה | 1.24.x (Bookworm) |
| רישיון | BSD-3 |

**ייעוד בפרויקט:** ייצוג תמונות (כל `cv2` חוזר עם `np.ndarray`),
ייצוג גבולות HSV (`np.array([79, 76, 0])`), חישובים וקטוריים.

**פונקציות עיקריות בשימוש:**

| פונקציה | שימוש |
|---|---|
| `np.array(...)` | יצירת מערך מרשימה |
| `frame.shape`, `frame.dtype` | בדיקת מבנה פריים |
| `np.zeros(...)` | יצירת מסכה ריקה |

**תקלות נפוצות:**
- **שגיאת `dtype mismatch`** — בדרך כלל כי לא מציינים `dtype=np.uint8`
  על הגבולות.

### 13.3.3 Adafruit CircuitPython ServoKit

| תכונה | ערך |
|---|---|
| מקור | **BB** — Adafruit Industries |
| התקנה | pip: `adafruit-circuitpython-servokit` |
| גרסה | ~1.3.x |
| רישיון | MIT |
| תלוי ב | `adafruit-circuitpython-pca9685`, `adafruit-blinka` |

**ייעוד בפרויקט:** API גבוה לשליטה בסרוו דרך PCA9685.

**פונקציות עיקריות בשימוש (בתוך `servo.py`):**

| פונקציה | שימוש |
|---|---|
| `ServoKit(channels=16)` | יצירת אובייקט |
| `kit.servo[ch].set_pulse_width_range(500, 2500)` | הגדרת טווח פולסים ל־DS3225 |
| `kit.servo[ch].actuation_range = 270` | הגדרת טווח זוויתי |
| `kit.servo[ch].angle = 135.0` | שליחת זווית — תרגום ל־I²C אוטומטי |

**תקלות נפוצות:**
- **`ImportError: No module named 'board'`** — חסר `adafruit-blinka`;
  התקן עם `pip install adafruit-blinka`.
- **`OSError: [Errno 121] Remote I/O error`** — I²C לא מגיב; בדוק
  `i2cdetect -y 1` לכתובת 0x40.
- **`actuation_range` שגוי** — ServoKit ברירת מחדל 180°; חובה
  להגדיר 270° ל־DS3225 — אחרת זוויות לא נכונות.

### 13.3.4 Adafruit CircuitPython PCA9685

| תכונה | ערך |
|---|---|
| מקור | **BB** — Adafruit Industries |
| התקנה | pip: `adafruit-circuitpython-pca9685` |
| גרסה | ~3.4.x |

**ייעוד בפרויקט:** דרייבר ברמה נמוכה לשבב PCA9685. **לא בשימוש
ישיר** — ServoKit עוטף אותו.

**פונקציות שזמינות (לא בשימוש בפרויקט):** `pca.frequency`,
`pca.channels[ch].duty_cycle`.

### 13.3.5 Adafruit Blinka

| תכונה | ערך |
|---|---|
| מקור | **BB** — Adafruit Industries |
| התקנה | pip: `adafruit-blinka` |
| גרסה | ~8.x |

**ייעוד בפרויקט:** Shim שמספק את ה־objects `board`, `digitalio`,
`busio` של CircuitPython על Raspberry Pi. מאפשר ל־ServoKit לעבוד
על Pi בלי לקבל port מ־microcontroller.

**שימוש בקוד שלנו:** אין ישיר — דרך ServoKit.

### 13.3.6 simple-pid

| תכונה | ערך |
|---|---|
| מקור | **BB** — m-lundberg (GitHub) |
| התקנה | pip: `simple-pid` |
| גרסה | ~1.0.1 |
| רישיון | MIT |
| גודל | ~400 שורות קוד |

**ייעוד בפרויקט:** חישוב תיקון PID לכל פריים בלולאת ה־tracker.

**פונקציות עיקריות בשימוש (בתוך `tracker.py`):**

| פונקציה | שימוש |
|---|---|
| `PID(Kp, Ki, Kd, setpoint=0, output_limits=(-LIM, LIM))` | יצירת בקר |
| `correction = pid(error)` | חישוב תיקון; dt מובנה |
| `pid.tunings = (Kp, Ki, Kd)` | שינוי מקדמים בזמן ריצה (לא בשימוש) |
| `pid.output_limits = (low, high)` | שינוי חסם פלט (לא בשימוש) |

**תקלות נפוצות:**
- **תיקון תמיד אפס** — נשכח להגדיר `setpoint` או `Kp = 0`.
- **קפיצות גדולות** — נשכח להגדיר `output_limits`.
- **חוסר יציבות** — `Kd > 0` מגביר רעש (תועד ב־§14).

### 13.3.7 gpiozero

| תכונה | ערך |
|---|---|
| מקור | **BB** — Raspberry Pi Foundation |
| התקנה | apt: `python3-gpiozero` |
| גרסה | ~2.0 (Bookworm) |
| רישיון | BSD-3 |

**ייעוד בפרויקט:** API גבוה ל־GPIO18 שמפעיל את ה־MOSFET של הלייזר.

**פונקציות עיקריות בשימוש (בתוך `laser.py`):**

| פונקציה | שימוש |
|---|---|
| `LED(18)` | יצירת אובייקט; מאתחל GPIO18 כפלט וכותב 0 |
| `led.on()` | כותב 1 ל־GPIO |
| `led.off()` | כותב 0 ל־GPIO |
| `led.is_lit` | מחזיר True/False |
| `led.close()` | שחרור משאב ה־GPIO (`finally`) |

**תקלות נפוצות:**
- **`GPIO busy`** — תהליך אחר מחזיק את הפין; הריצו
  `sudo pkill -f python` ונסו שוב.
- **`PinFactoryFallback` warning** — שפיר; gpiozero מנסה כמה
  backends ובוחר את הזמין.

### 13.3.8 tkinter

| תכונה | ערך |
|---|---|
| מקור | **BB** — Python Software Foundation (stdlib) |
| התקנה | מובנה ב־Python 3.11 (אין צורך ב־pip) |
| רישיון | PSF License |

**ייעוד בפרויקט:** ממשק GUI של `control_panel.py`.

**מודולים עיקריים בשימוש:**

| מודול | שימוש |
|---|---|
| `tkinter` | חלון ראשי, widgets בסיסיים |
| `tkinter.ttk` | widgets מודרניים (LabelFrame, Button, Entry) |
| `tkinter.scrolledtext` | חלון לוג עם scrollbar |
| `tkinter.messagebox` | דיאלוגים (אישור ירייה, שגיאות) |

**תקלות נפוצות:**
- **`_tkinter.TclError: no display name`** — חסר `DISPLAY`; הגדירו
  `export DISPLAY=:0`.
- **GUI קופא** — פעולה ארוכה רצה ב־main thread במקום ב־subprocess;
  פתרון: `subprocess.Popen` או `threading.Thread`.

---

## 13.4 גרף תלויות

```
                           ┌─────────────┐
                           │  config.py  │  ← Self-Written
                           └──────┬──────┘
                                  │
        ┌─────────┬───────────────┼───────────────┬─────────┐
        ↓         ↓               ↓               ↓         ↓
   ┌─────────┐ ┌────────┐  ┌──────────┐  ┌────────────┐  ┌────────┐
   │servo.py │ │camera  │  │detector  │  │ tracker.py │  │laser.py│  ← Self-Written
   │         │ │.py     │  │  .py     │  │            │  │        │
   └────┬────┘ └────┬───┘  └────┬─────┘  └─────┬──────┘  └───┬────┘
        │           │           │              │             │
        ↓           ↓           ↓              ↓             ↓
  ┌──────────┐ ┌──────┐    ┌──────┐     ┌─────────────┐ ┌─────────┐
  │ ServoKit │ │ cv2  │    │ cv2  │     │ simple-pid  │ │gpiozero │  ← BB
  │ + Blinka │ │      │    │+numpy│     │             │ │         │
  └──────────┘ └──────┘    └──────┘     └─────────────┘ └─────────┘
```

`config.py` הוא העלים — אינו תלוי בכלום מהפרויקט. שאר ה־Owner
Modules תלויים בו ובספרייה אחת חיצונית. הקוד שלמעלה (`main.py`,
`control_panel.py`) תלוי בכל ה־Owner Modules.

**אין תלויות מעגליות.**

---

## 13.5 ניהול תלויות במאגר

### תלויות Python (`requirements.txt`)

```
adafruit-circuitpython-pca9685
adafruit-circuitpython-servokit
adafruit-blinka
simple-pid
```

ארבעת אלה לא נמצאים באפסטרים של Bookworm — חייבים להותקן בתוך
venv.

### תלויות מערכת (apt)

```
python3-opencv      → cv2
python3-numpy       → numpy
python3-gpiozero    → gpiozero
```

ה־venv נוצר עם הדגל `--system-site-packages` כדי לראות אותן.
החיסכון — לא חוזרים על קומפילציית OpenCV בתוך כל venv (זה לוקח
שעות על Pi).

### Stdlib

`tkinter` חלק מ־Python — אין מה להתקין.

---

## 13.6 סיכום

המערכת מורכבת מ:

- **14 קבצי Python שנכתבו ע"י הסטודנט** (Self-Written): מודולי בעלות
  (`servo`, `camera`, `detector`, `tracker`, `laser`), קונפיגורציה
  (`config`), אינטגרציה (`main`, `control_panel`), וסקריפטי בדיקה
  וכיול.
- **8 ספריות צד־שלישי (BB)**: OpenCV, NumPy, ServoKit, PCA9685,
  Blinka, simple-pid, gpiozero, tkinter. ארבע מהן מותקנות דרך pip
  בתוך venv, שלוש דרך apt, ואחת חלק מ־stdlib.

ההבחנה ברורה: כל קוד שמייצב את הפרויקט (`*.py` במאגר) נכתב על־ידי;
כל קוד שמעניק שכבת הפשטה בסיסית (גישה לחומרה, עיבוד תמונה, PID
generic) מקורו בקהילת קוד פתוח. הקפדה על שימוש דרך ה־API הציבורי
בלבד שומרת על האפשרות לעדכן את הספריות בלי לשבור את הפרויקט.
