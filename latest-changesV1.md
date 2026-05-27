# Latest Changes — V1 (session 2026-05-27)

**Audience:** the next Claude Code session. Read this **after** `CLAUDE.md`. It explains what happened in the previous session, why the codebase looks the way it does now, and what's still open.

---

## TL;DR

This session took the project from **"Phase 6 blocked on a dead laser diode"** to **"Phase 8 complete, demo-ready"**. Three big things changed:

1. **Laser hardware was replaced.** The original plan (bare 5 mW diode + IRLZ44N MOSFET driver + 220 Ω/100 kΩ/100 Ω resistors + 5 V supply on Pi pin 4) was abandoned. We now run a **3 V self-contained laser module direct-driven from GPIO18**. Three wires total — GPIO18 → laser red, laser black → GND. The MOSFET is no longer in the circuit. The breadboard is essentially just two wires now.

2. **Phase 7B (boresight) infrastructure was built but not actually applied.** `calibrate_boresight.py` exists and works from the GUI. `BORESIGHT_X_OFFSET` / `BORESIGHT_Y_OFFSET` exist in `config.py`. The tracker code does *not* currently apply the offset — the user physically aligned the laser dot to the camera crosshair (laser taped on top of the camera), so software compensation isn't needed. The calibration tool stays in the repo for future use if alignment ever drifts.

3. **Phase 8 demo (`main.py`) is built and working.** Replaces the old placeholder stub. State machine: DISARMED → ARMED → (FIRING → COOLDOWN) → ARMED. Launches from a big green "▶ RUN FULL DEMO" button in the control panel. End-to-end loop: camera → HSV detect → PID → servos → laser on operator confirmation.

Bonus: cleaned up all 11 bookv3 Mermaid diagrams to render with straight lines, added a hand-coded SVG wiring schematic, and disabled camera auto-exposure to stop the bracket from "dancing" during firing.

---

## What changed and why — in order

### 1. Bookv3 diagram review and edits

The user asked to review every `.mmd` file in `bookv3/diagrams/`, validate the data against `CLAUDE.md`, and make the rendered output less squiggly.

- **All 11 .mmd files** got `%%{init: {'flowchart': {'curve': 'linear', 'nodeSpacing': N, 'rankSpacing': N}}}%%` at the top. Mermaid's default `basis` curve produces bezier-smoothed edges that look squiggly. Switching to `linear` gives straight polylines with right-angle bends where dagre routes around blocks.
- **`bookv3/diagrams/README.md`** was created. Per-diagram review: validation against ground truth, exact chapter placement, one-line description, summary table.
- **`bookv3/diagrams/electrical-schematic.svg`** was added. A hand-coded SVG schematic in the conventional auto-wiring style (component blocks with proper symbols, orthogonal wires, junction dots, ground glyphs, title block with cells). Mermaid can't render electrical symbols, so this is the "real" wiring drawing for Chapter 15 §15.1.
- **`bookv3/diagrams/control-loop.mmd`** was re-oriented from `LR` to `TB` so the 8-node loop fits a portrait page.

These edits are mostly settled. **The MOSFET-era diagrams still need updating** (see Open Items below) — the laser hardware change happened *after* the diagrams were reviewed, so `laser-driver.mmd`, `full-schematic.mmd`, and `electrical-schematic.svg` describe a circuit that no longer exists. **This was handled in the post-session doc-update pass — diagrams now reflect the GPIO18-direct-drive reality.**

### 2. Laser hardware swap — MOSFET driver dropped

The previous bare diode was dead (`problems/002-laser-dead.md`). The user got a replacement: a small **3 V laser module** (brass cylinder with internal driver electronics), not a bare diode.

Iterated through wiring trials with the user:

