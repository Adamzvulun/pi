# נספח ב' — מקורות וקישורים

רשימת המקורות שסייעו בתכנון, בנייה, ולמידה לאורך הפרויקט. מסודרת
לפי קטגוריה.

---

## תיעוד רשמי של ספריות

- **OpenCV Python Tutorials** — תיעוד מקיף של ספריית הראייה הממוחשבת
  המרכזית בפרויקט. שימוש עיקרי בפרקים על Image Thresholding, Morphological
  Transformations, Contour Detection, Image Moments.
  [https://docs.opencv.org/master/d6/d00/tutorial_py_root.html](https://docs.opencv.org/master/d6/d00/tutorial_py_root.html)

- **simple-pid (PyPI)** — תיעוד הספרייה המשמשת ב־`tracker.py` לבקרת
  PID דו־צירית.
  [https://pypi.org/project/simple-pid/](https://pypi.org/project/simple-pid/)

- **Adafruit CircuitPython ServoKit** — תיעוד ה־API לשליטה ב־PCA9685
  מ־Python.
  [https://docs.circuitpython.org/projects/servokit/](https://docs.circuitpython.org/projects/servokit/)

- **Adafruit Blinka** — שכבת התאמה (compat shim) של CircuitPython
  ל־Linux/Raspberry Pi.
  [https://github.com/adafruit/Adafruit_Blinka](https://github.com/adafruit/Adafruit_Blinka)

- **gpiozero** — ספריית GPIO גבוהת־רמה ל־Raspberry Pi.
  [https://gpiozero.readthedocs.io/](https://gpiozero.readthedocs.io/)

- **NumPy** — ספריית מערכים מתמטיים.
  [https://numpy.org/doc/](https://numpy.org/doc/)

- **tkinter** — ספריית GUI סטנדרטית של Python.
  [https://docs.python.org/3/library/tkinter.html](https://docs.python.org/3/library/tkinter.html)

## גליונות נתונים (Datasheets)

- **DS3225 Digital Servo** — מפרט הסרוו המשמש בפאן וטילט.
  זרם stall, טווח PWM, מומנט.

- **PCA9685 16-Channel 12-bit PWM I²C-Bus LED Controller** — מפרט שבב
  הדרייבר PWM.
  NXP Semiconductors, [https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf)

- **LM2596 Step-Down Voltage Regulator** — מפרט הבאק־קונברטר המשמש
  לאספקת חשמל לסרוו.
  Texas Instruments, [https://www.ti.com/lit/ds/symlink/lm2596.pdf](https://www.ti.com/lit/ds/symlink/lm2596.pdf)

- **IRLZ44N N-Channel Power MOSFET** — מפרט ה־MOSFET המשמש למיתוג הלייזר.
  Infineon, [https://www.infineon.com/dgdl/Infineon-IRLZ44N-DataSheet-v01_01-EN.pdf](https://www.infineon.com/dgdl/Infineon-IRLZ44N-DataSheet-v01_01-EN.pdf)

## חומרי לימוד ועזרה

- **SparkFun I²C Tutorial** — הסבר אינטראקטיבי על פרוטוקול I²C.
  [https://learn.sparkfun.com/tutorials/i2c](https://learn.sparkfun.com/tutorials/i2c)

- **SparkFun Transistors / MOSFETs Tutorial** — מבוא לטרנזיסטורים
  ומתגי MOSFET.
  [https://learn.sparkfun.com/tutorials/transistors](https://learn.sparkfun.com/tutorials/transistors)

- **Adafruit 16-Channel PWM Servo HAT Guide** — הדרכה רשמית של
  Adafruit על שימוש ב־PCA9685 עם Raspberry Pi.
  [https://learn.adafruit.com/adafruit-16-channel-pwm-slash-servo-hat-for-raspberry-pi](https://learn.adafruit.com/adafruit-16-channel-pwm-slash-servo-hat-for-raspberry-pi)

- **Raspberry Pi Pinout** — מפת פינים GPIO של ה־Pi, אינטראקטיבית.
  [https://pinout.xyz](https://pinout.xyz)

- **Wikipedia — PID Controller** — תיאוריה מקיפה של בקרי PID.
  [https://en.wikipedia.org/wiki/PID_controller](https://en.wikipedia.org/wiki/PID_controller)

- **Wikipedia — HSV Color Space** — תיאוריה ויזואלית של מרחב הצבע HSV.
  [https://en.wikipedia.org/wiki/HSL_and_HSV](https://en.wikipedia.org/wiki/HSL_and_HSV)

- **Single Responsibility Principle (Wikipedia)** — עיקרון הנדסת תוכנה
  המנחה את ארכיטקטורת הקוד.
  [https://en.wikipedia.org/wiki/Single-responsibility_principle](https://en.wikipedia.org/wiki/Single-responsibility_principle)

## דיונים בקהילה

- **Stack Exchange — Electrical Engineering** — שאלות וטיפים על MOSFET
  switching, gate pulldowns, low-side vs high-side switching.
  [https://electronics.stackexchange.com](https://electronics.stackexchange.com)

- **Raspberry Pi Forums** — דיונים על USB UVC drivers, gpio quirks,
  cron jobs.
  [https://forums.raspberrypi.com](https://forums.raspberrypi.com)

## מאגר הקוד של הפרויקט

- **Adamzvulun/pi (GitHub)** — מאגר Git הפרטי של הפרויקט. הקוד הסופי,
  התיעוד, ההיסטוריה.
  [https://github.com/Adamzvulun/pi](https://github.com/Adamzvulun/pi)

## תיעוד פנימי (במאגר הפרויקט)

קישורים פנימיים — ראה את הקבצים בתוך המאגר:

- `CLAUDE.md` — קונטקסט מלא של הפרויקט.
- `HANDOFF.md` — מצב נוכחי ב־TL;DR.
- `CHANGELOG.md` — היסטוריית פיתוח, session-by-session.
- `docs/operating-guide.md` — מדריך הפעלה מעשי.
- `docs/calibration.md` — ערכים מכוילים (סרוו, HSV, PID).
- `docs/circuit-diagram.md` — תרשימי מערכת ב־Mermaid.
- `docs/wiring.md` — מצב חיווט פיזי.
- `docs/setup-pi.md` — התקנה ראשונית של ה־Pi.
- `docs/plan/phase-*.md` — תיעוד פר־שלב פיתוח.
- `problems/001-servo-power.md` — בעיית מתח ה־MB-102 (פתורה).
- `problems/002-laser-dead.md` — בעיית הדיודה (פתורה לאחר החלפה).

---

## הצהרה על שימוש בכלי AI

חלקים מהפיתוח של הפרויקט (כולל יצירת ספר הפרויקט הזה) נעזרו בכלי AI
מסוג Large Language Model (Claude/ChatGPT) — הן ליצירת תוכן, ליישום
תכניות עבודה, ולתיעוד. כל החלטה תכנונית, כל בחירה אלגוריתמית, וכל
ניסוי מעשי בוצעו וננתחו על־ידי הסטודנט. ה־AI שימש ככלי עזר — בדומה
לחיפוש בגוגל או לקריאה בויקיפדיה — ולא כמקור עיקרי או יחיד.

הקוד עצמו פתוח לבחינה במאגר ב־GitHub. כל commit מתועד עם הסבר ה־
"למה" של כל שינוי.
