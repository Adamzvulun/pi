# Operating Guide

Practical reference for running the project. Daily commands, procedures
developed in real sessions, gotchas, and troubleshooting. Read this when
you come back to the project after a break, or when something stops
working.

> **Operator interface:** day-to-day operation goes through `control_panel.py`
> — the tkinter GUI. Install the desktop shortcut once with
> `bash ~/pi/scripts/install_desktop_shortcut.sh` and double-click the
> "Laser Tracker" icon (over VNC). Terminal commands in this guide are
> reserved for OS-level one-shots (`i2cdetect`, `lsusb`, `git pull`),
> first-time setup, and re-calibrations that the GUI subprocess-launches
> anyway. See §3.5 for the control panel walkthrough.

---

## 1. Daily workflow

### Architecture recap

- **Laptop** (`C:\Projects\pi`) — where all code is edited
- **GitHub** — central sync point, source of truth
- **Pi** (`~/pi`) — runs the code, auto-pulls from GitHub every minute

Code is **never** edited directly on the Pi. Edits happen on the laptop,
get pushed to GitHub, and the Pi picks them up automatically.

### Start of a session (on the laptop)

```bash
# Just open Claude Code at C:\Projects\pi and start editing.
# Optional: pull any changes from another machine first
git -C "C:\Projects\pi" pull
```

### Pushing code changes (on the laptop)

```bash
cd "C:\Projects\pi"
git add <files>             # or "git add -A" to add everything
git commit -m "message"
git push
```

Within ~60 seconds the Pi's cron will auto-pull. Or force it immediately
from the Pi:

```bash
cd ~/pi && git pull
```

### Running code on the Pi

```bash
ssh adam@LaserPi.local
cd ~/pi
source venv/bin/activate
python3 <script>.py
```

The `source venv/bin/activate` step is required for any Python script
that uses the Adafruit libraries (they live inside the venv).

### Hardware power-on order

1. Turn on the **12V PSU**. Red LED on the supply lights up. The LM2596
   immediately starts delivering 5V to the PCA9685 V+ rail.
2. Plug **USB-C** into the Pi. Wait ~30 seconds for it to boot.
3. Connect over **VNC** (for any GUI work — the control panel, the tracking
   overlay, the HSV tuner) or plain **SSH** (`ssh adam@LaserPi.local`) for
   non-GUI commands. The desktop launcher for `control_panel.py` is what
   gets used for actual operation; SSH/VNC terminals are only needed for
   `i2cdetect`, `lsusb`, or `git pull`.

**The order matters only for a tidy startup — there's no electrical
damage risk from reversing it.** But if the Pi is powered without the
servos, then you power on the servo PSU mid-session, the servos will
snap to whatever angle is currently being commanded (last value held by
the PCA9685 chip). Best to power both on before running any servo code.

---

## 2. Sanity check: is everything talking?

If you're not sure whether the Pi can see the PCA9685:

```bash
i2cdetect -y 1
```

Expected output:

```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: 40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
...
```

The `40` in row 40 column 0 is the PCA9685 responding on I2C address 0x40.
If you see ALL dashes, something's wrong — see troubleshooting below.

---

## 3. Servo scripts — how to use each one

### `test_servo.py` — sanity check the motion chain

Use when: you want to verify the PCA9685 + servos + power supply are all
working together with minimal movement.

```bash
python3 test_servo.py
```

Workflow:
1. Eyeball the bracket position before running. Note where it is.
2. Run the script.
3. Enter your estimated pan and tilt angles (e.g., `135` and `135` if the
   bracket looks centered). Be ready to **Ctrl+C** if the next step
   produces large unexpected motion.
4. Press Enter at the proceed prompt.
5. Script sends the estimate to both servos (may twitch), then sweeps
   pan ±10° and returns to start.

If motion is normal and small, the chain is healthy. If motion is huge
on the first command, your eyeball estimate was wrong — Ctrl+C, look at
the bracket, try again.

