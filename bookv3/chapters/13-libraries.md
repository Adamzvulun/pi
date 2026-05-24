# 13. הסבר ספריות (Self-Written + Building Blocks)

המחוון דורש להבחין בין **ספריות שהסטודנט כתב בעצמו** ("Self-Written") לבין **ספריות חיצוניות שולבו כתלות** ("Building Blocks", BB). הפרק עושה את ההבחנה הזו במפורש: ראשית סוקר את המודולים שכתבתי בעצמי לפרויקט (ה־owner modules), ואז את הספריות החיצוניות שהשתמשתי בהן.

## ספריות שכתבתי (Self-Written)

הקוד שלי מאורגן בשבעה מודולים (קבצי Python). כל אחד מהם הוא **owner module** — בעלים יחיד על תת־מערכת אחת.

**[`servo.py`](../../servo.py) — בעלים על ה־PCA9685 והסרוואים.** מספק 6 פונקציות ציבוריות: `init()` שמאתחל את ה־PCA9685, קובע את ה־pulse range של DS3225 ל־500–2500µs ואת ה־actuation range ל־270°, ומחזיר אובייקט `ServoKit`. `move_pan(kit, angle, ramp=True)` ו־`move_tilt(kit, angle, ramp=True)` מבצעים clamp לטווח הבטוח [`PAN_MIN`, `PAN_MAX`] או [`TILT_MIN`, `TILT_MAX`] ושולחים את הפקודה ל־PCA9685. ה־`ramp` קובע אם התנועה תהיה חלקה (2° צעדים עם sleep של 50ms — לכיול ומרכוז) או מיידית (`ramp=False` — ללולאת המעקב, כדי לא לחסום). `center(kit)` מחזיר את שני הסרוואים למרכז המכויל (135°/160°). `cleanup(kit)` נקרא ב־finally של כל סקריפט ומחזיר את הסרוואים למרכז בטוח. `current_pan()` ו־`current_tilt()` מחזירים את הזווית האחרונה שנשלחה — דרושים ל־PID שצריך לדעת מאיפה להחיל את התיקון.

**[`camera.py`](../../camera.py) — בעלים על המצלמה.** שלוש פונקציות: `init(width=640, height=480, device_index=0)` שפותחת את ה־`cv2.VideoCapture(0)`, מגדירה את הרזולוציה, ומחזירה את האובייקט. `capture_frame(cap)` שקוראת פריים אחד ומחזירה אותו כמערך numpy של BGR. `release(cap)` שמשחרר את המצלמה. הפשטות של הקובץ הזה מסתירה את העובדה שהוא לקח שעות לכוון — בעיקר בגלל שהמעבר ממצלמת CSI ל־USB דרש לכתוב הכל מחדש בלי לשבור את ה־API.

**[`detector.py`](../../detector.py) — בעלים על אלגוריתם הזיהוי.** שתי פונקציות ציבוריות: `build_mask(frame)` שמבצעת את כל ה־pipeline (blur → BGR→HSV → inRange → erode → dilate) ומחזירה את המסכה הבינארית — שימושית ל־debugging ולכלי הכיול. `detect(frame)` שעוטפת את `build_mask` עם `findContours` + `moments`, מחזירה `(cx, cy)` או `None`. הקובץ מייבא רק `cv2`, `numpy`, ו־`config` — אין לו מושג שיש PCA9685 או סרוואים, וזה במכוון.

