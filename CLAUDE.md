# CLAUDE.md — Laser Tracker Project Context

This file is read by Claude Code at the start of every session. Read it fully before writing any code.

**Also read `docs/project-plan.md`** — it has the full phase-by-phase implementation plan with detailed tasks, code descriptions, and test procedures. This file (CLAUDE.md) gives you the hardware and architecture context; project-plan.md tells you what to build next.

---

## What this project is

Autonomous laser tracking system on a Raspberry Pi 4B. Camera detects a target, two servos (pan + tilt) keep it centered via PID control, then a 5mW laser fires on user confirmation.

## Target environment

- Hardware: Raspberry Pi 4B (8GB), hostname `LaserPi`, user `adam`
- OS: Raspberry Pi OS 64-bit (Bookworm)
- Python: 3.11
- Working directory on Pi: `~/pi`
- SSH: `ssh adam@LaserPi.local`

## Three-machine workflow

1. Edit code on the laptop (`C:\Projects\pi`) using Claude Code
2. `git push` to GitHub (private repo `pi`)
3. Pi auto-pulls from GitHub every minute via cron
4. SSH to Pi → `source ~/pi/venv/bin/activate` → `python3 main.py`

Code is NEVER edited directly on the Pi.

## Libraries

**In requirements.txt (pip-installed into venv):**
- `adafruit-circuitpython-pca9685` — low-level PCA9685 driver
- `adafruit-circuitpython-servokit` — high-level servo control
- `adafruit-blinka` — CircuitPython compatibility layer for Pi
- `simple-pid` — PID controller for closed-loop tracking (Phase 5)

**apt-installed (system packages, NOT in requirements.txt):**
- `picamera2` — camera capture
- `python3-opencv` / `cv2` — image processing
- `python3-numpy` / `numpy` — array math
- `python3-gpiozero` / `gpiozero` — GPIO control
- `rpicam-apps` — CLI camera tools (`rpicam-still`, `rpicam-vid`) for testing

**Important:** The venv was created with `--system-site-packages`. This is why `picamera2`, `cv2`, and `numpy` are importable from within the venv even though they are apt packages, not pip packages. Do not attempt to pip-install these.

**GPIO:**
- Use `gpiozero.LED` for the laser GPIO pin (simple digital output)
- Use `RPi.GPIO` only if low-level timing is needed (it isn't for this project)

## Hardware constraints

| Item | Detail |
|---|---|
| I2C bus | Bus 1 (GPIO2=SDA, GPIO3=SCL) |
| PCA9685 address | 0x40 (default) |
| Servo frequency | 50 Hz |
| DS3225 pulse range | 500–2500 µs — must call `set_pulse_width_range(500, 2500)` |
| DS3225 actuation_range | 270 — must set `actuation_range = 270` (ServoKit defaults to 180, which is wrong) |
| DS3225 neutral | 1500 µs = angle 135° (center of 270° range) |
| Channel 0 | Pan servo (left-right, bottom of bracket) |
| Channel 1 | Tilt servo (up-down, top of bracket) |
| Laser GPIO | GPIO18 (physical pin 12), active HIGH via MOSFET gate |
| Laser gate resistor | 220Ω between GPIO18 and MOSFET gate |
| Laser pulldown | 100kΩ gate-to-GND |
| Servo supply voltage | 5V from MB102 rail (spec is 4.8–6.8V; running at lower end — may brown out under load) |

## Safety rules (always follow these)

- Software-enforced angle limits on both servos — never command past mechanical stops
- Laser is OFF by default when any script starts
- Laser must be turned OFF on script exit — use `try/finally`
- Every script must handle `KeyboardInterrupt` cleanly — do not let it leave the laser on
- When using laser.py, name the device variable `laser_dev`, never `laser` — using `laser` shadows the module name and causes a crash

## Module design pattern

Each hardware subsystem has exactly one owner module. All other code goes through that module's public functions — never imports the underlying library directly.

| Module | Owns | Other files must not import |
|---|---|---|
| `servo.py` | ServoKit, I2C, PCA9685 | `adafruit_servokit`, `adafruit_pca9685` |
| `camera.py` | picamera2 | `picamera2` |
| `laser.py` | GPIO18 | `gpiozero` directly for this pin |
| `detector.py` | OpenCV detection logic | (cv2 is fine to use in detector.py) |
| `tracker.py` | PID loop | `simple_pid` |
| `config.py` | All tuned constants | — |

`main.py` and test scripts import from these modules only — never from hardware libraries directly.

## Shared config (config.py)

`config.py` is the single source of truth for all values that get tuned or calibrated. Create it early (Task 4.5) with placeholder values; fill in real values as each calibration step is completed.

| Constant | Set during | Description |
|---|---|---|
| `HSV_LOWER` | Task 4.4 | numpy array [H_min, S_min, V_min] |
| `HSV_UPPER` | Task 4.4 | numpy array [H_max, S_max, V_max] |
| `FRAME_WIDTH` | Task 4.5 | 640 |
| `FRAME_HEIGHT` | Task 4.5 | 480 |
| `FRAME_CENTER_X` | Task 4.5 | FRAME_WIDTH // 2 |
| `FRAME_CENTER_Y` | Task 4.5 | FRAME_HEIGHT // 2 |
| `PAN_MIN`, `PAN_MAX` | Task 3.3 | Safe pan angle limits from bracket calibration |
| `TILT_MIN`, `TILT_MAX` | Task 3.3 | Safe tilt angle limits from bracket calibration |
| `KP`, `KI`, `KD` | Task 5.4 | PID gains, tuned empirically |
| `BORESIGHT_X_OFFSET` | Task 7.4 | Pixel offset between camera aim and laser dot (x) |
| `BORESIGHT_Y_OFFSET` | Task 7.4 | Pixel offset between camera aim and laser dot (y) |

## Confirmed design decisions

These were explicitly decided — do not change them without asking:

- **Target detection method:** HSV color thresholding on a bright solid-colored object (not red — red wraps around in OpenCV HSV and needs two masks). Uses `cv2.inRange` on the HSV frame.
- **Fire trigger:** `'f'` keypress in the SSH terminal fires the laser. `'q'` quits. No physical button.
- **Camera resolution:** 640×480. Good balance of detail vs. processing speed on the Pi.
- **Laser confirmation threshold:** Only fire if pixel error is below 15px in both axes — prevents firing while still moving.

## Coding style

- **Comments:** Comment generously. Adam is learning. Explain WHY, not just what.
- **Type hints:** Use them where they aid clarity (function signatures, return types)
- **Function size:** Prefer small, focused functions over large ones
- **Logging:** Use the `logging` module, not `print()`, for runtime output
- **Python version:** Python 3 only
- **Error handling:** Handle hardware errors gracefully (I2C failures, servo brownout)

## Current project state

Update this section at the end of every session.

- ✅ Phase 1–2: OS, libraries, breadboard hardware all complete
- ✅ Phase 3 prep: repo skeleton, cron auto-pull, all libraries installed (including simple-pid), system packages up to date
- ⏳ **Next task: 3.1** — wire three jumpers from Pi GPIO to breadboard, run `i2cdetect -y 1`, confirm `40` appears
- ⏸ Phase 4 (camera), Phase 5 (PID), Phase 6 (laser), Phase 7 (mounting), Phase 8 (integration) — not started
