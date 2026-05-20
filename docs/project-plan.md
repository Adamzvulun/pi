# Laser Tracker — Full Project Plan

This document is the authoritative step-by-step plan for building the laser tracker from where we are today to a finished, working system. Every phase is broken into individual tasks. Each task says what to do, what code to write, how to test it, and what success looks like.

Work through phases in order. Do not skip ahead. Every phase produces something testable before moving on.

---

## Where we are right now

- ✅ Pi OS installed, SSH/VNC/I2C enabled
- ✅ All libraries installed (Adafruit, picamera2, OpenCV, numpy, gpiozero, simple-pid, rpicam-apps)
- ✅ Repo on GitHub, auto-pull cron running every minute
- ✅ **Problem 001 (servo power) resolved**: LM2596 buck converter supplies servo V+ at 5V from the 12V PSU. Pi GPIO 5V powers PCA9685 VCC directly. MB102 no longer in the circuit. See `problems/001-servo-power.md` and `docs/wiring.md`.
- ✅ **Pan-tilt bracket reassembled** with electrical 135° = physical center on both axes.
- ✅ **Task 3.1 (i2cdetect) verified** — PCA9685 responds at 0x40.
- ✅ **Task 3.2 (test_servo.py) written and verified** — full chain Pi → I2C → PCA9685 → DS3225 works.
- ✅ **Task 3.3 (calibrate_servo.py) written and used** to find safe physical limits (`PAN_MIN/MAX`, `TILT_MIN/MAX`).
- ⏳ **Next task: 3.4** — write `servo.py` hardcoding the calibrated limits as safety clamps.

(Phase 6 laser circuit was temporarily disconnected when the breadboard was removed; it will be rebuilt in Phase 6 work.)

---

## Phase 3 — Servo Control

### Task 3.1 — Wire the Pi to the breadboard

**Do this with the Pi powered off. Unplug the USB-C cable first.**

You need three female-to-male jumper wires. One end goes on the Pi GPIO header; the other end presses into the breadboard.

Finding the right GPIO pins — hold the Pi so the USB ports face away from you. The 40-pin header is the two rows of pins on the top-left. Pin 1 is the corner pin closest to the SD card slot (tiny printed triangle on the board). The top row is odd numbers (1, 3, 5…), bottom row is even numbers (2, 4, 6…), both counting left to right.

| Pi physical pin | GPIO signal | Breadboard destination | Purpose |
|---|---|---|---|
| Pin 3 | GPIO2 — SDA | j14 | I2C data line to PCA9685 |
| Pin 5 | GPIO3 — SCL | j13 | I2C clock line to PCA9685 |
| Pin 6 | GND | blue (−) rail | Common ground |

**What is I2C?** I2C (pronounced "I-squared-C") is a communication protocol — a standard way for the Pi to talk to components like the PCA9685 over just two wires: SDA (data) and SCL (clock). The Pi sends commands down the SDA wire in time with pulses on the SCL wire. Each device on the bus has a unique address (the PCA9685 uses 0x40) so the Pi can target it specifically. That's all it is. You don't need to implement any of this yourself — the Adafruit library handles it. You just need the wires to be physically connected.

Pin 3 and Pin 5 are in the top row, second and third from the left. Pin 6 is directly below Pin 5 in the bottom row.

**Power up sequence:**
1. Plug the 12V PSU into the MB102 first — the red power LED on the MB102 should come on
2. Plug the USB-C cable into the Pi
3. Wait about 30 seconds for the Pi to finish booting

**Verify with i2cdetect:**

SSH to the Pi, then run:
```bash
i2cdetect -y 1
```

You should see a grid of dashes with `40` appearing somewhere in it. That `40` is the PCA9685 responding on I2C address 0x40. If the whole grid is dashes, see the troubleshooting section below.