1. User first wired the module across the always-on rails (`Pi pin 1 = 3V3 → red rail; Pi pin 9 = GND → blue rail; laser red → red; laser black → blue`). The laser came on continuously at boot, no software control possible.
2. We discussed the MOSFET driver as the canonical path, but the module's `3 V` rating means it's already at full brightness on the Pi's 3V3 rail. A MOSFET switching a 5 V supply doesn't add anything for this device.
3. Switched to **GPIO direct drive** — move the red wire from pin 1 to **pin 12 (GPIO18)**. Black stays on GND. `laser_dev.on()` drives the pin HIGH (3.3 V), and the module lights. `laser_dev.off()` drives it LOW, module dark.
4. Tested via `test_laser.py` — works, full brightness, fully software-controlled. **Phase 6 unblocked.**

Code-side: `laser.py` was already designed against `gpiozero.LED(18)` from day one, so it works unchanged. The internal `LASER_PIN = 18` comment was updated to describe the new circuit. A failed retry attempt I added in `init()` to defend against a GPIO-busy race was later removed (see #5).

**Current laser circuit** (per `CLAUDE.md`'s wiring table after my updates):

```
Pi GPIO18 (pin 12) ────► laser RED (+, anode)
                         │
                         ▼  (internal driver + current limiter)
                         │
                         ▼
Pi GND (pin 9)    ◄──── laser BLACK (−, cathode)
```

No MOSFET. No external resistors. No 5 V supply. The module's built-in driver handles current limiting.

### 3. Boresight calibration tool — Phase 7B Task 7B.4

Adam mounted the laser module by **taping it on top of the camera** and physically aligning the laser cross to the camera cross. With careful manual alignment the boresight offsets are effectively zero — no software compensation needed. But the infrastructure to *measure* the offset exists for the future.

- **`calibrate_boresight.py`** — new subprocess-launched cv2 tool. Workflow:
  - Live camera view with a cyan crosshair at frame center
  - `f` = 3 s countdown, fire laser briefly, capture frame, auto-detect the laser dot, switch to REVIEW mode
  - In REVIEW: left-click to relocate the marker if auto-detection picked the wrong spot, `s` to save, `r` to re-fire, `q` to quit
  - Saves `BORESIGHT_X_OFFSET` / `BORESIGHT_Y_OFFSET` to `config.py` via regex replace
- **`config.py`** — `BORESIGHT_X_OFFSET` / `BORESIGHT_Y_OFFSET` added (default 0/0)
- **`control_panel.py`** — new "Boresight calibration..." button in the Laser section, gated on laser-controls-enabled

There was a real engineering battle to get the subprocess hand-off working (see #5). Once that was fixed, the tool runs cleanly from the GUI.

**Status: tool exists, was demonstrated working by the user, but the values stored in `config.py` are still 0/0 because Adam didn't actually run a measurement after physical alignment.** `tracker.py` doesn't currently consume the boresight values (see next section).

### 4. Tracker boresight wiring (added, then removed)

I initially patched `tracker.py` so `pan_error` and `tilt_error` added `BORESIGHT_X_OFFSET` / `BORESIGHT_Y_OFFSET` before going to the PID. The user then said "the laser is taped on top of the camera and aligned with the cross — return to how it was, center of image is where the laser fires and where lock is." So I **reverted** that change.

The current tracker code:

```python
pan_error  = target_x - config.FRAME_CENTER_X       # no boresight applied
tilt_error = target_y - config.FRAME_CENTER_Y
```

The `deadband_override` parameter I added to `tracker.update()` for the firing-state widen-deadband experiment (see #7) **stays in the code as a tuning knob** but is no longer called from `main.py`.

### 5. Phase 8 — full integration demo (`main.py`)

Replaced the placeholder `main.py` with the real integration loop. Same imports as `test_tracking.py` plus `laser`.

**State machine** drives the overlay color and what's allowed:

| State | Banner color | Banner text | Tracking? | Can fire? |
|---|---|---|---|---|
| `DISARMED` | dark gray | `DISARMED  -  press A to arm` | yes | no |
| `ARMED` + not locked | muted slate | `ARMED  -  waiting for lock` | yes | no (target not in deadband) |
| `ARMED` + locked | solid green | `LOCKED  -  press F to fire` | yes | yes |
| `FIRING` | dark red | `FIRING` | yes | no |
| `COOLDOWN` | muted teal | `COOLDOWN N.Ns` | yes | no |

Keys: `A` toggles arm, `F` fires (requires armed + locked + not cooling down), `Q` quits cleanly.

Timing knobs in `config.py`:
- `LASER_FIRE_DURATION_S = 2.5` (was 0.5s initially — too short to register visually)
- `LASER_COOLDOWN_S = 1.0`

**Control panel integration** — new big green `tk.Button` in a dedicated "Demo" section, with a confirmation dialog warning about beam path safety. The handler:
- Releases both servos AND laser (main.py re-acquires both)
- Closes gpiozero's pin_factory (the GPIO hand-off fix — see #6)
- Sleeps 0.3 s
- Launches `main.py` via the same subprocess mechanism as the other GUI-launched scripts

### 6. The gpiozero subprocess GPIO contention bug

This was the nastiest debugging session of the day. Boresight tool launched from the GUI failed with `lgpio.error: 'GPIO busy'` even though the GUI explicitly called `laser.cleanup()` first. Subsequent retries failed with `gpiozero.exc.GPIOPinInUse: pin GPIO18 is already in use by <gpiozero.LED object closed>` (note: *closed* object — that was the giveaway).

**Diagnosis:**
- `LED.close()` releases the gpiozero-level reservation and calls `lgpio.gpio_free`, BUT it keeps the chip handle (`/dev/gpiochip0`) open inside the singleton `pin_factory`.
- `subprocess.Popen` forks before exec. The chip FD is inherited by the child via `fork()` even though Python's `close_fds=True` closes it after `exec()` — there's a brief kernel-level window where the pin still appears claimed via the inherited FD.
- Child's `lgpio.gpio_claim_input` fails with "GPIO busy".
- My naive retry logic in `laser.init()` made it worse: gpiozero's `reserve_pins()` succeeded on attempt 1 (Python-level), then `lgpio.gpio_claim_input` failed (kernel-level), leaving a stale Python-level reservation that blocked all subsequent retries with `GPIOPinInUse`.

**Fix (in `control_panel.py` for both `_on_boresight` and `_on_run_demo`):**

```python
from gpiozero import Device
if Device.pin_factory is not None:
    Device.pin_factory.close()    # release the chip handle entirely
    Device.pin_factory = None     # gpiozero lazily recreates on next LED()
time.sleep(0.3)                   # let kernel-level state settle
self.active_subprocess = _launch_script(filename)
```

When the subprocess exits, the control panel's `_tick()` re-acquires the laser if servos are still up:

```python
if self.laser_dev is None and self.kit is not None:
    self.laser_dev = laser.init()
```

Also removed the retry in `laser.init()` — it was masking the real bug and adding nothing useful.

**Defensive logging added in parallel:**

- `_launch_script()` now redirects subprocess stdout/stderr to `~/pi/last-subprocess.log` (truncated per launch, `python3 -u` for line-buffered output).
- `_tick()` detects non-zero exit codes and dumps the tail of that log into the GUI's log pane as `ERROR` lines, prefixed with `| `, so future subprocess crashes are visible without dropping to a terminal.

### 7. Bracket dance during firing — false starts and the real fix

The user reported "when the laser is on and being fired the camera starts to twitch and dance".

**First attempt** (wrong): widen the tracker's deadband to 40 px during `FIRING` and `COOLDOWN` states. Reasoning: detector centroid jittered ±15-25 px during fire, and the normal 15 px deadband meant every jitter triggered a small correction. Wider deadband absorbs jitter. Implementation: new `deadband_override` parameter on `tracker.update()`, called with `config.FIRE_DEADBAND_PX = 40` during firing.

Result: bracket stopped dancing, but **also stopped tracking** real target moves during fire (40 px is enough that small genuine moves are ignored too). User: "it's still not tracking when fired."

**Second attempt** (correct): identify the actual root cause and fix it. **The LifeCam's auto-exposure** was dropping overall gain when the bright laser dot appeared in the frame. That dimmed the blue target, shifted its HSV signature, and caused the detector centroid to wobble. Wider deadband was treating symptoms, not the cause.

Real fix:
- `config.CAMERA_DISABLE_AUTO_EXPOSURE = True`
- `config.CAMERA_EXPOSURE = 250` (V4L2 `exposure_absolute`, tunable per lighting)
- `camera.init()` sets `CAP_PROP_AUTO_EXPOSURE = 1` (V4L2 manual mode) then `CAP_PROP_EXPOSURE = 250`. Logs the actual values set/readback so driver quirks are visible.

With AE off, the image is stable when the laser fires → detector is stable → normal 15 px tracking deadband works fine during fire. Reverted `main.py`'s `deadband_override` call. The `deadband_override` parameter stays in `tracker.update()` as a tuning knob.

User confirmed: tracking now works during fire, no dance.

### 8. Overlay cleanup

The user also complained the demo overlay was "obnoxious" — pulsing greens, red strobes, star symbols (`★`), em-dashes (`—`), degree signs (`°`). The non-ASCII characters were rendering as boxes/question marks because OpenCV's Hershey font is ASCII-only. The animations were just visual noise.

Cleanup:
- All non-ASCII removed — plain ASCII labels everywhere
- Solid muted colors per state, no pulsing or strobing
- Slimmer banners and info strips
- Removed the boresight readout row (was always 0/0 anyway after the boresight revert)

### 9. tk.Button vs ttk.Button bug

Caught and fixed in passing: the new green "RUN FULL DEMO" button is a `tk.Button` (classic widget — supports `bg=`/`fg=` for color styling). The existing GUI widget-state code called `.state(["!disabled"|"disabled"])` on everything, which only works on `ttk.Widget`. Added a `_set_enabled()` helper that dispatches on `isinstance(w, ttk.Widget)` and uses `.configure(state=...)` for classic tk widgets. Future colored tk buttons "just work".

---

## Current state of every code file

| File | What changed | Why |
|---|---|---|
| `main.py` | Replaced placeholder with full demo loop, state machine, overlay | Phase 8 |
| `tracker.py` | Reverted boresight wiring; added `deadband_override` param | Laser physically aligned, no compensation needed |
| `laser.py` | Updated LASER_PIN comment to describe direct GPIO drive | Hardware change |
| `camera.py` | Disables AE, sets fixed exposure; new `import config` | Stop AE jitter during firing |
| `detector.py` | unchanged | — |
| `servo.py` | unchanged | — |
| `config.py` | Added `LASER_FIRE_DURATION_S`, `LASER_COOLDOWN_S`, `FIRE_DEADBAND_PX`, `CAMERA_DISABLE_AUTO_EXPOSURE`, `CAMERA_EXPOSURE`, `BORESIGHT_X_OFFSET`, `BORESIGHT_Y_OFFSET` | Phase 8 / camera fix / boresight scaffolding |
| `control_panel.py` | Added "Boresight calibration..." button and "▶ RUN FULL DEMO" button. Added subprocess logging to `last-subprocess.log`. Added `_set_enabled` helper. Added pin_factory close before subprocess launch. Auto-reinits laser on subprocess exit. | Phase 7B + Phase 8 + subprocess GPIO bug fix |
| `calibrate_boresight.py` | NEW file | Phase 7B Task 7B.4 |
| `bookv3/diagrams/*.mmd` (all 11) | Added linear-curve init block | Straight-line rendering |
| `bookv3/diagrams/control-loop.mmd` | LR → TB | Fit portrait page |
| `bookv3/diagrams/README.md` | NEW file | Per-diagram review |
| `bookv3/diagrams/electrical-schematic.svg` | NEW file | Reference-style schematic |

---

## What's tested and working

Confirmed by the user (Adam) end-to-end on the actual hardware:
- ✅ Laser fires from `test_laser.py` (GPIO direct drive at 3.3 V)
- ✅ Laser fires from the control panel's "Fire 1 second" button
- ✅ Boresight calibration tool opens from the GUI and runs
- ✅ Full demo runs from "▶ RUN FULL DEMO" button — tracking, locking, firing, cooldown
- ✅ Bracket sits at center until first detection (no false startup motion)
- ✅ Bracket follows the target during firing (after AE-off fix)
- ✅ Overlay is clean — no question marks, no pulsing, ASCII-only

---

## Files NOT YET updated to reflect current state

After the doc-update pass at end of session, **all of these were updated**:

- ✅ `CLAUDE.md` — hardware table, wiring snapshot, project state, design decisions
- ✅ `problems/002-laser-dead.md` — marked resolved with the actual resolution path
- ✅ `README.md` — describes demo, removes "main.py is placeholder" language
- ✅ `docs/plan/phase-6-laser.md` — marked complete with the GPIO-direct-drive resolution
- ✅ `docs/plan/phase-7-mounting.md` — Task 7B.4 marked complete
- ✅ `docs/plan/phase-8-integration.md` — marked complete
- ✅ `docs/calibration.md` — boresight section placeholder updated to reflect physical alignment
- ✅ `bookv3/diagrams/laser-driver.mmd` — redrawn without MOSFET (or replaced with note)
- ✅ `bookv3/diagrams/full-schematic.mmd` — MOSFET path removed
- ✅ `bookv3/diagrams/electrical-schematic.svg` — MOSFET removed
- ✅ `bookv3/diagrams/README.md` — entries for changed diagrams updated
- ✅ `bookv3/chapters/10-components.md` — laser section rewritten
- ✅ `bookv3/chapters/11-architecture.md` — ASCII schematic updated
- ✅ `bookv3/chapters/15-solution-documentation.md` — §15.1 prose updated

---

## Open items for the next session

1. **`docs/calibration.md` boresight values still 0/0.** Adam didn't actually run the boresight calibration tool — he aligned the laser physically. If alignment ever drifts, run `calibrate_boresight.py` from the GUI at ~1.5 m distance and update the file. Until then, `BORESIGHT_X_OFFSET / Y_OFFSET = 0` is correct.

2. **Camera exposure may need per-environment tuning.** `config.CAMERA_EXPOSURE = 250` is a guess for typical indoor light. If the demo gets moved to a different room or the lighting changes significantly, re-tune by running `tune_detector.py` to look at the current frame and adjusting until the blue target is solidly within the HSV range. If the image looks too dark/bright at 250, try 100-600.

3. **The HSV detection range was tuned with AE on.** Now that AE is off, the blue target's HSV signature may have shifted slightly. Adam said tracking works, so in practice this seems fine, but if the detector ever struggles, re-running `tune_detector.py` with the new fixed exposure is the first thing to try.

4. **Two MOSFET driver references remain in the book that might still need updating** if I missed them:
   - `docs/wiring.md` — not read this session, may still describe the MOSFET path
   - `docs/circuit-diagram.md` — same caveat

5. **The boresight tool's "live aim while watching the dot" UX is awkward.** Currently the operator has to: open boresight tool → press `l` to see dot → close tool → adjust sliders → reopen. A future improvement: add arrow-key servo control inside the boresight cv2 window. Not urgent — Adam's manual alignment was good enough that boresight isn't needed in practice.

---

## Reading order for the next session

1. **This file** (latest-changesV1.md) for session-1 context
2. **CLAUDE.md** for current hardware/architecture/code conventions
3. **docs/plan/README.md** for phase status (all phases ✅ now)
4. **docs/calibration.md** for tuned values
5. Specific phase docs only if working on a specific area

---

## Quick command reference (current state)

```bash
# Daily run — Adam launches from the desktop shortcut, but equivalent:
cd ~/pi && source venv/bin/activate
python3 control_panel.py

# Inside the GUI:
#   1. Initialize hardware
#   2. Enable laser controls (tick checkbox)
#   3. ▶ RUN FULL DEMO            → main.py
#   4. Boresight calibration...   → calibrate_boresight.py
#   5. Start tracking test...     → test_tracking.py  (no firing)
#   6. Tune HSV detector...       → tune_detector.py
#   7. Recalibrate limits...      → calibrate_servo.py

# Standalone runs (rarely needed now):
python3 test_laser.py             # 1s pulse, basic laser test
python3 main.py                   # full demo without going through panel
```

If the GUI subprocess hangs or crashes, check `~/pi/last-subprocess.log` for the captured stdout/stderr.
