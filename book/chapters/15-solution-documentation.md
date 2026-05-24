# 15. תיעוד הפתרון

הפרק מאגד את כל התיעוד הטכני שדורש המחוון: שרטוט חשמלי, חיבורים
ואופן הפעולה, קטעי קוד עיקריים, תרשים זרימה, תרשים פונקציונאלי,
התייחסות למערכת ההפעלה, והתייחסות לאבטחת מידע. כל סעיף עומד בפני
עצמו ואפשר לקרוא בנפרד.

---

## 15.1 שרטוט חשמלי (15.a)

שרטוט חשמלי מלא של המערכת. שלוש מסילות כוח (12V מהקיר, 5V לוגיקה
מ־Pi, 5V סרוו מ־LM2596), אדמה משותפת, ושני מעגלי בקרה (I²C ל־
PCA9685 ו־GPIO18 למתג הלייזר).

![שרטוט חשמלי מלא של המערכת](full-schematic.png)

### 15.1.1 שלושת מעגלי המשנה

**מעגל 1 — אספקת חשמל לסרוו:**

```
                    LM2596 Buck Converter
12V/5A   ┌────────┐      ┌──────────┐      ┌──────────────┐
PSU  ────┤   IN+  ├──────┤    +     ├──────┤  V+ (terminal)│
         │   IN-  ├──────┤   GND    ├──────┤  GND (terminal)│  PCA9685
         └────────┘      └──────────┘      └──────────────┘
                          (set to 5.0V                      ↓ channels 0,1
                           via trimpot                       ↓
                           BEFORE connecting)            2× DS3225
```

**מעגל 2 — לוגיקה ו־I²C:**

```
Raspberry Pi 4B                              PCA9685 (I²C 0x40)
 ┌─────────────────┐                         ┌──────────────────┐
 │ Pin 2  (5V)     ├─────────────────────────┤ VCC (logic)      │
 │ Pin 3  (GPIO2,SDA)─────────────────────────┤ SDA              │
 │ Pin 5  (GPIO3,SCL)─────────────────────────┤ SCL              │
 │ Pin 6  (GND)    ├─────────────────────────┤ GND              │
 │                 │                         │                   │
 └─────────────────┘                         └──────────────────┘
                                                    ↑
                                       (V+ comes from LM2596,
                                        kept ELECTRICALLY SEPARATE
                                        from VCC but sharing GND)
```

**מעגל 3 — מיתוג לייזר עם MOSFET ו־Pulldown:**

```
                              IRLZ44N MOSFET
                          (TO-220, N-Channel, Logic Level)
                                  
                                Gate   Drain   Source
                                  │     │       │
Pi GPIO18 ─── 220Ω ───────────────┘     │       │
(Pin 12, 3.3V)                          │       │
                                        │       │
                  ┌──── 100kΩ ─────────┘       │
                  │  (pulldown)                 │
                  │                             │
                Common                        Common
                 GND                           GND
                                                
                                                ↑
                                   Drain of MOSFET connects to:
                                                ↓
Pi Pin 4 (5V) ─── 100Ω ───── Laser(+) ─── Laser(−) ─── Drain
                  (current
                   limiter)                                
                                                       Source ─── Common GND
```

**זרימת זרם לייזר ON:** GPIO18 = HIGH (3.3V) → MOSFET נפתח (Drain
מחובר ל־Source דרך הערוץ) → זרם זורם מ־5V → 100Ω → laser(+) →
laser(−) → Drain → Source → GND. הדיודה פולטת אור.

**זרימת זרם לייזר OFF:** GPIO18 = LOW (0V) או floating → Pulldown
100kΩ מצמיד Gate ל־GND → MOSFET סגור → אין זרם דרך הלייזר.

### 15.1.2 חישובי הנגדים

| נגד | חישוב | משמעות |
|---|---|---|
| **100Ω** (גוף לייזר) | $(5V - V_f) / I_d = (5 - 3) / 0.020 = 100Ω$ | מגביל זרם דיודה ל־20mA — בטוח לדיודת 5mW |
| **220Ω** (Gate) | $V_{GPIO} / I_{max} = 3.3 / 0.015 = 220Ω$ | מגן GPIO ב־~15mA אם משהו נכשל |
| **100kΩ** (Pulldown) | מספיק נמוך כדי לסגור MOSFET ב־~100µs; מספיק גבוה כדי לא לבזבז זרם בעת ON | מבטיח GPIO LOW כברירת מחדל |

