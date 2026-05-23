# Phase 5 — PID Closed-Loop Tracking ⏳ IN PROGRESS

## Status

`tracker.py` and `test_tracking.py` are written. PID gains in [config.py](../../config.py) are conservative starting values that almost certainly need empirical tuning — and the sign of `KP_PAN` / `KP_TILT` may need flipping depending on servo mounting (see "sign caveat" below).

This is the first phase where camera, detector, servos, and PID controllers all run together.

## What's done and what's left

| Step | Status |
|------|--------|
| `tracker.py` written | ✅ |
| `test_tracking.py` written | ✅ |
| PID constants added to `config.py` | ✅ (placeholders — Kp=0.05, Ki=0, Kd=0.01) |
| Camera mounted on tilt plate | ✅ 3D-printed mount, rigid |
| **First real run of `test_tracking.py` on Pi via VNC** | ⏳ |
| **Confirm tracking direction (flip Kp sign if needed)** | ⏳ |
| **Tune Kp, then Kd, then Ki if needed** | ⏳ |
| **Record tuned gains in `config.py` and `docs/calibration.md`** | ⏳ |

Reference details for the built modules are at the bottom of this file.

---

# What to do now — step by step

## Step 1 — Camera mount ✅ done

A 3D-printed mount holds the LifeCam HD-3000 rigidly to the tilt plate. If you ever need to redo it, the requirements are:

- Camera lens points roughly forward (where the laser will eventually point)
- USB cable has 10+ cm of slack — pan sweep shouldn't tug on the camera
- Camera doesn't wobble when you nudge the bracket by hand
- Nothing on the bracket (cable, camera body) intrudes into the camera's field of view

Permanent mounting refinements happen in Phase 7B alongside the laser mount and the boresight calibration.

## Step 2 — Pre-flight checks before running

Before launching `test_tracking.py`, confirm:

- [ ] **12V PSU is plugged in and switched on.** The LM2596 LED should be lit. Without 12V the servos can't physically move — the loop runs but the bracket stays still and you get nothing but `clamped` warnings. (This bit us once already.)
- [ ] **Latest code is on the Pi.** From the laptop: `git log -1 --oneline` should match what's on the Pi. If you've made changes since the last Pi pull, wait 60 seconds for the auto-pull cron or run `git pull --rebase --autostash` on the Pi.
- [ ] **VNC into LaserPi** — `test_tracking.py` opens an OpenCV window; plain SSH can't show it.

## Step 3 — Stay clear of the bracket's sweep arc

`servo.init()` snaps both servos to center at script start. If the tilt servo drifted while unplugged, the snap motion may be large and sudden. The servos and PSU can handle it, but you don't want a hand or the USB cable in the way. Keep clear during the first 1–2 seconds after launch.

## Step 4 — Run test_tracking.py

In a terminal on the Pi desktop (the VNC one — not plain SSH, since the script opens an OpenCV window):

```bash
cd ~/pi
source venv/bin/activate
python3 test_tracking.py
```

A window titled `tracking` opens. You'll see:

- **Red cross** at the frame center (the target should be driven *here*).
- **Green circle** at the detected target centroid (only when the detector finds the blue bag).
- **Overlay text** showing current pan/tilt angles, pixel error, and per-frame PID correction.

If you don't see all of that, recheck Phase 4's smoke test — the loop depends on detection working.

## Step 5 — First behavior test: which way does it move?

Click on the `tracking` window to give it focus (`waitKey` needs window focus, same as Phase 4).

Hold the blue target **slightly to the right of center**. Watch what the bracket does:

- **Bracket pans RIGHT (toward the target)** → sign is correct.
- **Bracket pans LEFT (away from the target)** → flip `KP_PAN` in [config.py](../../config.py) from `0.05` to `-0.05`.

Repeat with the target **slightly below center** to test tilt:

- **Bracket tilts DOWN (toward the target)** → sign is correct.
- **Bracket tilts UP (away from the target)** → flip `KP_TILT` from `0.05` to `-0.05`.

To make sign changes, press `q` to quit, edit `config.py` on the laptop, commit + push, wait for the Pi to pull, then rerun. The bracket will track AWAY indefinitely if the sign is wrong, so don't dwell on the wrong-sign case — quit and flip it.

## Step 6 — Tune Kp (proportional-only)

Once the sign is right, the bracket will track but probably either too slowly, too aggressively, or with oscillation. Tune Kp first with Ki=0 and Kd=0.