**Success looks like:**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: 40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
...
```

**Troubleshooting if `40` doesn't appear:**
- Recheck the three jumper wires — each one has two ends, confirm both ends are firmly seated
- Confirm the 12V PSU is on (MB102 LED lit)
- Check I2C is still enabled: `sudo raspi-config` → Interface Options → I2C → Yes
- Run `i2cdetect -y 0` — if `40` appears there, I2C bus 0 is active instead of bus 1 (shouldn't happen on Pi 4B but worth checking)

---

### Task 3.2 — Write test_servo.py

This is the first real code. It moves the servos so you can confirm the whole chain works: laptop → GitHub → Pi auto-pull → Python → I2C → PCA9685 → servo physically moves.

**Create `test_servo.py` on the laptop.**

What it does:
- Imports ServoKit and configures it for the DS3225 servos
- Moves pan servo (channel 0) to center
- Moves tilt servo (channel 1) to center
- Slowly sweeps pan left, then right, then back to center
- Pauses between movements so you can see each step
- Shuts down cleanly when done

**Important — DS3225 pulse width configuration:**

A servo is controlled by sending it a PWM pulse of a specific width (measured in microseconds). The width tells the servo what angle to move to. Standard cheap servos use 1000–2000 µs for 0°–180°. The DS3225 is a higher-end servo that covers 270° and uses a wider range: 500–2500 µs.

ServoKit doesn't know you have a DS3225 — it assumes a standard servo by default. If you don't tell it otherwise, it will only ever command pulses between its default range, which means the servo will only move a fraction of its actual range and the angle numbers in your code will be wrong. You must configure it for every channel you use:
```python
kit.servo[channel].set_pulse_width_range(500, 2500)
kit.servo[channel].actuation_range = 270
```

After this, angle 0 = fully one direction, angle 270 = fully the other direction, and angle 135 = center. The center pulse works out to exactly 1500 µs, which is the DS3225's documented neutral point.

After writing the file on the laptop, commit and push. The Pi will auto-pull within 60 seconds. Then SSH to the Pi and run:
```bash
source ~/pi/venv/bin/activate
python3 test_servo.py
```

**Success looks like:** both servos move to center (135° in the 270° range), the pan servo sweeps left and right visibly, then returns to center. No errors in the terminal.

**Troubleshooting:**
- `OSError: [Errno 121] Remote I/O error` — I2C isn't reaching the PCA9685. Check jumper wires and re-run i2cdetect.
- Servo hums/vibrates but doesn't move — pulse range is wrong, or servo is at a limit. Check your actuation_range and pulse width settings.
- Servo moves but very weakly — possible brownout at 5V under load. This is known and accepted. If it's severe, reduce speed of movement (add more sleep between angle steps).

---

### Task 3.3 — Write calibrate_servo.py

The DS3225 is rated for 270° of rotation, but your pan-tilt bracket has physical stops — the mechanical limits where the bracket hits itself and can't go further. Those limits are the actual safe range for your system. You need to find them before writing any tracking code, because commanding a servo past its physical stop can damage it or burn out the motor.

**Create `calibrate_servo.py` on the laptop.**

What it does:
- Initializes both servos to center (135°)
- Enters an interactive loop: you type an angle (0–270), it moves the servo there
- You watch the bracket and type 's' when it hits a hard stop
- You do this for both servos, both directions
- At the end it prints the safe limits to copy into servo.py

**How to run:**
```bash
python3 calibrate_servo.py
```

**Calibration procedure:**
1. The script starts both servos at center (135°) and asks which servo to calibrate first — type `0` for pan, `1` for tilt
2. It will prompt: "Enter angle (0–270):" — type a number and press Enter, the servo moves there
3. Start with pan (channel 0), moving toward 0° in steps: type `100`, watch, type `70`, watch, type `50`…
4. Stop **before** you hear or feel the bracket grinding — the servo should stop smoothly at its physical limit, not be forced into it
5. The last angle where the bracket moved freely (not grinding) is your `pan_min` — write it down
6. Type `135` to return to center, then move toward 270° the same way to find `pan_max`
7. Type `done` when finished with one servo — the script will print the safe limits for that servo
8. Repeat for tilt (channel 1)

The four values you end up with — `pan_min`, `pan_max`, `tilt_min`, `tilt_max` — go into `servo.py` as constants. Write them down somewhere physical too (a sticky note is fine) in case you need to reference them later.

---

### Task 3.4 — Write servo.py

This is the servo module that all other code will import. It's the only place in the entire codebase that knows about servo hardware details. Everything else just calls `move_pan(angle)` and `move_tilt(angle)` without worrying about I2C, pulse widths, or limits.

**Create `servo.py` on the laptop.**

What it contains:
- Constants: `PAN_MIN`, `PAN_MAX`, `TILT_MIN`, `TILT_MAX` — from your calibration in Task 3.3
- Constants: `PAN_CENTER = (PAN_MIN + PAN_MAX) / 2`, `TILT_CENTER` similarly
- `init()` — creates the ServoKit, configures pulse width ranges, moves both servos to center, returns the kit
- `move_pan(kit, angle)` — clamps angle to [PAN_MIN, PAN_MAX] before commanding (the clamp is what enforces safety)
- `move_tilt(kit, angle)` — same for tilt
- `center(kit)` — moves both servos to their center positions
- `cleanup(kit)` — moves to center and releases (called on shutdown)

**Test it** by importing it from a quick test in the Python REPL on the Pi:
```bash
python3 -c "import servo; kit = servo.init(); servo.move_pan(kit, servo.PAN_MIN); import time; time.sleep(1); servo.center(kit)"
```

The pan servo should move to its minimum angle and come back to center.

---

## Phase 4 — Camera and Target Detection

### Task 4.1 — Connect the Pi Camera

**Do this with the Pi powered off.**

The Pi Camera connects via a flat ribbon cable into the CSI (Camera Serial Interface) slot on the Pi. The CSI slot is the narrow white connector between the HDMI ports and the USB ports, labeled "CAMERA" on the board.

**How to seat the ribbon cable:**
1. Gently lift the dark locking tab on the CSI connector — it pulls straight up (not a hinge, don't yank it)
2. Slide the ribbon cable in with the metal contacts facing toward the HDMI ports (away from you)
3. Press the locking tab back down firmly

Power the Pi back on, SSH in, and test with:
```bash
rpicam-still -o ~/test.jpg
```

This takes a still photo and saves it to your home directory. To view it, either copy it to your laptop with `scp` or use VNC to open the file browser.

**Success:** the command completes without errors and `test.jpg` exists and shows a real image.

**Troubleshooting:**
- `ERROR: *** no cameras available ***` — ribbon cable isn't seated. Power off and reseat it. Also check: `sudo raspi-config` → Interface Options → Camera → Enable.
- Image is dark or blurry — this is normal for initial testing, lighting and focus can be adjusted later.

---

### Task 4.2 — Write camera.py

This module is the single point of access to the Pi Camera for all other code. Nothing else talks to the camera directly.

**Create `camera.py` on the laptop.**

What it contains:
- `init(width=640, height=480)` — starts picamera2, configures resolution, returns the camera object. 640×480 is the right starting resolution: high enough to see detail, low enough for the Pi to process in real time.
- `capture_frame(camera)` — captures one frame and returns it as a numpy array in BGR color format (which is what OpenCV expects)
- `release(camera)` — stops and closes the camera cleanly

**Why BGR and not RGB?** OpenCV historically uses BGR order (Blue, Green, Red) instead of the more common RGB. picamera2 captures in RGB by default, so `camera.py` will convert to BGR on capture. This means the rest of the code never has to think about it.

**Test it** on the Pi:
```bash
python3 -c "
import camera, cv2
cam = camera.init()
frame = camera.capture_frame(cam)
cv2.imwrite('/home/adam/capture_test.jpg', frame)
camera.release(cam)
print('Saved.')
"
```
View the saved image. It should look identical to what `rpicam-still` produced.

---

### Task 4.3 — Understand HSV color detection

Before writing the detector, it helps to understand what it's doing.

Your camera produces images in BGR — every pixel has a Blue value, a Green value, and a Red value. The problem with detecting a color using BGR is that the same red ball looks very different in bright sunlight vs. indoor light — the raw RGB numbers change a lot depending on lighting.

HSV (Hue, Saturation, Value) separates color from brightness:
- **Hue** (0–179 in OpenCV) — the actual color: red, orange, yellow, green, blue, etc.
- **Saturation** (0–255) — how vivid the color is. 0 = grey, 255 = fully saturated color.
- **Value** (0–255) — how bright the pixel is. 0 = black, 255 = full brightness.

By thresholding on Hue only (or Hue + a loose range on S and V), you can find a specific color regardless of whether the room is bright or dim. That's why HSV is the right tool for this job.

**Choose your target object now.** It should be:
- A single solid color that doesn't appear anywhere else in the scene
- Bright and saturated (avoid pastel colors, they're hard to threshold)
- Good options: a bright orange object, a tennis ball (yellow-green), a bright blue tape mark

**Avoid red as your target color.** Red is the one color that wraps around in OpenCV's HSV space — it appears near H=0 AND near H=179, so a single `inRange` call can't capture it cleanly. You'd need two separate masks and combine them. Every other color is straightforward. Pick something orange, yellow, green, or blue instead.

---

### Task 4.4 — Write tune_detector.py

You can't write a good detector without first knowing the exact HSV range of your target. This script shows you a live camera feed and lets you adjust the color thresholds in real time using sliders until the target is cleanly isolated.

**Create `tune_detector.py` on the laptop.**

What it does:
- Opens two windows side by side: the live camera feed, and the "mask" (a black-and-white image where white pixels are what the current threshold is detecting)
- Shows 6 slider bars: H_min, H_max, S_min, S_max, V_min, V_max
- As you move the sliders, the mask updates live
- When the mask shows your target as a solid white blob and everything else as black, you've found your range
- Press 's' to save those values to `config.py` and exit

**How to run it:**

This script opens GUI windows, so you need to see the Pi's display. The easiest way on Windows is **VNC** — it's already enabled on your Pi. Open your VNC viewer, connect to `LaserPi.local`, and you'll see the Pi's desktop. Open a terminal there and run the script. The windows will appear on the Pi's virtual desktop in front of you.

(There is another method called SSH X forwarding — `ssh -X` — but on Windows it requires installing a separate X server program like VcXsrv. VNC is already set up, so use that.)

```bash
python3 tune_detector.py
```

**Tuning procedure:**
1. Point the camera at your target object with typical lighting (the lighting you'll actually use when tracking)
2. The sliders start at wide ranges (H: 0–179, S: 50–255, V: 50–255) — the mask will show a lot of white at first
3. Narrow H_max down from 179 and raise H_min up from 0 until only your target color is white in the mask
4. Raise S_min to remove grey and washed-out patches
5. Adjust V_min and V_max to handle the brightness of your lighting
6. When the mask shows your target as a clean solid white blob and everything else is black, press 's'

When you press 's', the script prints the six values to the terminal. Copy them into `config.py` manually — update the `HSV_LOWER` and `HSV_UPPER` lines. This is intentional: auto-writing Python files is fragile, and manually copying three numbers takes five seconds.

---

### Task 4.5 — Write config.py

A simple file that stores the tuned detection values and any other constants shared between modules.

**Create `config.py` on the laptop** (tune_detector.py will write into it, but create the template first):

What it contains:
- `HSV_LOWER` — numpy array of [H_min, S_min, V_min]
- `HSV_UPPER` — numpy array of [H_max, S_max, V_max]
- `FRAME_WIDTH = 640`
- `FRAME_HEIGHT = 480`
- `FRAME_CENTER_X = FRAME_WIDTH // 2`
- `FRAME_CENTER_Y = FRAME_HEIGHT // 2`