### `calibrate_servo.py` — interactive servo control

Use when:
- You want to find the bracket's safe angle limits (edge calibration)
- You need to drive the servos to specific angles for assembly work
- You want to verify the bracket moves correctly through its range

```bash
python3 calibrate_servo.py
```

Command reference (case-insensitive):

| Command   | What it does                                          |
|-----------|--------------------------------------------------------|
| `+`       | Move +<step> degrees (default 5°)                      |
| `-`       | Move -<step> degrees                                   |
| `+N`      | Move +N degrees (e.g. `+10`)                           |
| `-N`      | Move -N degrees                                        |
| `=N`      | Jump directly to absolute angle N (ramped, smooth)     |
| `step N`  | Change default step size (e.g. `step 2` for fine work) |
| `s`       | Mark current angle as a limit                          |
| `?`       | Show current angle, marks, step size                   |
| `help`    | Re-show the command list                               |
| `done`    | Finish this servo (need >=2 marks)                     |
| `q`       | Quit entirely — servos stay where they are             |

Every move ramps smoothly in 2° steps with 50ms sleeps. A `=135` from
`50` takes ~2 seconds and is completely smooth.

### Edge calibration procedure (full)

This is what produces the four numbers (`PAN_MIN`, `PAN_MAX`, `TILT_MIN`,
`TILT_MAX`) hardcoded in `servo.py`.

1. `python3 calibrate_servo.py`
2. Type `ready`
3. Pan estimate: best eyeball guess (e.g. `135`)
4. Tilt estimate: best eyeball guess
5. Press Enter — minimal motion expected
6. Select `0` (pan)
7. Step toward one side with `-` repeatedly. Watch the bracket. Listen.
8. **Stop** at any sign of:
   - Cable tension
   - Parts touching
   - Motor sound changing (buzz / growl / strain)
   - Servo body getting warm
9. Type `+` once to back off one step (5° safety margin).
10. Type `s` to mark this limit.
11. Type `=135` to jump back to center smoothly.
12. Step toward the other side with `+` repeatedly until strain.
13. Back off with `-` once, then `s`.
14. Type `done` — pan limits print.
15. Repeat for servo `1` (tilt).
16. At top-level `Select servo` prompt: `done`.
17. Four numbers print. **Record them.**

### Bracket reassembly procedure (when electrical center ≠ physical center)

If you find that electrical 135° on a servo doesn't correspond to physical
center of the bracket (typically because the servo gears were manually
rotated before bracket assembly), you need to remount the horns. The
software cannot fully compensate if the mismatch is large.

1. Power on the servo PSU. Servos energized.
2. `python3 calibrate_servo.py`
3. `ready`, enter accurate estimates (where servos currently are).
4. Pick servo `0`, type `=135`, then `s`, `s`, `done`. (The two fake marks
   are just to satisfy `done`'s minimum-2-marks check. Pan is now held
   at electrical 135°.)
5. Pick servo `1`, type `=135` (or `=160` to match TILT_CENTER if known),
   then `s`, `s`, `done`. (Tilt now held.)
6. Leave the script running at the top-level "Select servo" prompt —
   the servos continue to hold at their commanded angles indefinitely.
7. **With the servos holding**: unscrew the small Philips screw on top of
   the servo's horn. Lift the horn straight up off the splined shaft.
8. Manually rotate the bracket arm or top plate to its visual center
   (camera/laser plate pointing forward, no cable tension, equal room
   to rotate in both directions).
9. Lower the horn back onto the spline at this new orientation. The
   splines mesh in fixed positions (~15° apart), so accept the closest
   match to true center.
10. Screw the horn back down. Snug, not cranked.
11. Once both axes are remounted: at the top-level prompt, type `done`
    or Ctrl+C.

After this, re-run edge calibration (above) — limits will be different
because the mechanical reference has changed.