---

## 15.2 חיבורים ואופן הפעולה (15.b)

### 15.2.1 מטריצת חיווט מלאה

**Pi GPIO Header (40 פינים):**

| פין # | סיגנל | יעד | תפקיד |
|:---:|---|---|---|
| 2 | 5V | PCA9685 VCC | אספקת לוגיקה ל־PCA9685 |
| 3 | GPIO2 / SDA | PCA9685 SDA | נתוני I²C |
| 5 | GPIO3 / SCL | PCA9685 SCL | שעון I²C |
| 6 | GND | PCA9685 GND + Common GND | אדמה משותפת |
| 4 | 5V | מסילה אדומה ב־breadboard | אספקה ללייזר (דרך 100Ω) |
| 12 | GPIO18 | 220Ω → MOSFET Gate | פקודת on/off ללייזר |
| 14 | GND | מסילה כחולה ב־breadboard | אדמת מעגל הלייזר |
| (USB-A 1) | USB Data + Power | מצלמת LifeCam HD-3000 | זרם וידאו |
| (USB-C) | 5V Power | ספק USB-C 3A | חשמל ל־Pi |

**PCA9685:**

| חיבור | יעד |
|---|---|
| VCC | Pi פין 2 (5V) — אספקת לוגיקה |
| V+ (גרין טרמינל) | LM2596 OUT+ — אספקה לסרוו (5V/3A) |
| GND (גרין טרמינל) | LM2596 OUT− + Pi פין 6 GND |
| SDA | Pi פין 3 |
| SCL | Pi פין 5 |
| ערוץ 0 PWM | DS3225 פאן (חוט כתום) |
| ערוץ 1 PWM | DS3225 טילט (חוט כתום) |

**חוטי הסרוו:** DS3225 משתמש בקונבנציה צבעונית סטנדרטית:
**חום = GND**, **אדום = V+**, **כתום = PWM**. כל סרוו מתחבר לכותרת
3-pin של PCA9685 בערוצו.

### 15.2.2 אופן הפעולה הכולל

המערכת פועלת בלולאה רציפה של 30 fps. כל איטרציה:

1. **קליטת פריים** — `cv2.VideoCapture.read()` קוראת frame BGR
   מ־`/dev/video0` (LifeCam דרך uvcvideo).
2. **זיהוי מטרה** — `detector.detect()` מבצע: Gaussian blur → BGR→HSV
   → `cv2.inRange` → erode → dilate → findContours → בחירת הגדול
   ביותר → חישוב centroid. מחזיר `(cx, cy)` או `None`.
3. **חישוב שגיאה** — אם יש מטרה: `pan_error = cx - 320`,
   `tilt_error = cy - 240`.
4. **בקרת PID** — `simple_pid` מחשב `pan_correction` ו־
   `tilt_correction` במעלות (חתוך ל־±10°).
5. **בדיקת deadband** — אם השגיאה < 15 פיקסלים בשני הצירים,
   המערכת ב־"Locked" — לא שולחת תיקון.
6. **שליחה לסרוו** — `servo.move_pan/tilt()` שולחים פקודת I²C
   ל־PCA9685 שמייצר PWM ל־DS3225.
7. **טיפול במצבי קצה** — אם המטרה אבדה: Coast Mode (30 פריימים) →
   Recenter (חזרה למרכז) → Hold.
8. **אישור ירייה** — אם המפעיל לוחץ `'f'` ו־`in_deadband == True`,
   `laser.fire()` מצמיד GPIO18 ל־HIGH, ה־MOSFET נפתח, הלייזר נדלק
   למשך 1 שנייה, אז `laser.off()`.
9. **חזרה לשלב 1** — ~33ms עברו, פריים חדש מוכן.

הלולאה ממשיכה עד שהמפעיל לוחץ `'q'`. בלוק `finally` מבצע
`servo.cleanup` (חזרה למרכז), `laser.cleanup` (כיבוי), ו־
`camera.release`.

---

## 15.3 תיעוד קטעי קוד עיקריים (15.c)

הסעיף הזה מציג את **קטעי הקוד המרכזיים** של המערכת עם הסבר.
הקוד המלא במאגר.

