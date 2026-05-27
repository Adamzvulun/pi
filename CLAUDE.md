# CLAUDE.md — Laser Tracker Project Context

This file is read by Claude Code at the start of every session. Read it fully before writing any code.

**Also read these companion docs:**
- **`latest-changesV1.md`** — handoff from the previous session. Captures *why* the current code looks the way it does (MOSFET driver was removed, boresight tool exists but isn't applied, AE was disabled). Read this first if you didn't author the current state.
- **`docs/plan/`** — phase-by-phase build plan, one file per phase. All phases ✅ now; mostly a historical record at this point.
- **`docs/operating-guide.md`** — practical reference: daily commands, scripts and how to use them, troubleshooting, procedures we developed.
- **`docs/calibration.md`** — recorded tuned values (servo limits, HSV, PID, boresight).
- **`problems/`** — one file per problem encountered, with diagnosis and fix.

CLAUDE.md gives you the hardware and architecture context; the docs above tell you what to build and how to actually run things.

---

## What this project is

Autonomous laser tracking system on a Raspberry Pi 4B. Camera detects a target, two servos (pan + tilt) keep it centered via PID control, then a 3 V laser module fires on user confirmation.

**Status:** Phases 1–8 all complete. The full demo (camera → detect → PID → servos → laser) runs from a "▶ RUN FULL DEMO" button in `control_panel.py` and is demo-ready.

**Read `latest-changesV1.md` for the previous session's deltas before doing anything destructive** — it captures non-obvious decisions like why the MOSFET driver was dropped and why the boresight tool exists but isn't currently applied.

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
- `python3-opencv` / `cv2` — image processing AND camera capture (via `cv2.VideoCapture` against the USB webcam)
- `python3-numpy` / `numpy` — array math
- `python3-gpiozero` / `gpiozero` — GPIO control
- `picamera2`, `rpicam-apps` — installed but currently unused (Pi 5 CSI camera on hand is incompatible with the Pi 4 CSI slot; the project uses a USB webcam instead). Keep installed in case a compatible CSI camera ever appears.

**Important:** The venv was created with `--system-site-packages`. This is why `cv2` and `numpy` are importable from within the venv even though they are apt packages, not pip packages. Do not attempt to pip-install these.

**Camera:** Microsoft LifeCam HD-3000 USB webcam on `/dev/video0`. `camera.py` opens it via `cv2.VideoCapture(0)` at 640×480 BGR. The kernel `uvcvideo` driver handles it — no install needed. OpenCV's GStreamer backend emits a "Cannot query video position" warning at open; it's benign, the v4l2 fallback works fine.

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
| Laser hardware | 3 V self-contained laser module (small brass cylinder with internal driver electronics + internal current limiter). NOT a bare diode. |
| Laser drive | GPIO18 (physical pin 12) direct — active HIGH at 3.3 V powers the module; LOW turns it off. No MOSFET, no external current-limit resistor — the module handles its own current limiting. |
| Laser ground | Pi pin 9 (GND) — laser black wire connects directly here. |
| Servo supply voltage | 5V regulated from LM2596 buck converter fed by 12V 5A PSU — provides up to ~3A, isolated from Pi rail (see `problems/001-servo-power.md`) |
| PCA9685 VCC source | Pi GPIO 5V (pin 2) directly — MB102 no longer in the circuit |
| Camera exposure | **Auto-exposure DISABLED** in `camera.init()`. Fixed exposure value `config.CAMERA_EXPOSURE = 250` (V4L2 manual mode). Required so the laser dot in the frame doesn't shift AE and destabilize the HSV detector during firing. |

## Operator workflow — use the control panel

`control_panel.py` is the canonical operator GUI for this project. Adam launches it from a desktop shortcut (installed via `scripts/install_desktop_shortcut.sh`) and runs all hardware tests, calibrations, and Pi-system commands through its buttons:

- **Full demo** → big green "▶ RUN FULL DEMO" button (subprocess-launches `main.py` — tracking + firing state machine)
- **Boresight calibration** → "Boresight calibration..." button (subprocess-launches `calibrate_boresight.py`) — measures laser-vs-camera pixel offset; currently produces 0/0 because the laser is physically aligned with the camera crosshair
- Tracking test → "Start tracking test…" button (subprocess-launches `test_tracking.py` — no firing)
- Laser test → "Initialize hardware" + "Enable laser controls" + "Fire 1 second"
- Servo recalibration → "Recalibrate limits…" button (subprocess-launches `calibrate_servo.py`)
- HSV tuning → "Tune HSV detector…" button (subprocess-launches `tune_detector.py`)
- Pi shutdown/reboot → GUI buttons (not `sudo shutdown`)
- Emergency stop → big red button at the bottom

**Subprocess GPIO note:** any GUI button that launches a subprocess needing GPIO18 (boresight, full demo) must release the gpiozero pin_factory in the parent before forking. Without that, the inherited chip handle causes `lgpio.error: 'GPIO busy'` in the child. The pattern is `Device.pin_factory.close(); Device.pin_factory = None; time.sleep(0.3)` before `subprocess.Popen`. See `_on_boresight` / `_on_run_demo` for the canonical implementation.

**Subprocess crash logging:** `_launch_script()` redirects child stdout/stderr to `~/pi/last-subprocess.log` (truncated per launch). On non-zero exit, `_tick()` tails the log into the GUI's log pane. So crashes are visible without dropping to a terminal.

When writing instructions, point at the GUI button, not a terminal command. If a feature is missing from the panel, ADD IT TO `control_panel.py` rather than telling the user to use the terminal. Terminal use is reserved for OS-level one-shots (`i2cdetect`, `lsusb`, `git pull`) and first-time setup that runs before the GUI is available.

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
| `BORESIGHT_X_OFFSET` | Task 7.4 | Pixel offset between camera aim and laser dot (x). Currently 0 — laser physically aligned. Not applied in tracker.py. |
| `BORESIGHT_Y_OFFSET` | Task 7.4 | Pixel offset between camera aim and laser dot (y). Same situation as X. |
| `LASER_FIRE_DURATION_S` | Task 8.1 | How long the laser stays on per fire command. Currently 2.5 s. |
| `LASER_COOLDOWN_S` | Task 8.1 | Lockout after each fire. Currently 1.0 s. |
| `FIRE_DEADBAND_PX` | Phase 8 fix | Widened deadband available via `tracker.update(deadband_override=...)`. Unused after AE was disabled — kept as a tuning knob. |
| `CAMERA_DISABLE_AUTO_EXPOSURE` | Phase 8 fix | True = lock the LifeCam to fixed exposure. Required for stable HSV detection during firing. |
| `CAMERA_EXPOSURE` | Phase 8 fix | V4L2 `exposure_absolute` value when AE is off. Default 250; tune per room lighting. |

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

- ✅ Phase 1–2: OS, libraries installed
- ✅ Phase 3 prep: repo skeleton, cron auto-pull, all libraries installed
- ✅ **Problem 001 resolved**: MB102 removed from circuit. LM2596 buck converter supplies servo V+ rail at 5V from the 12V PSU. Pi GPIO 5V powers PCA9685 VCC directly. See `problems/001-servo-power.md`.
- ✅ **Pan-tilt bracket reassembled** with both servos held at electrical 135° during mounting → electrical center now corresponds to physical center on both axes.
- ✅ **Phase 3 complete.** Servo limits `PAN_MIN=50`, `PAN_MAX=220`, `TILT_MIN=115`, `TILT_MAX=205`. See `docs/calibration.md`.
- ✅ **Phase 4 complete.** LifeCam HD-3000 → `camera.py` → `detector.py` (HSV) returns `(x, y)` of a blue target. HSV range `[79,76,0]`–`[105,255,255]` tuned against a folded 10×20 cm blue plastic bag.
- ✅ **Phase 5 complete.** Closed loop end-to-end. `tracker.py` calls `servo.move_*` with `ramp=False`. Tuned: `Kp=0.017`, `Ki=Kd=0`, `PID_OUTPUT_LIMIT=10°`, `TRACKING_DEADBAND_PX=15`.
- ✅ **Problem 002 resolved**: original bare diode was DOA. Replaced with a 3 V laser module direct-driven from GPIO18. MOSFET driver path abandoned — module's internal driver handles current limiting. See `problems/002-laser-dead.md`.
- ✅ **Phase 6 complete.** `laser.py` + `test_laser.py` work end-to-end against the new 3 V module. `laser_dev.on()` puts GPIO18 HIGH → module lights. `laser_dev.off()` → dark.
- ✅ **Phase 7B complete.** `calibrate_boresight.py` written and works from the GUI. Boresight values currently 0/0 in `config.py` because the laser is physically taped on top of the camera with crosses aligned — software compensation not needed. Tool stays for future use if alignment drifts.
- ⏳ **Phase 7A not done** — electronics still on the temporary breadboard layout. Cosmetic / robustness only; nothing blocks demos. Could be skipped entirely if presentation deadline is tight.
- ✅ **Phase 8 complete.** `main.py` replaced the placeholder with a real tracking + firing state machine. Big green "▶ RUN FULL DEMO" button in the control panel launches it. Working end-to-end on the actual hardware (Adam confirmed 2026-05-27).
- ✅ **Camera AE disabled (Phase 8 follow-up):** the laser dot caused the LifeCam's auto-exposure to drop gain, which destabilized the HSV detector during firing → bracket "danced". `camera.init()` now sets `CAP_PROP_AUTO_EXPOSURE = 1` (V4L2 manual) and `CAP_PROP_EXPOSURE = 250`. Side effect: if the room lighting changes substantially, the fixed exposure may need re-tuning via `config.CAMERA_EXPOSURE` and a re-run of `tune_detector.py`.

### Current wiring snapshot

```
                                      ┌─→ DS3225 pan (channel 0)
                                      │
12V 5A PSU ─→ LM2596 (5.0V) ─→ PCA9685┤
            └─→ (LM2596 GND) ─→ GND   └─→ DS3225 tilt (channel 1)

Pi pin 2 (5V)  ─→ PCA9685 VCC          (logic power)
Pi pin 3 (SDA) ─→ PCA9685 SDA          (I2C data)
Pi pin 5 (SCL) ─→ PCA9685 SCL          (I2C clock)
Pi pin 6 (GND) ─→ PCA9685 GND          (shared with LM2596 GND)

Pi pin 12 (GPIO18) ─→ laser red wire   (anode +, 3V module driven directly)
Pi pin 9  (GND)    ─→ laser black wire (cathode −)

USB: LifeCam HD-3000 → any free USB-A port on the Pi
```

No MOSFET, no MB102, no external resistors on the laser path. The 3 V module's internal driver handles current limiting.