---

### Task 4.6 — Write detector.py

Now that you have the tuned HSV range, write the actual detection logic.

**Create `detector.py` on the laptop.**

What it contains:
- `detect(frame)` — takes a BGR frame, returns `(x, y)` pixel coordinates of the target center, or `None` if not found

What the function does step by step:
1. Apply a small Gaussian blur to the original BGR frame before converting — this smooths out pixel noise in the camera sensor so the color detection is less jittery (`cv2.GaussianBlur` with a 5×5 kernel)
2. Convert the blurred frame from BGR to HSV
3. Create a mask using `cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)` — white (255) where the target color is, black (0) everywhere else
4. Clean up the mask with morphological operations: `cv2.erode` (shrinks white regions, removes tiny specks of noise) followed by `cv2.dilate` (grows them back, fills small holes). This is better than blurring a black-and-white image, which just creates grey edges.
5. Find contours in the mask (`cv2.findContours`)
5. If no contours found, return None
6. Find the largest contour by area (this is most likely the target)
7. If the largest contour is too small (below a minimum area threshold), return None — this filters out noise
8. Find the center of that contour using moments (`cv2.moments`)
9. Return `(cx, cy)` — the pixel coordinates of the center

**Test it** by writing a quick loop that captures a frame, runs `detect()`, and prints the result:
```bash
python3 -c "
import camera, detector
cam = camera.init()
frame = camera.capture_frame(cam)
result = detector.detect(frame)
print('Detected at:', result)
camera.release(cam)
"
```
Hold your target in front of the camera. You should see coordinates printed. Move the target away and you should see `None`.