### Center the servos quickly (one-line)

```bash
python3 -c "import servo; servo.init()"
```

This configures and centers both servos. **Snaps** them to center from
wherever they are — DS3225 + LM2596 handle the spike fine, but you'll
hear a quick whine. If you want smooth motion, use `calibrate_servo.py`
with `=PAN_CENTER` and `=TILT_CENTER` instead. From the control panel
this is the "Center" button under the Servos section, or the emergency
stop button (which also turns the laser off).

---

## 3.5 The control panel (control_panel.py) — the operator GUI

`control_panel.py` is a single tkinter window that wraps every routine
operation. Adam launches it from the "Laser Tracker" icon on the Pi's
desktop (`bash ~/pi/scripts/install_desktop_shortcut.sh` installs it
once). It is the canonical operator interface — when something is
missing, that's a control-panel feature request, not a reason to drop
into the terminal.

| GUI section | Buttons / controls |
|---|---|
| Status header | Live pan / tilt angles, laser ON/OFF state (refreshed at 5 Hz) |
| Hardware | "Initialize hardware" — explicit init so the GUI doesn't claim devices on open |
| Servos | Center, pan / tilt sliders (clamped to calibrated limits), "Move to slider values", "Recalibrate limits…" (launches `calibrate_servo.py` as a subprocess) |
| Laser | "Enable laser controls" gate, "Fire 1 second" (with confirmation), "Force OFF" |
| Tools | "Start tracking test…" (launches `test_tracking.py`), "Tune HSV detector…" (launches `tune_detector.py`), "Camera smoke test" |
| System | "Reload config", "Show config values", "Shutdown Pi", "Reboot Pi" (with confirmations) |
| Log pane | Live `logging` output from anything running in the GUI process |
| Emergency stop | Big red button at the bottom — laser OFF, servos centered, no confirmation |

The GUI lazily inits hardware (you have to click "Initialize hardware"
first), releases its servo claim before launching a tracking subprocess
so two processes never fight over PCA9685, and runs a full cleanup
(laser off, servos centered, devices released, subprocesses terminated)
on window close.

---

## 4. Servo gotchas (things that are easy to forget)

### No position readback

The PCA9685 only sends pulses — it cannot read where a servo actually
is. Every script has to either:
- Track the position internally from the moment it sends the first pulse
- Or accept the user's eyeball estimate as the starting reference

This is why `servo.init()` *snaps* on first call: it has no way to know
where to ramp from. Subsequent moves in the same script ramp because the
module remembers what it last commanded.

### Spline granularity (~15°)

Horn-to-shaft splines on the DS3225 only mesh at ~15° increments. After
remounting a horn, the bracket may be up to ~7° off from true physical
center. That's why `TILT_CENTER` is 160° (asymmetric) instead of 135°
— the spline mesh forced it slightly off.

This is fine. Code uses `PAN_CENTER = (PAN_MIN + PAN_MAX) / 2` so the
"home" position is always the midpoint of the safe range, no matter
where that lands electrically.

### Don't auto-center on Ctrl+C

The test and calibration scripts deliberately do NOT center servos when
interrupted with Ctrl+C. Rationale: "center" might be past a hard stop
if the user was mid-calibration with unknown limits. Better to stop in
place and let the user reposition manually than to snap into something
that breaks the gears.