**Procedure:**
1. With current Kp (start at 0.05), hold the target stationary near center. Press `q` to quit, then move it, restart, and watch how the bracket converges.
   - Actually — you don't need to restart between target positions. Just keep the script running and move the target.
2. **If the bracket converges smoothly with no overshoot** — Kp is roughly right, move to Step 7.
3. **If the bracket reaches center but oscillates back and forth across it** — Kp is too high. Halve it (0.025) and retest.
4. **If the bracket reaches target sluggishly or stops short** — Kp is too low. Double it (0.10) and retest.
5. Repeat until the bracket lands on the target with at most one small overshoot.

Each change requires editing `config.py`, committing, pushing, waiting for the Pi to pull, and rerunning the script. Patience.

**Symptoms key:**
- *Bracket overshoots and oscillates* → Kp too high.
- *Bracket settles short of the target and stops* → Kp too low OR servo clamp warnings in the terminal (look for `Pan request X° clamped`).
- *Bracket lags noticeably behind a moving target* → Kp too low.

## Step 7 — Add Kd (derivative)

Kd damps the response — it reduces overshoot and stabilizes oscillation.

Rule of thumb: start `Kd ≈ Kp × 0.1`. If Kp landed on 0.08, try Kd = 0.008.

- **Too little Kd** → still overshoots.
- **Too much Kd** → sluggish, ignores fast target movement, jittery (Kd amplifies frame-to-frame detection noise).

## Step 8 — Add Ki only if needed

Ki removes persistent offset — if the bracket consistently settles 5–10 px away from center and never closes the gap, that's where Ki helps.

Start very small (`Ki = 0.001`) and increase by factors of 2.

- **Too little Ki** → persistent offset remains.
- **Too much Ki** → slow oscillation that grows over time (integral windup). Back off immediately if you see this.

Most setups can leave Ki = 0.

## Step 9 — Record the tuned gains

Once tracking is smooth, lock the values in.

