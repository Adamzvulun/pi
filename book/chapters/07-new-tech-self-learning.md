# פרק 7 — נושאים חדשים ולמידה עצמאית

המחוון מבקש: "התמודדות הסטודנט עם נושאים חדשים. למידה עצמאית. שימוש
ברכיבים ובפרוטוקולים עדכניים." הפרק מתעד את הטכנולוגיות, הספריות
והעקרונות שהיו חדשים בתחילת הפרויקט, ואת דרך הלימוד של כל אחד.

## 7.1 נקודת ההתחלה

הידע הקודם:

- **Python** ברמה בסיסית — תחביר, פונקציות, מחלקות, ספריות סטנדרטיות.
- **מתמטיקה** ברמת 5 יחידות.
- **Git** ברמת `add/commit/push` שטחית.

הנושאים שלא היו מוכרים בכלל לפני הפרויקט:

- I²C
- PWM
- מייצב מתח באק־קונברטר
- MOSFET כמתג
- OpenCV
- מרחב צבע HSV
- בקרת PID
- Linux ברמת SSH ו־cron
- workflow של CI/CD אוטומטי

זאת אומרת שרוב העבודה היא תוצר של למידה עצמאית — מהבחירה הטכנולוגית,
דרך החלטות אלגוריתמיות, ועד דפוסי הקוד.

## 7.2 רכיבים ופרוטוקולים חדשים

### 7.2.1 פרוטוקול I²C

#### מה זה

פרוטוקול תקשורת סינכרוני שפותח ב־Philips/NXP בשנות ה־80. שני חוטי
אות (SDA, SCL), מאפשר עד 127 התקנים על אותו אוטובוס.

#### מה היה חדש

חיבור לחיישנים בדרך כלל פירושו "חוט לכל אות". I²C הוא הדפוס הראשון
שבו שלושה חוטים (SDA, SCL, GND) משותפים לכל ההתקנים יחד, וה־"כתובת"
היא שמייחדת כל אחד.

#### איך התבצעה הלמידה

