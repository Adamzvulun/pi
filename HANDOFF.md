# Handoff — current state of the Laser Tracker project

This file is the first thing a new Claude Code session (or a human picking the project back up) should read. It's the TL;DR: what's done, what's blocked, what's next, and how to keep working in the same style. For depth on any item, follow the link.

---

## What this project is

Autonomous laser tracker on a Raspberry Pi 4B. A USB webcam mounted on a pan-tilt servo bracket detects a colored target via HSV thresholding, a PID closed loop keeps the target centered in the frame, and a GPIO-driven laser fires on operator confirmation. Adam's school final project. Read [`CLAUDE.md`](CLAUDE.md) for full hardware context, module rules, and coding style.

---

## TL;DR of where we are

- **Phases 1–5 complete.** Closed-loop tracking runs end-to-end on the Pi: camera → HSV detector → PID → servos. Tuned values: `Kp=0.017`, `Ki=0`, `Kd=0`, deadband=15 px, output limit=10°/frame, with coast (1 s of inertia after target loss) and recenter (smooth ramp back to home after coast fails).
- **Phase 6 blocked** on a dead bare-diode laser. The MOSFET driver circuit is built and code is written and pushed — only the diode itself is non-functional. See [`problems/002-laser-dead.md`](problems/002-laser-dead.md) for the full diagnosis path.
- **Phase 7A (permanent base + electronics mounting) is the next actionable phase.** Independent of the laser, runs in parallel with waiting for a replacement.
- **Phases 7B (laser mount + boresight) and 8 (integration `main.py`) are gated on Phase 6.**
- **`control_panel.py`** is the operator GUI — every hardware test now runs from there, not from the terminal. Desktop shortcut installed via `scripts/install_desktop_shortcut.sh`.

---

## Hardware on hand

| Item | State |
|------|-------|
| Pi 4B (8GB), hostname `LaserPi`, user `adam` | Working |
| 2× DS3225 servos on pan-tilt bracket, channels 0/1 of PCA9685 | Calibrated: PAN 50–220°, TILT 115–205° |
| PCA9685 at I2C 0x40 | Working, powered from Pi 5V (logic) + LM2596 (servo V+) |
| LM2596 buck converter (5.0 V) fed by 12V 5A PSU | Working |
| Microsoft LifeCam HD-3000 USB webcam, 640×480 BGR | Working, 3D-printed mount holds it on the tilt plate |
| MOSFET driver: IRLZ44N + 220Ω gate + 100kΩ pulldown + 100Ω laser limiter | Built on MB-102 breadboard, pulldown verified |
| Bare-diode 5mW 650nm laser, red/black wires | **DEAD — replacement required** |

Wiring snapshot in [`CLAUDE.md`](CLAUDE.md#current-wiring-snapshot-post-problem-001-resolution).

---

## Read these in order before doing anything

1. [`CLAUDE.md`](CLAUDE.md) — full project context, hardware constraints, module ownership rules, coding style, current state bullets
2. [`docs/plan/README.md`](docs/plan/README.md) — phase-by-phase status with links to each phase file
3. [`docs/operating-guide.md`](docs/operating-guide.md) — daily commands, procedures, troubleshooting
4. [`docs/calibration.md`](docs/calibration.md) — all tuned values (servo limits, HSV range, PID gains)
5. [`problems/`](problems/) — known hardware issues and their fixes (001-servo-power, 002-laser-dead)
6. Memory files in `~/.claude/projects/C--Projects-pi/memory/` — Adam's persistent preferences (auto-commit, GUI-first workflow)

---

## Adam's working preferences (override default Claude behavior)

These are persistent and have been explicitly stated. Don't relearn them every session.

- **Auto-commit and push** at the end of every unit of work. Don't ask "should I commit?" — just `git add → commit → push`. See [`feedback_auto_commit_push.md`](../../Users/Owner/.claude/projects/C--Projects-pi/memory/feedback_auto_commit_push.md).
- **All hardware/script tests go through `control_panel.py`**, not terminal commands. If you'd say "run `python3 test_X.py`", instead say "click X in the control panel." If a feature is missing, **add it to the panel**, don't tell Adam to use the terminal. See [`feedback_use_control_panel.md`](../../Users/Owner/.claude/projects/C--Projects-pi/memory/feedback_use_control_panel.md).
- **Beginner with electronics and Linux.** Explain WHY, not just what. Comment code generously. Walk through trade-offs.
- **Prose over bullets** in chat responses. Minimal headers. Compact.
- **No kill switch, no safety glasses** — accepted, don't push back.
- **VNC for any GUI script**; SSH for terminal-only. Don't ask Adam to do GUI work over SSH.

---

## Module ownership rules (don't bypass)

| Module | Owns | Other files must not import |
|---|---|---|
| `servo.py` | ServoKit + I2C + PCA9685 | `adafruit_servokit`, `adafruit_pca9685` |
| `camera.py` | `cv2.VideoCapture` for the LifeCam | (cv2 itself is fine to import for image work) |
| `laser.py` | GPIO18 + gpiozero | `gpiozero` directly for the laser pin |
| `detector.py` | HSV detection logic | — |
| `tracker.py` | PID loop | `simple_pid` |
| `config.py` | All tuned constants | — |
| `control_panel.py` | Operator GUI (tkinter) | (it's the consumer, imports the others) |

Adding new functionality goes inside the right owner module. Don't duplicate a hardware path in a new file.

---

## Current actionable work — Phase 7A

[Phase 7A — permanent base + electronics mounting](docs/plan/phase-7-mounting.md). Independent of the laser.

- Cut/sand a wooden base (~30 × 40 cm plywood, ~12 mm thick).
- 3D-print a pan-servo holder (snug socket for DS3225 body, wide base for stability).
- Mount the Pi (M2.5 standoffs), PCA9685 (M3 standoffs), LM2596, breadboard.
- Route cables so the pan sweep doesn't bind anything.

Adam has demonstrated 3D printing capability (camera mount). Phase 7B (laser mount + boresight) and Phase 8 (integration `main.py`) wait for Phase 6.

---

## When the replacement laser arrives

1. Power off everything (Pi + 12V).
2. Attach: red wire → 100Ω resistor side; black wire → MOSFET drain side.
3. Power on Pi. **Laser MUST be OFF before any code runs.** If it lights at boot, gate pulldown is wrong — power off immediately.
4. In the control panel: **Initialize hardware** → tick **Enable laser controls** → **Fire 1 second**.
5. Should see a red dot for 1 second on a matte wall.
6. Phase 6 closes. Phase 7B (mount laser on tilt plate + boresight) becomes actionable.

If the new diode also doesn't light, the MOSFET path is suspect — test with a regular LED + 100Ω as a known-good load. Full diagnostic sequence in [`problems/002-laser-dead.md`](problems/002-laser-dead.md).

---

## How to start the next Claude Code session

Adam will paste the [`docs/next-session-prompt.md`](docs/next-session-prompt.md) content into a fresh Claude Code window. That prompt instructs the new session to read this file and the others listed above before responding.

---

## Project origin

Originally bootstrapped in a planning conversation in regular Claude chat, then handed off to Claude Code on Adam's laptop (`C:\Projects\pi`). The original kickoff handoff (parts list, initial wiring state, "your first task" skeleton instructions) is no longer accurate — most of it is captured in current form in CLAUDE.md, plus the phase docs and problem records. This file replaces the original handoff.