**[`tracker.py`](../../tracker.py) — בעלים על בקרי ה־PID.** שלוש פונקציות ציבוריות: `init()` שיוצרת שני בקרי `simple_pid.PID` עם הרווחים מ־`config.py` (`KP_PAN`, `KI_PAN`, `KD_PAN`, וכן לטילט) ומחזירה אותם כ־tuple. `update(pan_pid, tilt_pid, kit, target_pos)` שמבצעת איטרציה אחת של הלולאה: מקבלת את `target_pos` מה־detector, מחשבת את ה־error, מזינה את ה־PID, מקבלת תיקון, ושולחת ל־`servo.move_*`. גם מטפלת ב־Deadband (15px), ב־Coast Mode (1 שנייה עם דעיכה), וב־Recenter Mode (חזרה למרכז ב־2°/פריים). `stop(kit)` שמתפעלת את `servo.cleanup`. הקובץ הזה ארוך בערך 310 שורות — הוא ה"מוח" של המערכת.

**[`laser.py`](../../laser.py) — בעלים על GPIO18 של הלייזר.** ארבע פונקציות: `init()` שיוצרת `gpiozero.LED(18)` עם ביטחון מפורש שהפין יוצא LOW. `fire(laser_dev)` ו־`off(laser_dev)` שמרימים ומורידים את GPIO18. `cleanup(laser_dev)` שמכבה את הלייזר ומשחרר את ה־GPIO. החוקיות החשובה ביותר בקובץ הזה — שגם רשומה ב־`CLAUDE.md` כהזהרה — היא ששם המשתנה החייב להיות `laser_dev` ולא `laser`, כי `laser` מוצל על שם המודול ויגרום ל־AttributeError בקריאה הבאה ל־`laser.cleanup`.

**[`config.py`](../../config.py) — Single Source of Truth.** לא מודול שעובד עם חומרה אלא קובץ קבועים. מכיל את כל הערכים שכויילו אמפירית: `HSV_LOWER`, `HSV_UPPER`, `MIN_CONTOUR_AREA`, `FIRE_PIXEL_THRESHOLD`, רווחי PID (`KP_PAN`, `KI_PAN`, `KD_PAN` × 2 לטילט), `PID_OUTPUT_LIMIT`, `TRACKING_DEADBAND_PX`, ופרמטרי Coast (`COAST_MAX_FRAMES`, `COAST_DECAY`, `COAST_MIN_CORRECTION_DEG`) ו־Recenter (`RECENTER_AFTER_COAST`, `RECENTER_STEP_DEG`). הערכים מתועדים עם הסבר למה הם הערך שהם — לא רק "$K_p=0.017$" אלא גם "0.017 הוא הסוף של 8 איטרציות כיול; 0.05 רטט, 0.01 איטי, 0.02 מעט רועד, 0.017 חלק".

**[`control_panel.py`](../../control_panel.py) — GUI מבוסס tkinter שעוטף את הכל.** קובץ של ~650 שורות. בנוי מ־class אחת `ControlPanel` שיוצרת את ה־window, מסדרת אזורי כפתורים (Servo, Laser, Tools, System), ומתחזקת מצב מקומי. כל לחיצה על כפתור היא callback שקורא לפונקציה רלוונטית (`servo.init()`, `servo.center()`, `laser.fire()`, או `subprocess.Popen(["python3", "test_tracking.py"])`). יש pane של log שמציג את הפלט של ה־`logging` של כל המודולים, כך שהמפעיל רואה מה קורה בזמן אמת. יש lock על שני־עיסוקי-שעמדה־בו־זמנית (אסור להפעיל test_tracking כש־subprocess אחר רץ). יש כפתור Emergency Stop אדום בתחתית שמכבה את הלייזר ומרכז את הסרוואים.

בנוסף לאלה יש סקריפטי הפעלה שהם יותר "מנהלים" של ה־modules מאשר ספריות — `test_servo.py`, `test_laser.py`, `test_tracking.py`, `calibrate_servo.py`, `tune_detector.py`, ו־`main.py`. הם מתוארים בקצרה ב־§11 ובמלואו ב־§15.

## ספריות חיצוניות (Building Blocks)

ה־BB נחלקות ל־**ספריות apt** (חבילות הפצה של Raspberry Pi OS) ול־**ספריות pip** (מותקנות ב־venv מ־PyPI).

### apt — חבילות מערכת