---

## Phase 5 — PID Closed-Loop Tracking

### Task 5.1 — Understand the tracking math

Before writing code, understand what's happening:

The camera frame is 640×480 pixels. The center of the frame is at (320, 240). When the target is perfectly centered, the servos should not move.

The **error** is the distance from the target to the frame center:
- `pan_error = target_x - 320` (positive means target is to the right, negative means left)
- `tilt_error = target_y - 240` (positive means target is below center, negative means above)

A PID controller takes that error as input and outputs a correction. For pan: if the target is 50 pixels to the right, the PID outputs a number that gets added to the current pan angle to move the camera right. Next frame, the error is smaller. Eventually the error reaches zero and the servo stops moving.

The **proportional gain (Kp)** is the main tuning knob. A higher Kp means larger corrections for the same error — the servo moves faster. Too high and it overshoots and oscillates. Too low and it tracks slowly.

**A note on the wide-angle lens:** your camera has a 220° field of view — that's a fisheye lens. It creates barrel distortion, meaning objects near the edges of the frame appear stretched and displaced. The math above (pixel error → servo angle) assumes a flat undistorted image. Near the center of the frame the distortion is small and the approximation works fine. Near the edges it gets worse. For this project that's acceptable — the tracker will keep the target near the center anyway. Don't be surprised if tracking feels slightly less precise when the target first enters the frame from the edge.