1. קריאת ה־[I²C tutorial של Sparkfun](https://learn.sparkfun.com/tutorials/i2c).
2. הרצת `i2cdetect -y 1` והבנת הפלט — איך הכתובת `0x40` מופיעה בגריד.
3. קריאת ה־datasheet של PCA9685 בפרק "I²C Bus Interface".
4. דיבוג של בעיית "I/O error" שהוביל להבנת חשיבות GND משותף.

### 7.2.2 PWM (Pulse-Width Modulation)

#### מה זה

טכניקה לקידוד "מתח אנלוגי" באות דיגיטלי — אות פעיל בחלק מהזמן
ולא־פעיל בחלק. ה־Duty Cycle (היחס) מקודד את המידע.

עבור סרוו, ה־PWM פועל ב־50Hz (תקופה 20ms), כאשר משך הפולס בתוך
התקופה (500–2500µs) קובע את הזווית.

#### מה היה חדש

ההנחה האינטואיטיבית היא שסרוו מקבל "מתח של זווית X" — מתח אנלוגי.
בפועל הוא מקבל **רצף פולסים דיגיטליים** עם תזמון קפדני.

#### איך התבצעה הלמידה

1. תיעוד של DS3225.
2. הפרק על PWM ב־[Adafruit servo HAT tutorial](https://learn.adafruit.com/adafruit-16-channel-pwm-slash-servo-hat-for-raspberry-pi).
3. ניסויי כיול עם `calibrate_servo.py` — הבנת היחס בין
   `kit.servo[0].angle = 100` לבין פולס PWM של 1130µs.

### 7.2.3 מייצב מתח באק־קונברטר

#### מה זה

ממיר מתח שטף־ירידה — מקבל מתח גבוה ומוציא מתח נמוך, ביעילות גבוהה
(85%+). שבב פנימי פותח וסוגר את מתח הכניסה בתדר גבוה (~150kHz),
סליל וקבל מחליקים את האות לזרם DC.

#### מה היה חדש

ההנחה הקודמת הייתה שכל מייצב הוא לינארי (כמו 7805) — ממיר את ההפרש
לחום. ההבחנה היא ששני סוגים שונים קיימים, ושהבחירה משפיעה דרמטית
על יעילות ההרכבה.

#### איך התבצעה הלמידה

1. בעיה 001 (MB-102 לא מספק זרם מספיק) הכריחה ירידה לתיעוד — מה זה
   מייצב, איך מודדים זרם מקסימלי, ולמה לינארי "שורף" הרבה חום.
2. קריאת [LM2596 datasheet](https://www.ti.com/lit/ds/symlink/lm2596.pdf).
3. סרטון GreatScott על buck מול linear (YouTube, ~10 דקות).

### 7.2.4 MOSFET כמתג

#### מה זה

Metal-Oxide-Semiconductor Field-Effect Transistor — טרנזיסטור־שדה.
בהקשר של מיתוג: מתח על ה־Gate מבקר זרם בין Drain ל־Source. כאשר
ה־Gate חיובי (מעל סף ההדלקה), הזרם זורם.

#### מה היה חדש

ידע קודם של "טרנזיסטור" כמושג כללי, אבל לא שיש שני סוגים עיקריים
(BJT לעומת MOSFET) ושה־MOSFET ייעודי למיתוג מהיר וביעיל.

#### איך התבצעה הלמידה

1. קריאת [IRLZ44N datasheet](https://www.irf.com/product-info/datasheets/data/irlz44n.pdf).
2. הסבר ויזואלי של low-side switching ב־
   [SparkFun MOSFET tutorial](https://learn.sparkfun.com/tutorials/transistors).
3. בנייה פיזית — חיווט המעגל עם נגדים פיזיים, מדידת מתח על ה־Gate
   עם ובלי הפעלת GPIO.
4. הבנת חשיבות ה־Pulldown אחרי דיון על "floating gate" ב־
   StackExchange.

### 7.2.5 Pi Camera CSI מול USB UVC

#### מה זה

שני פרוטוקולים שונים לחיבור מצלמות ל־Pi:

- **CSI** (Camera Serial Interface) — חיבור ייעודי דרך פס ribbon.
  משולב עם השבב, ביצועים גבוהים, מוגבל לחומרה ספציפית.
- **UVC** (USB Video Class) — תקן גנרי דרך USB. עובד עם כל מצלמה
  תואמת UVC.

#### מה היה חדש

ההנחה הראשונית הייתה שכל מצלמה מתחברת באותה צורה. היתרון של USB
הוא **גנריות** — אותו דרייבר עובד עם כל מצלמה שעוברת את הסטנדרט.

#### איך התבצעה הלמידה

1. ניסיון להפעיל מצלמת Pi 5 על Pi 4 — כשל בגלל חוסר תאמת מחבר.
2. הבנת UVC מתוך תיעוד הקרנל של Linux (`lsmod | grep uvc`).
3. הצלחה ראשונה עם `cv2.VideoCapture(0)` בלי שום installation
   נוסף — דוגמה לעוצמה של פרוטוקולים תקניים.

## 7.3 ספריות תוכנה חדשות

### 7.3.1 CircuitPython + Blinka

#### מה זה

**CircuitPython** היא וריאנט של Python שפותח ב־Adafruit למיקרובקרים
קטנים. ה־API פשוט וסטנדרטי לעבודה עם חומרה — `board`, `digitalio`,
`busio`, וכו'.

**Blinka** היא שכבת התאמה שמסטרבת את ה־CircuitPython על Raspberry
Pi — מאפשרת לרוץ קוד שנכתב ל־CircuitPython גם על ה־Pi בלי שינוי.

#### מה היה חדש

ההנחה הקודמת — שכל פלטפורמה דורשת קוד נפרד. Blinka הוא הדפוס
הראשון שמייצג "כותבים פעם אחת, רץ בכמה פלטפורמות" בעולם החומרה.

#### איך התבצעה הלמידה

1. תיעוד התקנה של [Adafruit ServoKit](https://learn.adafruit.com/16-channel-pwm-servo-driver/library-reference).
2. עיון בקוד של `adafruit-circuitpython-servokit` ובאיך הוא משתמש
   ב־`board.SCL`, `board.SDA`.
3. הבנה ש־`adafruit-blinka` הוא ה־shim שמספק את האובייקטים האלה
   על Raspberry Pi.

### 7.3.2 OpenCV (`cv2`)

#### מה זה

ספריית computer vision הפופולרית. מקיפה את כל זיהוי התמונה, טיפול
בווידאו, וזיהוי אובייקטים. פיתוח של Intel/Itseez/OSVL.

#### מה היה חדש

ההנחה הקודמת הייתה שזה כלי "לזיהוי דברים" באופן כללי. בפועל זו
ספרייה עם מעל 2,500 פונקציות שעוסקות בכל היבט של עיבוד תמונה.

#### איך התבצעה הלמידה

1. [Official OpenCV Python Tutorials](https://docs.opencv.org/master/d6/d00/tutorial_py_root.html).
2. ספציפית הפרקים על:
   - Image Thresholding (`inRange`)
   - Morphological Transformations (`erode`, `dilate`)
   - Contour Detection (`findContours`)
   - Image Moments (`moments`)
3. כתיבת `detector.py` בהדרגה — דיבוג כל שלב בנפרד.
4. הרצת `tune_detector.py` עם trackbars — קישור ויזואלי בין הקוד
   להבנה.

### 7.3.3 NumPy

#### מה זה

ספריית מערכים מתמטיים. בליבת כל ה־scientific computing של Python.

#### מה היה חדש

ההנחה הקודמת — שמספיק להשתמש ברשימות Python. מערכי NumPy:

- מאוחסנים ב־memory רציפה (cache-friendly).
- מבצעים פעולות מטריצה ב־C ולא בלולאה של Python.
- הם הפורמט הטבעי של תמונות ב־OpenCV.

#### איך התבצעה הלמידה

1. שימוש ב־OpenCV — כל תמונה היא `numpy.ndarray`.
2. ערכי `HSV_LOWER` ו־`HSV_UPPER` הם `np.array(...)` ולא רשימות.
3. בדיקת `frame.shape`, `frame.dtype` כדי להבין מבנה.

### 7.3.4 simple_pid

#### מה זה

ספריית PID מינימליסטית ל־Python. API:
`pid = PID(Kp, Ki, Kd, setpoint=target)`, ואז `output = pid(measurement)`.

#### מה היה חדש

ההנחה הראשונית — שצריך לכתוב את ה־PID מאפס (מה שבפועל היה מסובך
ולא יציב).

#### איך התבצעה הלמידה

1. חיפוש ב־PyPI אחרי "pid python", מציאת
   [simple-pid](https://pypi.org/project/simple-pid/) עם מספר רב
   של downloads ותיעוד טוב.
2. תיעוד PyPI עצמו מספיק לשימוש בסיסי.
3. דיבוג של `output_limits` בעת בעיות יציבות — הבנת anti-windup.

### 7.3.5 gpiozero

#### מה זה

ספריית GPIO גבוהת־רמה ל־Raspberry Pi. API פשוט:
`led = LED(18); led.on()` במקום ה־API הנמוך של RPi.GPIO.

#### מה היה חדש

דוגמאות RPi.GPIO ב־tutorials של hobby ארוכות עם הרבה boilerplate
(`setmode(GPIO.BCM)`, `setup(18, GPIO.OUT)`, וכו'). gpiozero מסתיר
את כל זה.

#### איך התבצעה הלמידה

1. תיעוד של [gpiozero](https://gpiozero.readthedocs.io/).
2. השוואת קוד — `gpiozero.LED` מציע גם `is_lit`, `blink()`, וכו'.
3. כתיבת `laser.py` — 4 שורות במקום ~15 שדרושות ב־RPi.GPIO.

### 7.3.6 tkinter

#### מה זה

ספריית GUI סטנדרטית של Python — מבוססת Tk. בנייה של חלונות שולחן
עבודה בלי תלויות חיצוניות.

#### מה היה חדש

הצורך בלוח בקרה גרפי לא היה ברור בהתחלה. כשפעולות במערכת התרבו
וטעויות שורת פקודה התחילו להיות יקרות — GUI הפך נחוץ.

#### איך התבצעה הלמידה

1. [Tkinter Tutorial של Python.org](https://docs.python.org/3/library/tkinter.html).
2. חלון מינימלי עם 2 כפתורים, ואז גידול הדרגתי.
3. סוגיות מתקדמות:
   - הרצת פעולות ארוכות (`subprocess.Popen`) בלי לחסום את ה־GUI.
   - העברת logs ל־scrolledtext widget (queue + tick).
   - טיפול ב־window close (`WM_DELETE_WINDOW`).

## 7.4 דפוסי קוד

### 7.4.1 Owner Module Pattern

#### מה זה

מודול אחד אחראי על משאב אחד. אף מודול אחר לא מייבא את ספריית
החומרה ישירות — רק את ה־API של ה־owner.

#### איך התבצעה הלמידה

1. הדפוס התגבש לאחר באג: בכמה קבצים יובא `adafruit_servokit`
   ישירות. כאשר נדרש לעדכן הגדרה (טווח 270° במקום 180°), היה צריך
   לעדכן בכל מקום בנפרד. סיכון לשגיאה.
2. מציאת מאמר ה־[Single Responsibility Principle](https://en.wikipedia.org/wiki/Single-responsibility_principle)
   בויקיפדיה.
3. refactor: כל גישה ל־ServoKit עוברת דרך `servo.py`. שינוי הפך פשוט.

### 7.4.2 Single Source of Truth — `config.py`

#### מה זה

כל קבוע שניתן לכיול חי במקום אחד.

#### איך התבצעה הלמידה

1. באג: כיוון `HSV_LOWER` ב־`detector.py` בלי לעדכן ב־
   `tune_detector.py`. שני המודולים החזירו תוצאות שונות.
2. refactor: יצירת `config.py` עם כל הקבועים; שני המודולים מייבאים
   ממנו.

### 7.4.3 Defensive Programming (`try/finally`, clamping, Pulldown)

#### מה זה

ההנחה שדברים יכולים להשתבש — ובנייה של הקוד כך שגם בתקלה החומרה
לא תתקלקל.

#### איך התבצעה הלמידה

1. ניסיון של `Ctrl+C` באמצע `test_servo.py` השאיר את הסרוו במצב
   לא מוגדר. בהפעלה הבאה הוא קפץ קפיצה חדה.
2. הוספת `try/finally` בכל סקריפט — `servo.cleanup` רץ גם בעת
   תקלה.

### 7.4.4 Lazy Initialization

#### מה זה

לא לאתחל משאב יקר עד שיש צורך אמיתי.

#### איך התבצעה הלמידה

1. הגרסה הראשונה של ה־GUI אתחלה את כל החומרה בעת פתיחת החלון. שתי
   בעיות: זמן המתנה עד שהחלון נפתח, ומשאבים תפוסים גם אם המשתמש לא
   מתכוון להזיז סרוו.
2. refactor: כפתור "Initialize hardware" שמאתחל רק על בקשה.

## 7.5 Linux + GitHub Workflow

### 7.5.1 SSH

חיבור remote ל־Pi. הליך הלמידה כלל: ייצור key pair (`ssh-keygen`),
העלאת המפתח לשרת (`ssh-copy-id`), חיבור כדרישת מינימום ל־dev work.

### 7.5.2 cron

לוח זמנים אוטומטי. הוקם cron job ב־Pi שמבצע `git pull` כל דקה —
workflow של "עורכים, דוחפים, ה־Pi מקבל לבד".

### 7.5.3 VNC

שיתוף שולחן עבודה מרחוק. הוקם VNC Server על ה־Pi לבדיקות שדורשות
חלון OpenCV.

### 7.5.4 Git מעבר ל־`add/commit/push`

- **Branches** עדיין לא בשימוש, רק `main`.
- **commit messages** עם פרפיקס כמו `feat:`, `fix:`, `docs:` עם
  הסבר ה־why ב־body.
- **CHANGELOG.md** כתיעוד חיצוני, לא רק `git log`.

## 7.6 מתודולוגיה ללמידת טכנולוגיה חדשה

מעבר לטכנולוגיות הבודדות, התגבשה מתודה ללמידת טכנולוגיה חדשה:

1. **התחלה עם official docs.** ה־README של ספרייה ב־GitHub, ה־
   datasheet של רכיב. לא tutorials של פורומים — הם לעיתים קרובות
   מיושנים.
2. **דוגמה מינימלית קודם.** "Hello world" של כל ספרייה לפני שילוב
   בקוד הראשי. למשל, `blink LED` עם gpiozero לפני קוד הלייזר.
3. **דיבוג מעט־מעט.** אם משהו לא עובד — לא מנסים לתקן שלוש שורות
   בו זמנית. שורה אחת, ניסוי, שורה הבאה.
4. **תיעוד תוך כדי**, לא אחרי. כל בעיה שנפתרה — שורה ב־CHANGELOG.md
   או קובץ ב־problems/.
5. **שאלת ChatGPT/Claude כעוזר**, לא כמקור עיקרי. כל הסבר נבדק
   בתיעוד הרשמי לפני יישום.
6. **בנייה פיזית.** קריאה על MOSFET לא מספיקה — חיבור המעגל,
   הפעלה, ומדידה הם מה שמבסס את ההבנה.

## 7.7 קישור לתיעוד עצמי

המקורות העיקריים שגוללו במהלך הפרויקט (כולם נצברו ב־[`book/references.md`](../references.md)):

- **Adafruit:** תיעוד של PCA9685, ServoKit, gpiozero.
- **OpenCV:** Python tutorials הרשמיים.
- **Datasheets:** DS3225, IRLZ44N, LM2596, PCA9685.
- **Raspberry Pi:** pinout.xyz, `raspi-config`, `i2cdetect`.
- **simple-pid:** PyPI page.
- **Stack Exchange** (electronics, raspberrypi): שאלות על Pulldown
  ו־wire-routing.