- **`python3-opencv`** (cv2, גרסה ~4.6) — ספריית עיבוד תמונה ובינה חזותית. השימוש שלי: `cv2.VideoCapture` לקריאת פריימים מהמצלמה, `cv2.cvtColor` להמרת BGR→HSV, `cv2.GaussianBlur` להחלקה, `cv2.inRange` לזיהוי טווח HSV, `cv2.erode/dilate` לניקוי רעש מורפולוגי, `cv2.findContours` לחילוץ קונטורים, `cv2.moments` למרכז מסה. גם משמשת ב־`tune_detector.py` ו־`test_tracking.py` לחלונות הצגה (`cv2.imshow`, `cv2.namedWindow`, סליידרים `cv2.createTrackbar`).
- **`python3-numpy`** (numpy, גרסה ~1.24) — מערכי N־dimensional ופעולות וקטוריות מהירות עליהם. השימוש שלי: כל פריים שמוחזר מ־cv2 הוא `np.ndarray`, ו־`config.HSV_LOWER`/`HSV_UPPER` הם `np.array` של uint8. כל החישוב המתמטי הכבד בפועל מתבצע בתוך numpy/cv2 (C מהודר), לא ב־Python.
- **`python3-gpiozero`** (gpiozero, גרסה ~2.0) — ספרייה ידידותית למתחילים על GPIO של Raspberry Pi. השימוש שלי: `LED(18)` ל־GPIO18 של הלייזר, עם `.on()` ו־`.off()`. הספרייה עוטפת את `/sys/class/gpio/` של הקרנל בממשק נקי.

הסיבה ש־3 הספריות האלה מותקנות דרך apt ולא דרך pip — הן כבדות מאוד לקמפול, וה־Pi לוקח 30+ דקות לכל אחת. עדיף להשתמש בחבילות apt המוכנות, ולפצות ע"י ה־flag `--system-site-packages` שעובד ב־venv.

### pip — חבילות ב־venv

מותקנות דרך `pip install -r requirements.txt`:

- **`adafruit-circuitpython-pca9685`** — driver ל־PCA9685. מטפל בכל הרגיסטרים של השבב, חישוב duty cycle, תכיפויות. השימוש שלי דרך ServoKit שעוטף אותו.
- **`adafruit-circuitpython-servokit`** (`ServoKit`) — wrapper ברמה גבוהה יותר על PCA9685, מותאם לבקרת סרוואים. ממשק פשוט: `kit = ServoKit(channels=16, address=0x40)`, אחר־כך `kit.servo[0].angle = 135`. תומך ב־`set_pulse_width_range` ו־`actuation_range` שאני צריך כדי להגדיר את ה־DS3225 נכון.
- **`adafruit-blinka`** — שכבת תאימות ש"מדמה" את ה־CircuitPython על Pi רגיל. בלעדיה ה־adafruit-circuitpython-* לא היו עובדים. רץ אוטומטית ולא מצריך קוד שלי.
- **`simple-pid`** — ספרייה מינימליסטית של 200 שורות שמיישמת בקר PID. השימוש שלי: `PID(Kp, Ki, Kd, setpoint=0, output_limits=(-10, 10))`, אחר־כך `correction = pid(current_error)`. מטפלת בנושאים העדינים: time delta אמיתי בין קריאות, חישוב integral עם anti-windup, output clamping.
- **`tkinter`** — מובנה ב־Python 3.11 (חבילת `python3-tk` של apt). GUI toolkit וותיק אבל יציב. השימוש שלי: בניית ה־control panel.

### תיעוד צד שלישי

הקישורים הרשמיים לכל ספרייה רשומים בפרק §18 (ביבליוגרפיה). כל קוד שאני כותב משתמש ב־API הציבורי המתועד של הספריות בלבד — לא לקחתי קוד מתוך הספריות והעתקתי אותו לתוך מודולי הפרויקט.
