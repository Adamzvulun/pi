# 18. ביבליוגרפיה

הפרק מאגד את כל המקורות החיצוניים שסייעו בתכנון, בנייה, ולמידה
במהלך הפרויקט, מסודרים לפי קטגוריה. הצהרת מקוריות מלאה ב־§3.

---

## 18.1 תיעוד רשמי של ספריות תוכנה

### 18.1.1 OpenCV

**OpenCV Python Tutorials.** התיעוד הרשמי של ספריית הראייה
הממוחשבת. שימוש עיקרי בפרקים על:

- [Image Thresholding](https://docs.opencv.org/master/d7/d4d/tutorial_py_thresholding.html)
  — `cv2.inRange` ומשפחת הסף.
- [Morphological Transformations](https://docs.opencv.org/master/d9/d61/tutorial_py_morphological_ops.html)
  — `erode`, `dilate`, Opening, Closing.
- [Contour Detection](https://docs.opencv.org/master/d4/d73/tutorial_py_contours_begin.html)
  — `findContours`, `RETR_EXTERNAL`, `CHAIN_APPROX_SIMPLE`.
- [Image Moments](https://docs.opencv.org/master/dd/d49/tutorial_py_contour_features.html)
  — חישוב centroid דרך moments.

URL: [https://docs.opencv.org/master/d6/d00/tutorial_py_root.html](https://docs.opencv.org/master/d6/d00/tutorial_py_root.html)

### 18.1.2 NumPy

**NumPy Documentation.** ייצוג מערכי תמונה, פעולות וקטוריות.

URL: [https://numpy.org/doc/](https://numpy.org/doc/)

### 18.1.3 simple-pid

**simple-pid (PyPI).** ספריית PID מינימליסטית שמשמשת ב־`tracker.py`.
שימוש ב־`PID(Kp, Ki, Kd, setpoint, output_limits)`.

URL: [https://pypi.org/project/simple-pid/](https://pypi.org/project/simple-pid/)

מאגר GitHub: [https://github.com/m-lundberg/simple-pid](https://github.com/m-lundberg/simple-pid)

### 18.1.4 Adafruit CircuitPython ServoKit

**Adafruit CircuitPython ServoKit Library Reference.** API גבוה
לשליטה ב־PCA9685 מ־Python.

URL: [https://docs.circuitpython.org/projects/servokit/en/latest/](https://docs.circuitpython.org/projects/servokit/en/latest/)

מאגר GitHub: [https://github.com/adafruit/Adafruit_CircuitPython_ServoKit](https://github.com/adafruit/Adafruit_CircuitPython_ServoKit)

### 18.1.5 Adafruit Blinka

**Adafruit Blinka.** שכבת התאמה (compat shim) של CircuitPython
ל־Raspberry Pi.

URL: [https://github.com/adafruit/Adafruit_Blinka](https://github.com/adafruit/Adafruit_Blinka)

### 18.1.6 gpiozero

**gpiozero Documentation.** ספריית GPIO גבוהת־רמה ל־Raspberry Pi.

URL: [https://gpiozero.readthedocs.io/](https://gpiozero.readthedocs.io/)

### 18.1.7 tkinter

**Python tkinter Tutorial (python.org).** ספריית GUI סטנדרטית של
Python.

URL: [https://docs.python.org/3/library/tkinter.html](https://docs.python.org/3/library/tkinter.html)

---

## 18.2 גליונות נתונים (Datasheets)

### 18.2.1 PCA9685

**PCA9685 — 16-Channel, 12-bit PWM Fm+ I²C-Bus LED Controller.**
NXP Semiconductors.

מתועד בו: מבנה רגיסטרים, פרוטוקול I²C, חישוב prescaler לתדר רצוי.

URL: [https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf)

### 18.2.2 IRLZ44N MOSFET

**IRLZ44N — HEXFET Power MOSFET, N-Channel, Logic Level.**
Infineon (לשעבר International Rectifier).

מתועד בו: $V_{GS(th)}$, $R_{DS(on)}$, גרפים של $I_D$ כפונקציה של
$V_{GS}$.

URL: [https://www.infineon.com/dgdl/Infineon-IRLZ44N-DataSheet-v01_01-EN.pdf](https://www.infineon.com/dgdl/Infineon-IRLZ44N-DataSheet-v01_01-EN.pdf)

### 18.2.3 LM2596

**LM2596 — Simple Switcher Power Converter, 150 kHz, 3A
Step-Down Voltage Regulator.** Texas Instruments.

מתועד בו: עקרון פעולה של buck converter, חישובי יעילות, סכמת
מעגל מומלצת.

URL: [https://www.ti.com/lit/ds/symlink/lm2596.pdf](https://www.ti.com/lit/ds/symlink/lm2596.pdf)

### 18.2.4 DS3225

**DS3225 25 kg Digital Servo Motor.** DSServo.

מתועד בו: טווח PWM (500–2500 µs), מומנט, מהירות, זרם stall.

מקור: דף המוצר אצל יצרני סרוו ב־Aliexpress / AmazonAU; ה־datasheet
המקורי אינו זמין באופן רשמי בעברית, אבל הספציפיקציות מאוחדות עם
מוצרי טייוואן/סין דומים.

### 18.2.5 BCM2711 (Raspberry Pi 4 SoC)

**Broadcom BCM2711 — ARM Cortex-A72 Quad-Core Application Processor.**
Raspberry Pi Foundation.

URL: [https://datasheets.raspberrypi.com/bcm2711/bcm2711-peripherals.pdf](https://datasheets.raspberrypi.com/bcm2711/bcm2711-peripherals.pdf)

### 18.2.6 LifeCam HD-3000

**Microsoft LifeCam HD-3000 Product Page.** Microsoft.

הספציפיקציה הטכנית המלאה (אורך גל, חיישן CMOS, פורמטים נתמכים)
זמינה ב־USB Device descriptor של ה־USB ID `045e:0779`.

URL: [https://www.microsoft.com/accessories/en-us/products/webcams/lifecam-hd-3000/t3h-00011](https://www.microsoft.com/accessories/en-us/products/webcams/lifecam-hd-3000/t3h-00011)

---

## 18.3 חומרי לימוד והדרכות

### 18.3.1 SparkFun

- **I²C Tutorial** — הסבר אינטראקטיבי על פרוטוקול I²C.
  [https://learn.sparkfun.com/tutorials/i2c](https://learn.sparkfun.com/tutorials/i2c)

- **Transistors / MOSFETs Tutorial** — מבוא לטרנזיסטורים ומתגי
  MOSFET, כולל Low-Side לעומת High-Side switching.
  [https://learn.sparkfun.com/tutorials/transistors](https://learn.sparkfun.com/tutorials/transistors)

- **Pulse-Width Modulation Tutorial** — הסבר על PWM ושימושיו.
  [https://learn.sparkfun.com/tutorials/pulse-width-modulation](https://learn.sparkfun.com/tutorials/pulse-width-modulation)

### 18.3.2 Adafruit

- **16-Channel PWM / Servo HAT for Raspberry Pi Guide** — הדרכה
  רשמית של Adafruit על שימוש ב־PCA9685 עם Raspberry Pi.
  [https://learn.adafruit.com/adafruit-16-channel-pwm-slash-servo-hat-for-raspberry-pi](https://learn.adafruit.com/adafruit-16-channel-pwm-slash-servo-hat-for-raspberry-pi)

### 18.3.3 Raspberry Pi

- **pinout.xyz** — מפת פינים GPIO של ה־Pi, אינטראקטיבית. שימוש
  בכל פעם שנדרש לוודא לאיזה פין פיזי שייכת כתובת BCM נתונה.
  [https://pinout.xyz](https://pinout.xyz)

- **Raspberry Pi Documentation** — תיעוד רשמי של ה־Pi, מערכת
  ההפעלה, וההגדרות.
  [https://www.raspberrypi.com/documentation/](https://www.raspberrypi.com/documentation/)

### 18.3.4 Wikipedia

- **PID Controller** — תיאוריה מקיפה של בקרי PID.
  [https://en.wikipedia.org/wiki/PID_controller](https://en.wikipedia.org/wiki/PID_controller)

- **HSV Color Space** — תיאוריה ויזואלית של מרחב הצבע HSV.
  [https://en.wikipedia.org/wiki/HSL_and_HSV](https://en.wikipedia.org/wiki/HSL_and_HSV)

- **Single Responsibility Principle** — עיקרון הנדסת תוכנה המנחה
  את ארכיטקטורת הקוד (ראו §11.6).
  [https://en.wikipedia.org/wiki/Single-responsibility_principle](https://en.wikipedia.org/wiki/Single-responsibility_principle)

- **Pulse-Width Modulation** — הגדרה כללית של PWM.
  [https://en.wikipedia.org/wiki/Pulse-width_modulation](https://en.wikipedia.org/wiki/Pulse-width_modulation)

- **I²C** — היסטוריה ומבנה של פרוטוקול I²C.
  [https://en.wikipedia.org/wiki/I%C2%B2C](https://en.wikipedia.org/wiki/I%C2%B2C)

- **MOSFET** — מבנה ותפעול של טרנזיסטור־שדה.
  [https://en.wikipedia.org/wiki/MOSFET](https://en.wikipedia.org/wiki/MOSFET)

- **Buck Converter** — עקרון פעולה של ממיר באק.
  [https://en.wikipedia.org/wiki/Buck_converter](https://en.wikipedia.org/wiki/Buck_converter)

---

## 18.4 דיונים בקהילה (Forums)

- **Electronics Stack Exchange** — שאלות וטיפים על MOSFET switching,
  Gate pulldowns, Low-Side לעומת High-Side.
  [https://electronics.stackexchange.com](https://electronics.stackexchange.com)

- **Raspberry Pi Forums** — דיונים על USB UVC drivers, GPIO
  quirks, cron jobs.
  [https://forums.raspberrypi.com](https://forums.raspberrypi.com)

- **Stack Overflow** — שאלות תוכנה כלליות (Python, OpenCV, tkinter).
  [https://stackoverflow.com](https://stackoverflow.com)

---

## 18.5 כלי AI

לפי הצהרת המקוריות ב־§3, כלי AI שימשו כעוזרי עבודה:

- **Anthropic Claude** — Claude Code CLI לעריכת קוד, ספר פרויקט.
  [https://www.anthropic.com/claude](https://www.anthropic.com/claude)

- **OpenAI ChatGPT** — לשאלות אד־הוק ולאימות הסברים.
  [https://chat.openai.com](https://chat.openai.com)

השימוש בכלים האלה תועד בפתיחות ב־§3.5. הם לא מהווים מקור עיקרי
לידע — כל הסבר נבדק בתיעוד הרשמי לפני יישום.

---

## 18.6 מאגר הקוד של הפרויקט

**Adamzvulun/pi (GitHub).** המאגר הציבורי של הפרויקט. כולל את הקוד
המלא, היסטוריית commits, תיעוד טכני, וספר הפרויקט הזה.

URL: [https://github.com/Adamzvulun/pi](https://github.com/Adamzvulun/pi)

---

## 18.7 תיעוד פנימי במאגר

קישורים פנימיים — קבצים בתוך המאגר:

| קובץ | תוכן |
|---|---|
| [`CLAUDE.md`](../../CLAUDE.md) | קונטקסט מלא של הפרויקט להעברה למפתחים עתידיים |
| [`HANDOFF.md`](../../HANDOFF.md) | מצב נוכחי ב־TL;DR |
| [`CHANGELOG.md`](../../CHANGELOG.md) | היסטוריית פיתוח session-by-session |
| [`docs/operating-guide.md`](../../docs/operating-guide.md) | מדריך הפעלה מעשי |
| [`docs/calibration.md`](../../docs/calibration.md) | ערכים מכוילים (סרוו, HSV, PID) |
| [`docs/circuit-diagram.md`](../../docs/circuit-diagram.md) | תרשימי מערכת ב־Mermaid |
| [`docs/wiring.md`](../../docs/wiring.md) | מצב חיווט פיזי |
| [`docs/setup-pi.md`](../../docs/setup-pi.md) | התקנה ראשונית של ה־Pi |
| [`docs/plan/phase-*.md`](../../docs/plan/) | תיעוד פר־שלב פיתוח |
| [`problems/001-servo-power.md`](../../problems/001-servo-power.md) | בעיית מתח MB-102 (פתורה) |
| [`problems/002-laser-dead.md`](../../problems/002-laser-dead.md) | בעיית הדיודה (פתורה לאחר החלפה) |

---

## 18.8 מקורות שנשקלו ולא נכללו

המקורות הבאים נשקלו אך נמצאו לא רלוונטיים או overkill לפרויקט,
ולכן לא בשימוש:

- **ROS / ROS 2 Documentation** — תיעוד מקיף לרובוטיקה אקדמית.
  נשקל ונדחה (§7.5 ו־§16.7.2) — overkill לפרויקט יחיד־רכיב.
- **MATLAB / Simulink** — סביבת סימולציה לבקרה. נשקלה לכיוון PID
  אך הוחלפה בכיוון אמפירי ישיר על החומרה.
- **ImageNet / COCO** — מאגרי תמונות לאימון נוירונים. רלוונטיים
  רק לשדרוג עתידי (§16.2.1).
- **Kalman Filter Tutorial** — נשקל ל־§16.7.5 ונדחה לטובת
  Deadband + Coast.

---

## 18.9 הערה על שלמות הרשימה

המקורות לעיל הם **אלה שהיו רלוונטיים ברמה מספיקה כדי להופיע בקוד
או בעיצוב**. במהלך הפיתוח גוללו עשרות עמודי forums, GitHub
issues, ו־StackExchange threads — לא כולם נשמרו או תועדו. המאמץ
הושקע בלהבטיח שכל **החלטה תכנונית** מבוססת על מקור שאפשר לאמת,
ולא ש**כל קישור שנקרא** מתועד.

הקוד הסופי במאגר GitHub הוא ה־**ground truth** — אם נדרש הסבר
מדויק של "למה כתבת ככה", התשובה היא בתגובות בקוד או בקבצי
`problems/`, לא בביבליוגרפיה.