---

### Task 5.2 — Write tracker.py

**Create `tracker.py` on the laptop.**

What it contains:
- `init()` — creates two PID instances (one for pan, one for tilt) with initial gains, sets setpoint to 0 (we want zero error), returns them
- `update(pan_pid, tilt_pid, kit, target_pos)` — the main function called every frame:
  - If `target_pos` is None, don't move (hold position)
  - Compute pan_error and tilt_error from target_pos and frame center
  - Run `pan_pid(pan_error)` — returns a correction value
  - Add that correction to the current pan angle, clamp to safe limits, move the servo
  - (Kp is the scaling factor that converts pixels of error into degrees of correction — tuning Kp in Task 5.4 is exactly this)
  - Same for tilt
- `stop(kit)` — centers servos and cleans up

**Initial PID gains to start with:**
```python
Kp = 0.05   # start very gentle
Ki = 0.0    # disable integral to start
Kd = 0.01   # small amount of damping
```

**Output limits:** set the PID's output limits to something like (-20, 20) degrees per update. This prevents the PID from commanding a huge sudden jump if the target suddenly appears at the edge of the frame.

---

### Task 5.3 — Write a combined tracking test

**Create `test_tracking.py` on the laptop.**

This isn't the final main.py — it's a standalone test that runs the full loop (camera → detect → PID → servos) so you can tune the gains before adding the laser.