1. Final values stay in `config.py` (you've been editing them all along).
2. Update [docs/calibration.md](../calibration.md): add a "PID gains" section under the existing HSV section. Include the four numbers (Kp/Ki/Kd for each axis), the date, and a one-line description of how it tracks ("smoothly converges on a slow-moving blue bag with no overshoot").
3. Commit + push.

## Step 10 — Acceptance criteria

Phase 5 is complete when:

- `test_tracking.py` runs without errors
- Slowly moving the target → bracket follows smoothly
- Holding target still at frame center → error converges to near zero, servos stop
- No `Pan request X° clamped` warnings under normal use (clamps during recovery from a far-edge target are fine)
- No runaway behavior, no growing oscillation
- Final gains recorded in `config.py` and `docs/calibration.md`

---

# Troubleshooting

**Bracket jiggles when the target is stationary** — detector centroid jitters (~8–12 px frame-to-frame with the LifeCam + blue plastic bag). There's a deadband for this: `TRACKING_DEADBAND_PX` in `config.py`. While both pixel errors are below that threshold, `tracker.update()` holds position; the overlay marker turns cyan and reads `LOCKED (deadband)`. Current value is 15 — if jitter is still pushing the centroid in and out, raise it. Also keep `KD_PAN` / `KD_TILT` at 0 — Kd amplifies frame-to-frame noise and isn't needed for this slow-target use case. `TRACKING_DEADBAND_PX` is also used as the fire threshold in Phase 8, so they match by design.

**Camera feels laggy / frame rate is low** — the original `servo.py` ramped every move in 2°/50 ms steps. A 10° correction blocked the main loop for 250 ms while the bracket ramped, starving the camera capture. Fixed by adding `ramp=False` support and having `tracker.update()` pass it. If you ever see the lag again, check that `tracker.py` is still using `ramp=False`. The DS3225's own mechanical slew rate (~1°/12 ms) provides natural smoothing — no software ramp needed in tracking mode.

**Bracket oscillates between calibrated limits / "jumps in the opposite direction"** — Kp is too high for the current un-ramped tracking. The original 0.05 worked only because `servo.py`'s ramp was the real rate-limiter; once the ramp was removed, 0.05 caused the bracket to snap past the target every frame and oscillate. Tuned down to 0.01 (5× smaller). If you still see oscillation, halve Kp again. If tracking is now too sluggish (bracket lags far behind a moving target), raise Kp by 50%. The right value depends on lighting + detector noise + how quickly you tend to move the target.

**Bracket snaps violently on startup** — expected on the very first run after the servos drifted while unplugged. `servo.init()` has no readback so it can't ramp; it just commands `PAN_CENTER` / `TILT_CENTER` directly. The DS3225 + LM2596 handle this. If it's repeatedly violent on every startup, the servos may be drifting between runs — check that the bracket isn't being bumped while powered down.

**Bracket tracks AWAY from target forever** — sign of Kp is wrong for your servo mounting. See Step 5.

**Bracket reaches one limit and sticks there** — usually wrong sign of Kp. Could also be runaway integral if you set Ki too high; reset Ki to 0.

**Bracket oscillates around the target without settling** — Kp too high. Halve it.

**Bracket lags behind a moving target** — Kp too low, or the 2°/50ms ramping inside `servo.py` is adding too much latency. First try increasing Kp. If you hit oscillation before catching up, the ramping is the bottleneck and may need its delay reduced (in `servo.py`).

**`Pan request X° clamped` warnings on every frame** — PID is asking for moves outside the calibrated bracket limits. Either the target is in a position the bracket physically can't reach, or `PID_OUTPUT_LIMIT` is too large combined with high Kp. Reduce `PID_OUTPUT_LIMIT` first.

**Detector loses target while tracking** — bracket motion may be blurring the frame, or the camera's auto-exposure is hunting because lighting changed mid-frame. Move the target more slowly; if persistent, see Phase 4's note on pinning exposure.

**`servo.init() must be called before move_pan()`** — the order in `test_tracking.py` calls `servo.init()` first; if you see this, something else has reset the module state. Restart the script.

---

# Reference: what was already built

### tracker.py ✅

[tracker.py](../../tracker.py). The ONLY module that uses `simple_pid`.

Public API:
- `init()` → `(pan_pid, tilt_pid)` — two `simple_pid.PID` instances with `setpoint=0` and `output_limits=(-PID_OUTPUT_LIMIT, PID_OUTPUT_LIMIT)`.
- `update(pan_pid, tilt_pid, kit, target_pos)` — per-frame call. If `target_pos is None`, holds position and skips updating PID state (no phantom-zero-error samples). Otherwise computes pixel errors, runs each PID, adds the correction to the current servo angle, calls `servo.move_pan` / `servo.move_tilt`. Returns a result dict with errors, corrections, and final commanded angles.
- `stop(kit)` — delegates to `servo.cleanup`.

Sign convention: `simple_pid` computes `error = setpoint − input`. We feed it `(target − center)` with `setpoint=0`, so the correction sign comes out OPPOSITE to the error sign for positive Kp. Whether that matches the bracket's mechanical orientation is unknown a priori → Step 5 establishes the sign empirically.

### test_tracking.py ✅

[test_tracking.py](../../test_tracking.py). Standalone end-to-end test — closes the camera → detector → tracker → servo loop with no laser involvement.

OpenCV window with:
- Red cross at frame center
- Green circle at detected target
- Overlay: current pan/tilt angles, pixel error per axis, PID correction per axis

`q` quits cleanly; `finally` block guarantees `servo.cleanup`, `camera.release`, `cv2.destroyAllWindows`.

### config.py — PID section ✅

[config.py](../../config.py). Added:

```python
KP_PAN  = 0.05    # PLACEHOLDER — sign may need flipping (see tracker docs)
KI_PAN  = 0.0
KD_PAN  = 0.01

KP_TILT = 0.05
KI_TILT = 0.0
KD_TILT = 0.01

PID_OUTPUT_LIMIT = 20.0  # degrees per update (per axis)
```

---

# Open questions / known unknowns

- **Ramping latency vs PID stability.** `servo.py`'s `_ramp` adds 50 ms per 2° of motion. A 20° correction takes 500 ms — far longer than a single frame interval. The PID will compute the next correction based on a stale view of the bracket position. If this proves unstable, options are: shrink `PID_OUTPUT_LIMIT` so corrections stay small (and ramp quickly), reduce `RAMP_DELAY_S` in `servo.py`, or skip ramping entirely during tracking and reserve it for `init()`/`cleanup()` only.
- **Detection jitter and Kd.** Kd amplifies frame-to-frame noise. If the detector's centroid jiggles by 5–10 px while the target is stationary, Kd will try to "correct" that. A low-pass filter on detector output (e.g., exponential moving average) would help if this becomes a real problem.
- **Auto-exposure on the LifeCam.** Same caveat as Phase 4 — sudden lighting changes can throw off detection mid-track. Not worth pinning exposure unless we see it bite during tuning.