### 15.3.1 `config.py` — Single Source of Truth

קבועים מכוילים במקום אחד. כל מודול אחר מייבא, לא משכפל ערכים.

```python
import numpy as np

# Frame geometry
FRAME_WIDTH: int = 640
FRAME_HEIGHT: int = 480
FRAME_CENTER_X: int = FRAME_WIDTH // 2   # 320
FRAME_CENTER_Y: int = FRAME_HEIGHT // 2  # 240

# HSV target range (tuned for blue target under indoor lighting)
HSV_LOWER: np.ndarray = np.array([79, 76, 0])
HSV_UPPER: np.ndarray = np.array([105, 255, 255])

# Detection
MIN_CONTOUR_AREA: int = 200
FIRE_PIXEL_THRESHOLD: int = 15

# PID gains (tuned empirically — 8 iterations, see §14.7)
KP_PAN: float = 0.017
KI_PAN: float = 0.0
KD_PAN: float = 0.0   # Kd amplifies detector centroid noise
KP_TILT: float = 0.017
KI_TILT: float = 0.0
KD_TILT: float = 0.0

PID_OUTPUT_LIMIT: float = 10.0       # max correction per frame, degrees
TRACKING_DEADBAND_PX: int = 15       # hold position within this error

# Coast mode (after target loss)
COAST_MAX_FRAMES: int = 30           # ~1 sec at 30 fps
COAST_DECAY: float = 0.95            # multiply correction each frame
COAST_MIN_CORRECTION_DEG: float = 0.1
RECENTER_AFTER_COAST: bool = True
RECENTER_STEP_DEG: float = 2.0
```

**הסבר:** קבועים בלבד. אין לוגיקה. כל ערך מתועד עם הסבר WHY בקוד
המקור (קטעי תגובה הושמטו כאן לקיצור). שינוי של HSV או PID דורש
עריכה רק כאן.

### 15.3.2 `servo.py` — Owner Module + Clamping

הליבה הבטיחותית — clamping של זוויות.

```python
PAN_MIN: float = 50.0
PAN_MAX: float = 220.0
TILT_MIN: float = 115.0
TILT_MAX: float = 205.0

def move_pan(kit: ServoKit, angle: float, ramp: bool = True) -> float:
    """
    Move pan to `angle`, clamped to the safe physical range [PAN_MIN, PAN_MAX].
    This is the SAFETY-CRITICAL function for pan.
    """
    global _pan_current

    if _pan_current is None:
        raise RuntimeError("servo.init() must be called before move_pan()")

    clamped = max(PAN_MIN, min(PAN_MAX, angle))
    if clamped != angle:
        log.warning(
            "Pan request %.1f° clamped to %.1f° (limits %.1f°-%.1f°)",
            angle, clamped, PAN_MIN, PAN_MAX,
        )

    if ramp:
        _pan_current = _ramp(kit, PAN_CHANNEL, _pan_current, clamped)
    else:
        kit.servo[PAN_CHANNEL].angle = clamped
        _pan_current = clamped

    return _pan_current
```

**הסבר:** הפונקציה תמיד מצמידה את הזווית הנדרשת לטווח הבטוח. אין
דרך עוקפת — כל קוד שרוצה להזיז את הסרוו חייב לעבור דרך כאן.
החזרה (`clamped`) מאפשרת ל־caller (למשל `tracker.update`) לדעת
אם הבקשה שלו נחתכה.

### 15.3.3 `detector.py` — צינור HSV

הצינור המלא של זיהוי המטרה.

```python
def detect(frame: np.ndarray) -> Optional[Tuple[int, int]]:
    """Find the target in a BGR frame. Returns (x, y) or None."""
    mask = build_mask(frame)   # blur → HSV → inRange → erode → dilate

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < config.MIN_CONTOUR_AREA:
        return None   # noise, not target

    moments = cv2.moments(largest)
    if moments["m00"] == 0:
        return None   # guard against divide-by-zero

    cx = int(moments["m10"] / moments["m00"])
    cy = int(moments["m01"] / moments["m00"])
    return cx, cy


def build_mask(frame: np.ndarray) -> np.ndarray:
    """blur → BGR→HSV → inRange → erode → dilate."""
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, config.HSV_LOWER, config.HSV_UPPER)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    return mask
```