What it does:
- Initializes camera, servos, and PID
- Runs in a loop:
  - Capture frame
  - Detect target
  - Update tracker
  - Optionally save a frame with the detected position drawn on it (for debugging)
  - Press 'q' to quit
- On quit: center servos, release camera

**Running it:**
```bash
python3 test_tracking.py
```

Move your colored target slowly in front of the camera. The pan-tilt bracket should follow it.

---

### Task 5.4 — Tune the PID gains

This step requires iteration. There's no shortcut — you run the tracking test, observe the behavior, adjust a number, and run again.

**Tuning procedure:**

Start with P-only (Ki=0, Kd=0):
- If tracking is too slow or barely moves: increase Kp (try doubling it)
- If the servos oscillate (overshoot and wobble back and forth): decrease Kp
- Find the value where tracking is responsive but not oscillating

Add D once P is roughly set:
- Kd = Kp * 0.1 is a reasonable starting point
- D damping reduces overshoot and stabilizes the system
- If you add too much D, the system becomes sluggish and ignores fast movements

Only add I if there's a persistent offset:
- If the target settles slightly off-center and never fully corrects, add a tiny Ki (try 0.001)
- Too much I causes slow oscillation that builds over time (integral windup)

**Record your final gain values** in `config.py` alongside the HSV values.

---

## Phase 6 — Laser Integration

### Task 6.1 — Verify laser voltage before wiring anything

The laser module is rated at 3V. The MB102 rail is 5V. Do not connect the laser directly to 5V — it will likely burn out.

**Before wiring, look at the laser module PCB.** Many laser modules (especially ones sold as "KY-008" or similar 3-pin breakout boards) already have a small resistor on the PCB that limits the current. Look for any component soldered onto the module board — if you see a resistor (a small rectangular component with colored bands or markings), the module already has protection built in and can likely accept 3–5V directly.

**Regardless, always wire a series resistor anyway.** A 100Ω resistor in series between the 5V rail and the laser (+) terminal:
- Protects a module with no internal regulation by dropping about 1V at typical laser currents
- Does nothing harmful to a module that already has internal regulation — it just drops a tiny bit more voltage
- Costs you nothing and takes 30 seconds to add

When we reach this task, we'll pick the exact resistor value based on your module. The point is: **never connect the laser directly to 5V without any series resistance.**

---

### Task 6.2 — Wire the laser

**Do this with everything powered off.**

Two connections to make:
1. Pi GPIO18 (pin 12) → breadboard row 50 (this is the MOSFET gate stub — the wire from row 50 already has the 220Ω resistor going to the gate at c45)
2. Laser (+) → 5V rail (with series resistor if needed, see Task 6.1) and laser (−) → MOSFET drain (c46)

Finding GPIO18: it's Pin 12, in the top row, sixth from the left.

After wiring, before running any code: double-check that the laser (−) is connected to the MOSFET drain (c46), and the source (c47) has a jumper to the GND rail. When GPIO18 goes HIGH (3.3V from the Pi), the MOSFET turns on and conducts — current flows from the laser (+) supply, through the laser, through the MOSFET drain-to-source, to GND. That's what lights the laser. When GPIO18 goes LOW, the MOSFET turns off and the circuit is broken — laser off.

---

### Task 6.3 — Write laser.py

**Create `laser.py` on the laptop.**