`servo.cleanup()` DOES center because by that point the safe limits are
already known (they're hardcoded).

### First command after power-on is a snap

When you first power the PSU and the PCA9685 starts sending PWM, the
servos snap to whatever angle is being commanded (the chip might be
sending stale pulses from a previous session, or zero pulses, depending).
This is unavoidable. Pre-position the bracket near center before
powering on to keep the snap small.

---

## 5. LM2596 voltage setup (do once, do right)

The LM2596 has a blue trimpot that sets output voltage. **You must set
it to 5.0V before connecting the output to anything sensitive.** If the
trimpot happens to be at the wrong position, the LM2596 could output
12V directly to the servo headers and destroy the DS3225 instantly.

Procedure:
1. Wire LM2596 IN+/IN- to the 12V PSU only. Do NOT connect output to
   anything yet.
2. Power on the PSU.
3. Multimeter (DC, 20V range) on LM2596 OUT+ and OUT-.
4. Turn the trimpot slowly with a small screwdriver until the meter
   reads exactly 5.0V. Clockwise typically raises voltage.
5. Power off the PSU.
6. Now wire OUT+ to PCA9685 V+ and OUT- to shared GND.
7. Power on. Verify with meter once more if you want.

Once set, the trimpot stays where it is. You don't need to redo this
unless you replace the LM2596.

---

## 6. Troubleshooting

### "Nothing moves" when running test_servo.py or calibrate_servo.py

Likely causes (in order):
1. **External PSU isn't on.** This is the #1 cause. Check the PSU's
   power LED. If you can't see it, wire a multimeter to confirm.
2. **You didn't press Enter at the proceed prompt.** The script waits.
3. **Servo connectors backward.** DS3225 wire order: brown(GND)–red(V+)–
   orange(signal). If reversed, no movement.
4. **LM2596 trimpot at near-zero.** Output voltage too low to drive servos.
5. **Loose connection in green terminal block.** Screws not tight.

### `OSError: [Errno 121] Remote I/O error`

This means I2C isn't reaching the PCA9685. Causes:
- SDA/SCL swapped (Pi pin 3 must go to PCA SDA, pin 5 to PCA SCL)
- No shared ground (Pi pin 6 → PCA GND must connect)
- PCA9685 unpowered (VCC pin not connected)
- I2C disabled in `raspi-config`

Quick test: `i2cdetect -y 1`. If it shows all dashes, none of the wiring
is working.

### Bracket moves a HUGE amount on first command

You ran a script that sent the first PWM and the bracket swung 90° or
more. Cause: electrical center on the servo is far off from where the
bracket is currently positioned (because the gears were manually
rotated at some point, or the horn was mounted at an awkward angle).

Fix: see "Bracket reassembly procedure" above. The mechanical mismatch
needs to be physically corrected; software cannot fully compensate.

### Servo hums but doesn't move

The servo is trying to drive against a mechanical stop. Either:
- The commanded angle is outside the bracket's physical range
- The bracket has bound on something (cable, debris)
- Two servos competing (shouldn't happen with this setup)

Fix: reduce the commanded angle. If you're in `calibrate_servo.py`,
back off with `-` or `+` until the humming stops.

### Servos move weakly or stutter

Power supply problem. Causes:
- LM2596 output voltage too low (re-measure with multimeter)
- LM2596 hitting current limit (>3A) — usually only happens during stall
- Loose wire on V+ or GND
- 12V PSU itself overloaded or failing

### "AttributeError: module 'servo' has no attribute 'X'"

You're calling a function that doesn't exist. See `servo.py` for the
actual public API:
- `init()`, `move_pan(kit, angle)`, `move_tilt(kit, angle)`
- `center(kit)`, `cleanup(kit)`
- `current_pan()`, `current_tilt()`

---

## 7. File reference (what each thing is for)

### Python files

| File                  | Purpose                                                |
|-----------------------|--------------------------------------------------------|
| `main.py`             | Final tracking loop (placeholder until Phase 8 lands)  |
| `control_panel.py`    | Operator GUI (tkinter) — the canonical interface       |
| `servo.py`            | Owner module for ServoKit/PCA9685 — all servo access   |
| `camera.py`           | Owner module for the LifeCam HD-3000 via `cv2.VideoCapture` |
| `detector.py`         | HSV target detection (blur → HSV → inRange → centroid) |
| `tracker.py`          | PID closed-loop tracking with coast + recenter modes   |
| `laser.py`            | Owner module for GPIO18 laser control                  |
| `config.py`           | Single source of truth for tuned constants             |
| `test_servo.py`       | Sanity test for servo chain                            |
| `test_tracking.py`    | End-to-end tracking with cv2 overlay (no laser)        |
| `test_laser.py`       | Standalone laser fire test                             |
| `calibrate_servo.py`  | Interactive servo control + edge calibration tool      |
| `tune_detector.py`    | HSV slider GUI for retuning detection                  |
| `scripts/install_desktop_shortcut.sh` | One-time installer for the control-panel desktop launcher |

### Doc files

| File                          | Purpose                                       |
|-------------------------------|-----------------------------------------------|
| `CLAUDE.md`                   | Project context for Claude Code sessions      |
| `README.md`                   | Project overview                              |
| `CHANGELOG.md`                | Session-by-session change log                 |
| `HANDOFF.md`                  | Current session quickstart (TL;DR + state)    |
| `docs/plan/`                  | Phase-by-phase build plan (one file per phase) |
| `docs/operating-guide.md`     | This file — practical how-to                  |
| `docs/wiring.md`              | Current physical wiring state                 |
| `docs/circuit-diagram.md`     | Mermaid diagrams of full system               |
| `docs/calibration.md`         | Record of all tuned values                    |
| `docs/setup-pi.md`            | One-time Pi setup instructions                |
| `docs/next-session-prompt.md` | Paste-ready prompt for fresh Claude sessions  |
| `problems/NNN-*.md`           | One file per problem encountered + fix        |

### Where calibrated values live

- **Servo angle limits** (`PAN_MIN`/`PAN_MAX`/`TILT_MIN`/`TILT_MAX`) —
  `servo.py`, mirrored in `docs/calibration.md`.
- **HSV target range** (`HSV_LOWER`/`HSV_UPPER`) — `config.py`, mirrored
  in `docs/calibration.md`. Current: `np.array([79, 76, 0])` to
  `np.array([105, 255, 255])` (folded blue plastic bag, overhead lighting).
- **PID gains** (`KP_PAN`/`KP_TILT`/`KI_*`/`KD_*`/`PID_OUTPUT_LIMIT`) —
  `config.py`, mirrored in `docs/calibration.md`. Current: Kp=0.017
  (both axes), Ki=0, Kd=0, output limit 10°/frame, deadband 15 px.
- **Coast + recenter knobs** (`COAST_MAX_FRAMES`/`COAST_DECAY`/
  `COAST_MIN_CORRECTION_DEG`/`RECENTER_AFTER_COAST`/`RECENTER_STEP_DEG`)
  — `config.py`. See `CHANGELOG.md` entries for coast mode and recenter.
- **Boresight offset** (`BORESIGHT_X_OFFSET`/`BORESIGHT_Y_OFFSET`) — will
  live in `config.py` after Task 7B.4 (gated on Phase 6).

---

## 8. Phase status (quick view)

- ✅ **Phase 1–2**: OS install, libraries, initial breadboard hardware (Phase 2 superseded by Phase 3 rework)
- ✅ **Phase 3**: Servo control (`test_servo.py`, `calibrate_servo.py`, `servo.py`)
- ✅ **Phase 4**: Camera + target detection (USB webcam via `cv2.VideoCapture`, HSV detector tuned)
- ✅ **Phase 5**: PID closed-loop tracking with coast + recenter (Kp=0.017, deadband 15 px)
- ⏸ **Phase 6**: Laser integration — driver circuit built, software-verified; **blocked on dead bare-diode laser** ([problems/002-laser-dead.md](../problems/002-laser-dead.md))
- ⏳ **Phase 7A**: Permanent base + electronics mounting — actionable now, independent of the laser blocker
- ⏸ **Phase 7B**: Laser mount + boresight — gated on Phase 6
- ⏸ **Phase 8**: Final integration into `main.py` — gated on Phase 6