**הסבר:** הצינור מורכב משבעה שלבים — כל אחד מטפל בהיבט אחר של
האלגוריתם (החלקת רעש → המרה ל־HSV → סף → ניקוי מורפולוגי → מציאת
קונטורים → בחירת הגדול → חישוב centroid). כל קריאה ל־`cv2` בנפרד
היא $O(WH)$, סך הכל ~5–8ms.

### 15.3.4 `tracker.py` — PID + מכונת מצבים

לב הבקרה. מטפל ב־5 מצבים: Tracking, Locked, Coasting, Recentering, Holding.

```python
def update(pan_pid, tilt_pid, kit, target_pos):
    """One iteration. Call once per frame."""
    global _last_pan_correction, _last_tilt_correction
    global _coast_frames_remaining, _recentering

    # ---- Target lost branch ----------
    if target_pos is None:
        last_was_meaningful = (
            abs(_last_pan_correction) >= config.COAST_MIN_CORRECTION_DEG
            or abs(_last_tilt_correction) >= config.COAST_MIN_CORRECTION_DEG
        )
        if _coast_frames_remaining > 0 and last_was_meaningful:
            # COASTING — apply last correction with decay
            requested_pan = servo.current_pan() + _last_pan_correction
            requested_tilt = servo.current_tilt() + _last_tilt_correction
            actual_pan = servo.move_pan(kit, requested_pan, ramp=False)
            actual_tilt = servo.move_tilt(kit, requested_tilt, ramp=False)
            _last_pan_correction *= config.COAST_DECAY  # 0.95
            _last_tilt_correction *= config.COAST_DECAY
            _coast_frames_remaining -= 1
            return {..., "coasting": True}

        if config.RECENTER_AFTER_COAST and not _recentering:
            # Coast ended without target — start RECENTERING
            _recentering = True

        if _recentering:
            # Step toward center at RECENTER_STEP_DEG per frame
            pan_step = ...   # capped
            tilt_step = ...
            servo.move_pan(kit, servo.current_pan() + pan_step, ramp=False)
            servo.move_tilt(kit, servo.current_tilt() + tilt_step, ramp=False)
            return {..., "recentering": True}

        return None   # HOLDING

    # ---- Target acquired branch — PID tracking ----------
    if _recentering:
        _reset_recenter()  # target back — abort recenter

    target_x, target_y = target_pos
    pan_error = target_x - config.FRAME_CENTER_X
    tilt_error = target_y - config.FRAME_CENTER_Y

    pan_correction = pan_pid(pan_error)
    tilt_correction = tilt_pid(tilt_error)

    in_deadband = (
        abs(pan_error) < config.TRACKING_DEADBAND_PX
        and abs(tilt_error) < config.TRACKING_DEADBAND_PX
    )

    if in_deadband:
        _reset_coast()
        return {..., "in_deadband": True}   # LOCKED

    # ramp=False because ramp's 50ms/2° sleeps would block the loop
    actual_pan = servo.move_pan(kit, servo.current_pan() + pan_correction, ramp=False)
    actual_tilt = servo.move_tilt(kit, servo.current_tilt() + tilt_correction, ramp=False)

    _last_pan_correction = pan_correction
    _last_tilt_correction = tilt_correction
    _coast_frames_remaining = config.COAST_MAX_FRAMES

    return {..., "coasting": False}   # TRACKING
```

**הסבר:** הפונקציה מחליטה באיזה מצב המערכת ופועלת בהתאם. שלוש
החלטות עיקריות: (א) האם המטרה אבדה? אם כן — Coast / Recenter / Hold.
(ב) אם המטרה נמצאת — האם בתוך deadband? אם כן — Locked. (ג) אחרת —
PID פעיל. `ramp=False` חשוב — בלעדיו הלולאה נחסמת ל־250ms בכל
תיקון (לקח מ־§14.7).

### 15.3.5 `laser.py` — בטיחות ירייה

