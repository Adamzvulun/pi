# 18. ביבליוגרפיה

הפרק מאגד את כל המקורות שנעזרתי בהם במהלך הפרויקט: דאטה־שיטים של רכיבי חומרה, תיעוד רשמי של ספריות תוכנה, סדרת מאמרים/tutorials שעזרו ללמוד מושגים חדשים, ומאגרי קוד פתוח שהשפיעו על תכנון. הקישורים נכונים נכון למאי 2026.

## דאטה־שיטים של רכיבי חומרה

1. **Raspberry Pi 4 Model B — Datasheet רשמי.** Raspberry Pi Foundation. [https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-datasheet.pdf](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-datasheet.pdf)

2. **DS3225 Digital Servo — Datasheet.** Towerpro / Generic. [https://www.dfrobot.com/product-1612.html](https://www.dfrobot.com/product-1612.html) — מפרט הסרוואים שבפרויקט (טווח 270°, מומנט 25 kg·cm, פולס 500–2500µs ב־50Hz).

3. **PCA9685 16-Channel 12-Bit PWM/Servo Driver — Datasheet.** NXP Semiconductors. [https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf)

4. **IRLZ44N Logic-Level MOSFET — Datasheet.** Infineon (formerly International Rectifier). [https://www.infineon.com/dgdl/Infineon-IRLZ44N-DataSheet-v01_01-EN.pdf](https://www.infineon.com/dgdl/Infineon-IRLZ44N-DataSheet-v01_01-EN.pdf)

5. **LM2596 Step-Down Switching Regulator — Datasheet.** Texas Instruments. [https://www.ti.com/lit/ds/symlink/lm2596.pdf](https://www.ti.com/lit/ds/symlink/lm2596.pdf)

6. **Microsoft LifeCam HD-3000 — Technical specifications.** Microsoft. [https://www.microsoft.com/accessories/en-us/products/webcams/lifecam-hd-3000/t3h-00011](https://www.microsoft.com/accessories/en-us/products/webcams/lifecam-hd-3000/t3h-00011)

## תיעוד ספריות תוכנה

7. **OpenCV — Documentation (Python bindings).** [https://docs.opencv.org/4.x/](https://docs.opencv.org/4.x/) — בעיקר הסעיפים על `cv2.VideoCapture`, `cv2.cvtColor`, `cv2.inRange`, `cv2.findContours`, `cv2.moments`, ו־HSV color space tutorial.

8. **NumPy — User Guide.** [https://numpy.org/doc/stable/user/index.html](https://numpy.org/doc/stable/user/index.html)

9. **gpiozero — Documentation.** [https://gpiozero.readthedocs.io/en/stable/](https://gpiozero.readthedocs.io/en/stable/) — בעיקר ה־class `LED`.

10. **Adafruit CircuitPython ServoKit — Library reference.** [https://docs.circuitpython.org/projects/servokit/en/latest/](https://docs.circuitpython.org/projects/servokit/en/latest/) — `set_pulse_width_range`, `actuation_range`.

11. **Adafruit CircuitPython PCA9685 — Library reference.** [https://docs.circuitpython.org/projects/pca9685/en/latest/](https://docs.circuitpython.org/projects/pca9685/en/latest/)

12. **simple-pid — PyPI page + GitHub.** [https://github.com/m-lundberg/simple-pid](https://github.com/m-lundberg/simple-pid) — בקר PID מינימליסטי עם anti-windup ו־output limits.

13. **tkinter — Python Standard Library docs.** [https://docs.python.org/3/library/tkinter.html](https://docs.python.org/3/library/tkinter.html)

## מאמרים, tutorials וקורסים

14. **Adrian Rosebrock — "OpenCV color spaces (cvtColor)".** PyImageSearch. [https://pyimagesearch.com/2021/04/28/opencv-color-spaces-cvtcolor/](https://pyimagesearch.com/2021/04/28/opencv-color-spaces-cvtcolor/) — בסיס ה־HSV thresholding בפרויקט.

15. **Adrian Rosebrock — "Ball tracking with OpenCV".** PyImageSearch. [https://pyimagesearch.com/2015/09/14/ball-tracking-with-opencv/](https://pyimagesearch.com/2015/09/14/ball-tracking-with-opencv/) — המקור המרכזי להשראה ל־`detector.py`.

16. **Brett Beauregard — "Improving the Beginner's PID" (series).** [http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-introduction/](http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-introduction/) — סדרת מאמרים בנושא בקרת PID, anti-windup, output clamping. הפך את כל הבחירות התכנוניות ב־`tracker.py` למובנות.

17. **Pololu — "Controlling RC Servos with Arduino".** [https://www.pololu.com/docs/0J50](https://www.pololu.com/docs/0J50) — הסבר טוב ל־PWM 50Hz עבור סרוואים גם אם הוא לא ספציפי ל־PCA9685.

18. **Sparkfun — "I2C tutorial".** [https://learn.sparkfun.com/tutorials/i2c](https://learn.sparkfun.com/tutorials/i2c) — הסבר נגיש לפרוטוקול I²C.

19. **Adafruit — "MOSFETs as switches".** [https://learn.adafruit.com/transistors-101](https://learn.adafruit.com/transistors-101) — בסיס למעגל הלייזר.

## מקורות אחרים

20. **Raspberry Pi OS — Documentation.** [https://www.raspberrypi.com/documentation/computers/os.html](https://www.raspberrypi.com/documentation/computers/os.html) — סעיפי GPIO, I²C ו־VNC.

21. **Linux UVC driver — kernel.org documentation.** [https://www.kernel.org/doc/html/latest/userspace-api/media/v4l/dev-capture.html](https://www.kernel.org/doc/html/latest/userspace-api/media/v4l/dev-capture.html)

22. **Stack Overflow — discussion threads.** מספר רב של חיפושים ספציפיים, בעיקר בנושאים: `cv2.VideoCapture` slow on Raspberry Pi, `simple-pid` tuning best practices, `tkinter` + `subprocess` integration, mixing `subprocess` with tkinter mainloop.

23. **GitHub — מאגר Raspberry Pi PWM examples של Adafruit.** [https://github.com/adafruit/Adafruit_CircuitPython_PCA9685/tree/main/examples](https://github.com/adafruit/Adafruit_CircuitPython_PCA9685/tree/main/examples) — דוגמאות שעזרו להבין את ה־ServoKit API לפני שכתבתי את `servo.py`.

24. **Anthropic Claude (Claude Code) — AI Assistant.** [https://claude.ai/code](https://claude.ai/code) — שותף לדיון על תכנון, debugging, וכתיבה. בוצע במצב חמר־מצח: כל החלטה תכנונית, כל בחירה אלגוריתמית, כל ניסוי בפועל וכל פסקה בספר אומתו והותאמו על־ידי. ה־AI סייע בעיקר ב־"רעיון ראשון" ל־הצעות ובסקירת קוד שכבר נכתב. כל הבחירות הסופיות נעשו על־ידי.

## מסמכי הפרויקט הפנימיים

מאגר הקוד הציבורי: **[https://github.com/Adamzvulun/pi](https://github.com/Adamzvulun/pi)**.

המסמכים הפנימיים הבאים הם חלק מהמאגר עצמו ומשמשים כמקור־אמת לפרטי המערכת:

- [`CLAUDE.md`](../../CLAUDE.md) — קונטקסט שלם של הפרויקט עבור session של Claude Code: חוקי החומרה, owner module pattern, חוקי קוד, מצב נוכחי של כל phase.
- [`docs/calibration.md`](../../docs/calibration.md) — תיעוד כל הערכים שכויילו אמפירית: גבולות סרוואים, טווח HSV, רווחי PID, היסטוריית כיול.
- [`docs/operating-guide.md`](../../docs/operating-guide.md) — מדריך הפעלה יומיומי: פקודות, סקריפטים, troubleshooting, פרוצדורות.
- [`docs/plan/`](../../docs/plan/) — תיעוד מלא של 8 phases הפיתוח. כל phase קובץ נפרד.
- [`problems/001-servo-power.md`](../../problems/001-servo-power.md) — תיעוד מלא של אירוע הספק.
- [`problems/002-laser-dead.md`](../../problems/002-laser-dead.md) — תיעוד מלא של אירוע הדיודה המתה.