What it contains:
- Uses `gpiozero.LED` to control GPIO18 (the simplest way to drive a GPIO pin high/low)
- `init()` — sets up GPIO18 as output, ensures it starts LOW (laser off), returns the device object
- `fire(laser_device)` — sets GPIO18 HIGH (laser on)
- `off(laser_device)` — sets GPIO18 LOW (laser off)
- `cleanup(laser_device)` — calls `off()` then closes the GPIO device

**Safety pattern to use everywhere laser is involved:**
```python
laser_dev = laser.init()
try:
    # ... do things ...
finally:
    laser.cleanup(laser_dev)
```
This guarantees the laser turns off even if an exception is raised or the script is interrupted.

Note the variable is named `laser_dev`, not `laser`. If you named it `laser`, it would shadow the module — `laser = laser.init()` would work but then `laser.cleanup(...)` would fail because `laser` now refers to the device object, not the module. Always use a different name for the variable.

---

### Task 6.4 — Write test_laser.py

Before integrating with anything else, test the laser in isolation.

**Create `test_laser.py` on the laptop.**

What it does:
- Initializes the laser
- Prints "Firing in 3... 2... 1..."
- Fires for exactly 1 second
- Turns off
- Confirms in the terminal that it's off

**Success:** the laser dot appears on the wall for 1 second and then turns off cleanly.

**Troubleshooting:**
- Laser doesn't turn on: check GPIO18 wiring, check MOSFET connections (gate/drain/source order on the IRLZ44N is G-D-S with flat face toward you)
- Laser stays on after script ends: `cleanup()` wasn't called — the `finally` block should handle this
- Laser is too dim or not full brightness: voltage may be too low — recheck the series resistor calculation

---

## Phase 7 — Mechanical Mounting

### Task 7.1 — Mount the camera to the pan-tilt bracket

The camera needs to be attached to the tilt plate (the part that moves up and down) and pointed forward. The exact mounting method depends on your bracket hardware — most kits include screws or standoffs.

Things to aim for:
- Camera lens roughly centered on the bracket's rotation axis (reduces the amount the image "swings" when tilting)
- Cable routed so it doesn't bind or pull when the bracket moves through its full range
- Secure enough that the camera doesn't wobble

After mounting: run `test_servo.py` again and verify the servos can still move through their full safe range without the cable snagging.

---

### Task 7.2 — Mount the laser to the bracket

Mount the laser on the same tilt plate as the camera, pointing in roughly the same direction as the camera.

The laser doesn't need to be perfectly aligned to the camera yet — boresighting (Task 7.4) handles that. Just get it physically secure and pointing roughly forward.

Route the laser wires the same way as the camera cable — make sure they don't bind during movement.

---

### Task 7.3 — Extend cables if needed

Now that the camera and laser are mounted on the bracket, measure whether the existing wires (camera ribbon cable, laser wires, servo wires) have enough length to reach their respective connections while allowing full bracket movement.

If the camera ribbon cable is too short: longer Pi Camera ribbon cables are available cheaply (look for "Pi Camera extension cable"). This is very common and expected.

If laser wires are too short: splice or solder extensions. Thin hookup wire works fine.

---

### Task 7.4 — Boresight calibration (align camera and laser)

The camera and laser are physically offset from each other on the bracket — they don't point at exactly the same spot. Boresighting measures that offset so the tracking code can compensate.

**Create `boresight.py` on the laptop.**

What it does:
1. Shows a live camera feed
2. Draw crosshairs at the frame center (320, 240)
3. Instruct Adam to point the bracket at a target until the crosshair is centered on it
4. Fire the laser for 0.5 seconds
5. Adam notes where the laser dot landed relative to the target
6. Instruct Adam to use arrow keys to move a second cursor on-screen to where the laser dot was
7. The difference between (320, 240) and the laser cursor position is the boresight offset
8. Save `BORESIGHT_X_OFFSET` and `BORESIGHT_Y_OFFSET` to `config.py`

After boresighting: the tracker will aim slightly ahead of the target to account for the offset — so when the laser fires, it lands on the target rather than on the camera's exact aim point.

**Update `tracker.py`** to subtract the boresight offset from the pixel error fed into the PIDs.