```python
LASER_PIN: int = 18   # BCM GPIO18

def init() -> LED:
    """Set up GPIO18 as output and explicitly drive it LOW."""
    laser_dev = LED(LASER_PIN)
    laser_dev.off()                       # explicit OFF
    log.info("Laser initialized on GPIO%d (OFF)", LASER_PIN)
    return laser_dev

def fire(laser_dev: LED) -> None:
    """Drive GPIO18 HIGH — laser ON."""
    laser_dev.on()
    log.info("Laser ON")

def off(laser_dev: LED) -> None:
    """Drive GPIO18 LOW — laser OFF. Always safe to call."""
    laser_dev.off()
    log.info("Laser OFF")

def cleanup(laser_dev: LED) -> None:
    """Force OFF + release GPIO. Catches its own exceptions
    so it cannot mask the original error in finally blocks."""
    try:
        laser_dev.off()
    except Exception:
        log.exception("Error driving laser pin LOW during cleanup")
    try:
        laser_dev.close()
    except Exception:
        log.exception("Error closing laser device during cleanup")
```

**הסבר:** שלוש שכבות בטיחות לאחור: (א) ה־init מצמיד ל־LOW במפורש,
(ב) הסכמה החיצונית של MOSFET + Pulldown 100kΩ שומרת על OFF גם
כש־GPIO צף, (ג) ה־cleanup קורא `off()` ואז `close()` עם try/except
על כל פעולה — לא יוכל להפיל את ה־finally אם משהו נכשל.

### 15.3.6 `test_tracking.py` — לולאת ה־tracking הסופית

המערכת רצה end-to-end דרך הסקריפט הזה (camera + detector + PID +
servos, ללא לייזר — `main.py` נשמר לעתיד עם אינטגרציית לייזר).

```python
def main() -> int:
    kit = servo.init()
    cam = camera.init()
    pan_pid, tilt_pid = tracker.init()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    try:
        while True:
            frame = camera.capture_frame(cam)
            target = detector.detect(frame)
            result = tracker.update(pan_pid, tilt_pid, kit, target)

            display = frame.copy()
            _draw_overlay(display, target, result)
            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        return 0
    finally:
        tracker.stop(kit)
        camera.release(cam)
        cv2.destroyAllWindows()
```

**הסבר:** ה־try/finally מבטיח cleanup גם בעת חריגה או Ctrl+C.
הסדר חשוב: `tracker.stop(kit)` קורא ל־`servo.cleanup` (מרכז את
הסרוו), אז `camera.release` (משחרר את ה־webcam), אז
`cv2.destroyAllWindows` (סוגר חלון OpenCV).

---

## 15.4 תרשים זרימה (15.d)

תרשים הזרימה של הלולאה הראשית (`test_tracking.py main()`):

![תרשים זרימה — לולאת tracking](control-flow.png)

תיאור מילולי:

```
                    ┌─────────────────┐
                    │   START         │
                    │ servo.init      │
                    │ camera.init     │
                    │ tracker.init    │
                    └─────┬───────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ camera.capture_    │◄──────────────┐
                │   frame()          │               │
                └─────┬──────────────┘               │
                      ▼                              │
              ┌──────────────────┐                   │
              │ detector.detect()│                   │
              └─────┬────────────┘                   │
                    ▼                                │
              ┌──────────────────┐                   │
              │ tracker.update() │                   │
              │  (5 states FSM)  │                   │
              └─────┬────────────┘                   │
                    ▼                                │
            ┌────────────────────┐                   │
            │  draw overlay      │                   │
            │  cv2.imshow        │                   │
            └─────┬──────────────┘                   │
                  ▼                                  │
          ┌────────────────────┐                     │
          │  cv2.waitKey(1)    │                     │
          │  == 'q' ?          │                     │
          └────┬───────────┬───┘                     │
              YES         NO ────────────────────────┘
               ▼
       ┌──────────────────┐
       │ finally:         │
       │  tracker.stop    │
       │  camera.release  │
       │  destroyAllWind. │
       └──────┬───────────┘
              ▼
        ┌──────────┐
        │   END    │
        └──────────┘
```

זרימת `tracker.update()` עצמה (החלטת מצב):

```
                  target_pos == None ?
                       │
              YES ◄────┴────► NO
               │              │
               ▼              ▼
       (last correction      _recentering
        meaningful + coast    flag set?
        frames remaining?)         │
               │           YES ◄───┴───► NO
       YES ◄───┴───► NO            │            (compute error)
       │            │              ▼            error < deadband?
       ▼            ▼     (move toward center)       │
   COASTING    (recenter             │           YES ◄─┴─► NO
   apply       enabled?)             ▼            │     │
   correction       │            return            ▼     ▼
   × decay     YES ◄┴► NO        (RECENTERING)  LOCKED  TRACKING
                │     │                         (hold)  (PID
                ▼     ▼                                  + move
            set       return                              servo)
            _recentering=True  (HOLDING)
                ▼
            (next frame)
```

---

## 15.5 תרשים פונקציונאלי (15.e)

תרשים פונקציונאלי מציג את **זרימת הנתונים** בין מודולי הפרויקט,
לא את שלבי הבקרה (זה בתרשים הזרימה לעיל):

![תרשים פונקציונאלי](functional-diagram.png)

תיאור מילולי:

```
   ╔══════════════════════════════════════════════════════════════╗
   ║                  ORCHESTRATION LAYER                          ║
   ║  test_tracking.py / control_panel.py / main.py (future)       ║
   ║   - main loop                                                  ║
   ║   - user interaction                                           ║
   ║   - lifecycle (init, finally cleanup)                          ║
   ╚════════════╤═══════════════════════════════╤═════════════════╝
                │ uses                          │ uses
                ▼                               ▼
   ╔════════════════════════╗   ╔═════════════════════════════════╗
   ║      LOGIC LAYER       ║   ║   HARDWARE ABSTRACTION LAYER    ║
   ║  ─────────────────     ║   ║  ─────────────────────────────  ║
   ║                        ║   ║                                  ║
   ║  detector.py           ║   ║  servo.py    camera.py  laser.py║
   ║   detect(frame)        ║   ║   move_*      init      fire    ║
   ║    → (cx,cy) | None    ║   ║   center      capture   off     ║
   ║   build_mask(frame)    ║   ║   cleanup     release   cleanup ║
   ║    → np.ndarray        ║   ║                                  ║
   ║                        ║   ║   (Owner Modules — each wraps   ║
   ║  tracker.py            ║   ║    exactly one HW subsystem)    ║
   ║   init() → (pan,tilt)  ║   ║                                  ║
   ║   update(...)          ║   ╚════════════╤════════════════════╝
   ║    → result dict       ║                │ exclusive imports
   ║                        ║                ▼
   ╚═════════╤══════════════╝   ╔═════════════════════════════════╗
             │ uses             ║       THIRD-PARTY LIBRARIES      ║
             │                  ║                                   ║
             ▼                  ║  cv2  numpy  ServoKit+Blinka     ║
   ╔══════════════════════╗     ║  simple-pid  gpiozero  tkinter   ║
   ║   CONFIG LAYER       ║     ║                                   ║
   ║   ────────────       ║     ╚═══════════════════════════════════╝
   ║                      ║
   ║   config.py          ║◄─── ALL layers above import from config
   ║   (HSV, PID, limits, ║
   ║    Coast/Recenter)   ║
   ╚══════════════════════╝
```

**זרימת נתונים בפר־פריים:**

```
LifeCam ─USB─→ camera.capture_frame ─np.ndarray─→ detector.detect ─(x,y)─→ tracker.update ─deg─→ servo.move_* ─I²C─→ PCA9685 ─PWM─→ DS3225
                                                                                                                                          │
                                                                              ←──── motion changes camera position next frame ─────────────┘
```

---

## 15.6 התייחסות למערכת ההפעלה (15.f)

### 15.6.1 בחירת מערכת ההפעלה

הפרויקט רץ על **Raspberry Pi OS Bookworm 64-bit** (Debian 12).
ההיבטים שהשפיעו על הבחירה:

1. **תמיכה רשמית** — Raspberry Pi Foundation מתחזקת את ההפצה
   ספציפית ל־Pi 4B.
2. **64-bit** — נדרש לטעון 8GB RAM של ה־Pi (ב־32-bit הגבול 4GB).
3. **kernel 6.x עם uvcvideo מובנה** — מצלמת USB עובדת ללא דרייבר
   נוסף.
4. **apt עם `python3-opencv` מקומפל ל־ARM64** — חוסך שעות
   קומפילציה ידנית.
5. **systemd 252** — תזמון משימות (cron) ושירותי רקע.

### 15.6.2 דרישות סף

- **גרסה:** Bookworm 64-bit (לא 32-bit, לא Bullseye).
- **Kernel:** 6.6.x LTS (מובנה ב־Bookworm).
- **Python:** 3.11 (ברירת מחדל ב־Bookworm).
- **glibc:** 2.36+ (ברירת מחדל).