---

## Phase 8 — Final Integration

### Task 8.1 — Write the full main.py

Replace the placeholder with the real tracking loop.

**What main.py does:**

```
Initialize logging
Initialize servos (servo.py) → center
Initialize camera (camera.py)
Initialize PID trackers (tracker.py)
Initialize laser (laser.py) → off

Print instructions to user:
  - 'f' = fire laser at current target
  - 'q' = quit

Enter main loop:
  1. Capture frame
  2. Run detector.detect(frame)
  3. If target found:
       - Update tracker (moves servos)
       - Draw target marker on frame for debugging
  4. If 'f' pressed AND target is currently centered (error below threshold):
       - Log "Firing"
       - laser.fire()
       - Wait 0.5 seconds
       - laser.off()
  5. If 'q' pressed: break

On exit (finally block):
  - laser.off()
  - servo.cleanup()
  - camera.release()
  - Log "Shutdown complete"
```

The "centered" check before firing: only allow firing if the pixel error is below a threshold (e.g. 15 pixels in both axes). This prevents firing when the target is moving fast or partially out of frame.

---

### Task 8.2 — End-to-end test

Run the full system:
```bash
source ~/pi/venv/bin/activate
python3 main.py
```

**Test sequence:**
1. No target visible → servos should hold position, laser stays off
2. Bring target into frame → servos should start tracking
3. Move target slowly → servos follow
4. Hold target still in center → error drops to near zero
5. Press 'f' → laser fires for 0.5 seconds, turns off
6. Press 'q' → clean shutdown, servos center, laser off confirmed in log

---

### Task 8.3 — Update documentation

Once the system is working end-to-end:

**Update `CHANGELOG.md`** with an entry covering this session.

**Update `README.md`** to reflect the finished project — the "How to run" section should describe what `main.py` actually does now, not the placeholder.

**Create `docs/calibration.md`** — record the actual values from your calibration runs:
- Safe servo angle limits (pan_min, pan_max, tilt_min, tilt_max)
- Tuned HSV range for your target
- Tuned PID gains
- Boresight offset values

This document is important if you ever need to recalibrate or rebuild from scratch.

---

## Full file map at completion

```
pi/
├── main.py                  the full tracking loop
├── servo.py                 servo init, safe limits, move functions
├── camera.py                picamera2 capture
├── detector.py              HSV color detection, returns target (x,y)
├── tracker.py               PID loop: pixel error → servo correction
├── laser.py                 GPIO18 control with safety defaults
├── config.py                tuned constants: HSV range, PID gains, boresight offset
├── test_servo.py            servo movement test (keep for debugging)
├── calibrate_servo.py       interactive servo limit finder
├── tune_detector.py         live HSV tuning tool
├── test_tracking.py         tracking loop without laser (for PID tuning)
├── test_laser.py            laser test in isolation
├── boresight.py             camera-laser offset calibration tool
├── requirements.txt         pip packages (simple-pid already included)
├── CLAUDE.md                project context for Claude Code
├── CHANGELOG.md             session log
├── README.md                project overview
└── docs/
    ├── setup-pi.md          Pi setup instructions
    ├── wiring.md            wiring reference
    ├── project-plan.md      this file
    └── calibration.md       recorded calibration values
```

---

## Rules to follow throughout the project

- **Every file is written on the laptop, committed, and pushed.** Never edit files directly on the Pi.
- **Every phase ends with a working, tested piece** before starting the next phase.
- **Test scripts are kept** — don't delete `test_servo.py` or `test_laser.py` after the real code is working. They're useful for debugging if something breaks later.
- **Commit often** — after every task that produces working code, commit with a clear message.
- **Update CHANGELOG.md** at the end of every working session.
- **If something doesn't work**, diagnose before moving on. Each phase assumes the previous phase's test passed cleanly.
- **Update `docs/wiring.md`** as you complete physical wiring steps — mark the connections as done so the document stays accurate.