### 15.6.3 שירותי מערכת בשימוש

| שירות | תפקיד בפרויקט |
|---|---|
| `systemd-journald` | אגירת לוגים של הסקריפטים (דרך `logging`) |
| `NetworkManager` | חיבור Wi-Fi לסנכרון GitHub + SSH/VNC |
| `cron` | משימת `git pull` כל דקה |
| `sshd` | חיבור remote מהלפטופ |
| `vncserver` | תצוגת חלונות OpenCV מהלפטופ |
| `Xorg + LXDE/PIXEL` | הסביבה הגרפית של ה־Pi (ל־`control_panel.py`) |

### 15.6.4 משאבי OS שהקוד דורש

| משאב | מי משתמש | תפקיד |
|---|---|---|
| `/dev/video0` | `camera.py` | מצלמת USB דרך `uvcvideo` |
| `/dev/i2c-1` | `servo.py` (דרך ServoKit) | אוטובוס I²C |
| `/sys/class/gpio/gpio18` | `laser.py` (דרך gpiozero) | GPIO18 |
| TCP port 22 (SSH) | מהלפטופ | טרמינל remote |
| TCP port 5900 (VNC) | מהלפטופ | תצוגה גרפית remote |
| TCP port 443 (HTTPS) | cron job | גישה ל־GitHub לעדכון קוד |

### 15.6.5 cron job לסנכרון אוטומטי

ב־`/etc/cron.d/pi-auto-pull`:

```
* * * * * adam cd /home/adam/pi && /usr/bin/git pull --quiet 2>&1 | logger -t pi-auto-pull
```

מבצע `git pull` כל דקה. הפלט נשלח ל־`logger` כך שמופיע ב־
`journalctl -t pi-auto-pull`. זה מאפשר workflow של "עורכים על
הלפטופ, push ל־GitHub, הקוד על ה־Pi מעודכן בתוך דקה".

### 15.6.6 הגנות OS

- **`sudo` דורש סיסמה** לכל פעולה מערכתית.
- **`passwd` בטוח** — הסיסמה של `adam` לא דיפולטית.
- **משתמש `adam` לא ב־sudoers ללא סיסמה.**
- **SSH מקבל רק כניסות עם מפתח** (PasswordAuthentication מבוטל)
  — ראו §15.7.

---

## 15.7 התייחסות לאבטחת מידע (15.g)

### 15.7.1 סקירת איומים

ה־Pi מחובר לרשת Wi-Fi ביתית, נגיש ב־SSH ו־VNC. אילו האיומים
הרלוונטיים:

1. **גישה לא־מורשית ל־SSH** — תוקף ברשת מנסה כניסה בכוח־ברוטלי.
2. **גישה לא־מורשית ל־VNC** — חוסם פיזי שמשתמש בלפטופ של אדם
   אחר ברשת.
3. **קוד פתוח חושף סודות** — תוקן שמסתכל ב־GitHub repo מוצא
   credentials.
4. **נזק פיזי** — מישהו לוקח את ה־Pi ומחלץ ממנו מידע מה־microSD.
5. **שיבוש המערכת** — תוקף מנסה להפעיל את הלייזר מרחוק.

### 15.7.2 מערכת הגנות

**SSH:**

- **Public Key Authentication בלבד** — סיסמה בוטלה ב־
  `/etc/ssh/sshd_config`:
  ```
  PasswordAuthentication no
  PubkeyAuthentication yes
  ```
- **המפתח של הלפטופ** מותקן ב־`~/.ssh/authorized_keys`.
- **fail2ban** מנטר ניסיונות כניסה כושלים — חוסם IP אחרי 5 ניסיונות.

**VNC:**

- **דורש סיסמה** (RealVNC עם authentication).
- **לא חשוף לאינטרנט** — רק ב־LAN המקומית; הראוטר לא מעביר את
  פורט 5900 החוצה.

**GitHub:**

- **המאגר ציבורי** (לפי המחוון — תיק פרויקט פתוח לבדיקה).
- **אין בקוד secrets**: אין סיסמאות, API keys, או credentials.
  בדיקה ידנית של `git log -p` לפני העלאה ראשונה אישרה.
- **`.gitignore` כולל**: `venv/`, `__pycache__/`, `*.pyc`,
  `.vscode/`, אבל אין שם דבר רגיש.

**microSD:**

- **לא מוצפן** — Raspberry Pi OS תומך הצפנה אבל לא נכלל ב־default.
  ההחלטה: ה־Pi לא מאחסן נתונים רגישים; ההצפנה מוסיפה ביצועים
  פגומים בלי תועלת אמיתית.
- **תיוג פיזי** של ה־microSD עם שם הפרויקט — למניעת אובדן.

**רשת:**

- **WPA2/WPA3 על ה־Wi-Fi הביתי** — סיסמה חזקה.
- **אין port forwarding** מהראוטר ל־Pi — לא נגיש מהאינטרנט
  הציבורי.

### 15.7.3 הגנות ספציפיות ללייזר

הלייזר הוא וקטור התקפה ייחודי — אם תוקף מצליח להריץ קוד על ה־Pi,
הוא יכול להדליק אותו ולכוון אותו לכל מקום שהסרוו מאפשר.

**הגנות:**

1. **GPIO18 דורש שמשתמש מקומי יריץ קוד** — אין דרך מרחוק להפעיל
   את הלייזר חוץ מ־SSH/VNC.
2. **Pulldown 100kΩ** — אם משהו ב־userland כותב byte שגוי
   ל־`/sys/class/gpio`, ה־MOSFET לא נפתח באופן יציב.
3. **Clamping של זוויות הסרוו** — גם אם הלייזר נדלק, הוא מוגבל
   לטווח של ~170° × 90° — אי אפשר להפנות אותו "לכל הכיוונים".
4. **משך ירייה מוגבל ב־`main.py`** — `time.sleep(1.0)` קבוע;
   ארוך יותר ידרוש שינוי קוד.
5. **אישור מפעיל הוא הגנה אנושית** — בלי לחיצה פיזית של `'f'`,
   הלייזר לא נדלק.

### 15.7.4 התראות ולוגים

- **`journalctl`** מאגד את כל הלוגים של המערכת. ניתן לבדוק ניסיונות
  SSH כושלים: `journalctl -u sshd | grep "Failed password"`.
- **`logging` Python** של כל הסקריפטים — מודפס ל־stderr וגם נכנס
  ל־journald. רישום של כל הפעלת לייזר.
- **fail2ban-status** — בדיקה תקופתית של IP חסומים.

### 15.7.5 פרטיות

- **מצלמת USB מצלמת רק כשהסקריפט פעיל** — אין הקלטה לדיסק.
- **אין שליחת נתונים החוצה** — כל העיבוד מקומי על ה־Pi.
- **GitHub repo לא כולל וידאו או תמונות** — רק קוד וטקסט.

### 15.7.6 שיפורים עתידיים

לפרויקט הזה, רמת האבטחה הנוכחית **מספיקה** (פרויקט שולחני, רשת
ביתית). אם המערכת תוצב בסביבה ציבורית או תופעל מרחוק:

- **HTTPS עם self-signed cert** למקרה ש־control_panel יוחלף ב־web.
- **OAuth ל־GitHub** במקום SSH keys.
- **הצפנת microSD** עם LUKS.
- **2FA על SSH** עם Google Authenticator.

הצעות אלה לא ממומשות כיום — היו overkill לפרויקט סטודנט שולחני,
אבל תועדו לטובת הקורא העתידי.

---

## 15.8 סיכום

הפרק כיסה את שבע תחנות התיעוד שהמחוון דרש:

| § | מה |
|---|---|
| 15.1 | שרטוט חשמלי מלא עם חישובי הנגדים |
| 15.2 | מטריצת חיווט + תיאור אופן הפעולה הכולל |
| 15.3 | 6 קטעי קוד עיקריים עם הסברים |
| 15.4 | תרשים זרימה (לולאת `main()` + מכונת מצבי `tracker.update`) |
| 15.5 | תרשים פונקציונאלי (4 שכבות: orchestration, logic, hardware, config) |
| 15.6 | התייחסות למערכת ההפעלה (Bookworm, kernel, שירותים, cron) |
| 15.7 | התייחסות לאבטחת מידע (SSH keys, VNC, GitHub, microSD, רשת, לייזר, פרטיות) |

יחד הם מספקים את כל מה שמהנדס חיצוני צריך כדי לשחזר את המערכת,
לאבחן בעיה, או להוסיף שדרוג.
