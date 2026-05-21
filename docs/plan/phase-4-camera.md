# Phase 4 — Camera + Target Detection ✅ COMPLETE

## Status

**Done as of 2026-05-22.** Camera + detection pipeline runs end-to-end on the Pi: USB webcam → `camera.capture_frame` → `detector.detect` → `(x, y)` pixel coordinates.

The path the project ended up on:
- USB webcam (Microsoft LifeCam HD-3000, `045e:0779`) on `/dev/video0`, accessed via `cv2.VideoCapture(0)`.
- Original Pi 5 camera + 22-pin ribbon stay shelved (incompatible with the Pi 4's 15-pin CSI slot).
- HSV range tuned against a folded 10×20 cm blue plastic bag under overhead ceiling lighting. Recorded in `config.py` and [`docs/calibration.md`](../calibration.md).
- Smoke test passed — `detector.detect()` returned `(385, 288)` with the target in frame, inside the 640×480 bounds.

## Final state

| Step | Status |
|------|--------|
| Camera connected and verified | ✅ |
| `camera.py` written | ✅ |
| `config.py` written | ✅ |
| `detector.py` written | ✅ |
| `tune_detector.py` written | ✅ |
| HSV range tuned via VNC | ✅ |
| HSV values committed to `config.py` | ✅ `np.array([79, 76, 0])` → `np.array([105, 255, 255])` |
| Values + target + lighting in `docs/calibration.md` | ✅ |
| Smoke test on Pi | ✅ `(385, 288)` |

The runbook below is preserved for **re-tuning** — rerun if the target object, lighting, or camera position changes. Reference details for the built modules are at the bottom of the file.

---

# Re-tuning runbook (only when re-calibrating)

The phase is complete — you only need to follow this if the target object, lighting, or camera position changes. The steps below take you through tuning the HSV range from scratch.

## Step 1 — On the laptop: make sure Phase 4 code is on GitHub

The Pi can't run `tune_detector.py` until the code is pushed and pulled. From a terminal on the laptop in `C:\Projects\pi`:

```powershell
git status
```

If `camera.py`, `config.py`, `detector.py`, `tune_detector.py` show up as untracked or modified, ask Claude Code to commit and push them (one Phase 4 scaffolding commit). Then wait ~60 seconds for the Pi's auto-pull cron to run.

## Step 2 — On the Pi (over SSH): confirm the pull happened

```bash
ssh adam@LaserPi.local
cd ~/pi
git log -1 --oneline       # should be the Phase 4 scaffolding commit
ls camera.py detector.py tune_detector.py config.py
```

If git log is still showing the Phase 3 commit, the auto-pull hasn't run yet. Either wait, or run it manually:

```bash
git pull --rebase --autostash
```

## Step 3 — Pick your target object

Hold up the object you plan to track. It must be:

- A single solid color that doesn't appear elsewhere in the camera's view
- Bright and saturated — a washed-out pastel will be hard to isolate
- **Not red** — red wraps around OpenCV's hue space (H near 0 AND H near 179), so a single `cv2.inRange` call can't catch it cleanly. Avoid red entirely.

Good options: bright orange, tennis-ball yellow-green, vivid blue, vivid purple. A piece of colored paper, a ball, a sticky note all work.

Set up the room with the actual lighting you'll use during the demo — HSV tuned at 2 AM under a desk lamp won't survive being moved into sunlight.

## Step 4 — VNC into the Pi (you need a GUI for this)

`tune_detector.py` opens three OpenCV windows. SSH alone can't show them. Connect via VNC instead:

1. Open the VNC Viewer on the laptop
2. Connect to `LaserPi.local` (or the Pi's IP if `.local` doesn't resolve)
3. Log in to the Pi desktop
4. Open a terminal in the Pi desktop (not the SSH one — needs to inherit the desktop's display)

## Step 5 — Run tune_detector.py

In the Pi-desktop terminal (the VNC one):

```bash
cd ~/pi
source venv/bin/activate
python3 tune_detector.py
```

Three windows open:

- **controls** — six sliders (`H_min`, `H_max`, `S_min`, `S_max`, `V_min`, `V_max`)
- **feed** — live camera view with a green circle at the detected centroid (only drawn when a target is found)
- **mask** — the binary mask `detector.detect()` will actually operate on. White = "matches color range," black = "doesn't."

If you don't see all three, drag them apart — they may be stacked.

The terminal will say:
```
Tuner running. 's' = print values, 'q' = quit.
```

**Important about keyboard input:** OpenCV captures `s` / `q` keypresses only when one of its windows is focused, not the terminal. Click on the `feed` window (or `mask`, or `controls`) before pressing keys. The output of `s` still prints to the terminal — but the *keystroke* has to be received by an OpenCV window.

## Step 6 — Tune the HSV range

Hold the target in front of the webcam. Aim is to make the **mask** window show **just the target as a clean white blob on a pure-black background**.

### The order to adjust sliders

Start with all sliders at default (H range wide, S/V at 0–255 — the mask will be almost all white).

1. **Narrow Hue first.** Hue is the color. Drag `H_min` up and `H_max` down until the mask is white **only** where the target is. Tighten until just before the target itself starts losing pixels — that's the edge of usable range.
2. **Then raise `S_min`.** Saturation removes greys and washed-out background. Push `S_min` up until walls, skin, paper, etc. drop out of the mask. The target should still glow white.
3. **Then nudge `V_min` and `V_max` for lighting.**
   - Raise `V_min` if dark shadows are leaking through as false positives.
   - Lower `V_max` if shiny / overexposed highlights are getting included where they shouldn't.
4. **Wave the target around the frame.** The green circle in the `feed` window should follow it. If the circle disappears, your range is too tight — widen the dimension that was about to clip.
5. **Hold it stationary near a frame edge.** Confirm the mask doesn't suddenly grow large blobs from something the camera sees in the periphery.

### What "good" looks like

- `mask` window: target = solid white blob, no holes. Background = pure black, no twinkly noise pixels.
- `feed` window: green circle pinned to the visual center of the target, follows smoothly as you move it.
- The mask doesn't flicker noticeably between frames when nothing's moving.

### What "bad" looks like (and what to do)

- **Mask has lots of background noise (twinkly white speckles).** Raise `S_min`. If that hurts the target too much, raise `V_min` a little instead.
- **Target shows up as a ring with a black hole inside.** Saturation is dropping out in the highlight at the center. Lower `S_min` a touch.
- **Green circle jumps around even when the target is still.** Two separate blobs of similar color exist. Move the camera, change background, or tighten the range further to kill the smaller blob.
- **Green circle never appears even though the mask shows white.** Blob is smaller than `MIN_CONTOUR_AREA=200` (about a 14×14 patch). Hold target closer, or open `config.py` and lower the constant.

## Step 7 — Capture the tuned values

When the mask is clean and the green circle locks on, **click on the `feed` window** to give it focus, then press **`s`**. (Pressing `s` while the terminal is focused does nothing — OpenCV only sees keys when one of its own windows has focus.)

It prints something like:

```
============================================================
Current HSV range — paste into config.py:

HSV_LOWER: np.ndarray = np.array([10, 150, 100])   # [H_min, S_min, V_min]
HSV_UPPER: np.ndarray = np.array([25, 255, 255])  # [H_max, S_max, V_max]

Also record in docs/calibration.md along with target description
and lighting conditions.
============================================================
```

Copy the two `HSV_LOWER` / `HSV_UPPER` lines. Then press **`q`** to quit cleanly.

## Step 8 — On the laptop: paste the values into config.py

Open `C:\Projects\pi\config.py`. Find this block:

```python
HSV_LOWER: np.ndarray = np.array([0, 100, 100])   # [H_min, S_min, V_min]
HSV_UPPER: np.ndarray = np.array([30, 255, 255])  # [H_max, S_max, V_max]
```

Replace those two lines with the printed values from Step 7.

## Step 9 — Record the calibration in docs/calibration.md

Open `C:\Projects\pi\docs\calibration.md`. Find the section that says:

```
## HSV target range — not yet measured
```

Replace it with the actual measurement. Use this format:

```markdown
## HSV target range — YYYY-MM-DD

Measured with `tune_detector.py` on the Microsoft LifeCam HD-3000.

| Constant   | Value                | Notes |
|------------|----------------------|-------|
| `HSV_LOWER` | np.array([H, S, V]) | |
| `HSV_UPPER` | np.array([H, S, V]) | |

**Target object:** <describe — e.g. "bright orange Post-it Note, ~7×7 cm">

**Lighting:** <describe — e.g. "overhead room LED, no direct sunlight, ~6 PM">

Values live in `config.py`. If lighting or target change, rerun
`tune_detector.py` and update both.
```

Fill in the date, the numbers, the target description, the lighting.

## Step 10 — Commit and push

From the laptop:

```powershell
git add config.py docs/calibration.md
git commit -m "Tune HSV target range for Phase 4 detection"
git push
```

The Pi auto-pulls within 60 seconds.

## Step 11 — Smoke-test detector.detect on the Pi

SSH back to the Pi (regular SSH is fine — no GUI needed):

```bash
ssh adam@LaserPi.local
cd ~/pi && source venv/bin/activate
python3 -c "
import camera, detector
cam = camera.init()
frame = camera.capture_frame(cam)
print('Detected at:', detector.detect(frame))
camera.release(cam)
"
```

Hold the target in front of the camera → should print `Detected at: (x, y)` with sensible coordinates (0 ≤ x ≤ 639, 0 ≤ y ≤ 479).

Take the target away → should print `Detected at: None`.

Run it a few times to confirm it's stable.

When this passes, Phase 4 is complete and you can move to Phase 5 (PID tracking).

---

# Acceptance criteria

- Detector returns valid `(x, y)` for the held-up target
- Returns `None` when the target is removed
- Coordinates are inside `(0, 0)` to `(FRAME_WIDTH-1, FRAME_HEIGHT-1)`
- HSV range, target description, lighting all recorded in `docs/calibration.md`
- No false positives from the empty room (background returns `None`)

---

# Troubleshooting

**Pressing `s` or `q` does nothing** — you're focused on the terminal. OpenCV's `waitKey` only sees keypresses when one of its windows is focused. Click on the `feed` window first, then press the key.

**`tune_detector.py` crashes immediately with "Cannot open camera"** — webcam isn't connected or another process has it (including a previous `tune_detector.py` that didn't exit cleanly). Run `pgrep -fa python` to spot any orphan, kill it with `kill <pid>`, then retry. Replug the USB if that doesn't help. Confirm device with `ls /dev/video0`.

**Three windows don't appear** — VNC may be sharing display `:0` but the script is opening on `:1`. Check `echo $DISPLAY` in the VNC terminal — it should print `:0` or similar. If empty, run `export DISPLAY=:0` before running the script.

**Sliders work but the live feed is frozen** — could be a v4l2 buffering issue. Press `q` to quit cleanly, then retry. If persistent, restart the Pi.

**The mask is clean but the green circle never appears** — the blob is smaller than `MIN_CONTOUR_AREA = 200`. Either bring the target closer to the camera, or open `config.py` and lower the constant (e.g., to 100).

**Mask twinkles even when nothing moves** — auto-exposure is hunting. For now, just live with it — if it causes real detection problems during Phase 5 tracking, see the auto-exposure note under "Open questions" below.

**After tuning the mask is clean but the detector smoke test (Step 11) returns `None`** — probably the lighting changed between when you tuned and when you tested. Re-run `tune_detector.py` under the test's actual lighting.

---

# Open questions / known unknowns

- **Field of view** — the LifeCam HD-3000's FOV is narrower than the original 220° fisheye plan. Detector code is unaffected, but the PID gains tuned in Phase 5 will be specific to this camera's degrees-per-pixel. If the camera is ever swapped, expect to retune Phase 5.
- **Auto-exposure** — most consumer webcams (LifeCam included) hunt their exposure when lighting changes. The HSV range tuned in stable lighting may misfire under sudden changes. If this becomes a real problem, `camera.py` can set `cv2.CAP_PROP_AUTO_EXPOSURE = 0.25` and pin `cv2.CAP_PROP_EXPOSURE` manually. Not worth doing until we see it bite.

---

# Reference: what was already built

Details on the ✅ items from the top table. You don't need to do anything in this section — it's here for "what is this file / why does it exist" lookups.

### Task 4.1 — Camera connection ✅

Microsoft LifeCam HD-3000 plugged into a USB port on the Pi. In-kernel `uvcvideo` driver handles standard UVC webcams — no install needed. Verified:

```bash
lsusb                    # → "Microsoft Corp. LifeCam HD-3000" at 045e:0779
ls /dev/video*           # → /dev/video0 exists (alongside several others)
python3 -c "import cv2; cap=cv2.VideoCapture(0); ok,f=cap.read(); print(ok, f.shape); cap.release()"
# → True (480, 640, 3)
```

### Task 4.2 — camera.py ✅

[camera.py](../../camera.py). Owner module for the camera subsystem; the only file that imports `cv2.VideoCapture` for capture.

Public API:
- `init(width=640, height=480, device_index=0)` → `cv2.VideoCapture`
- `capture_frame(cap)` → BGR `numpy.ndarray`
- `release(cap)` → `None`

`VideoCapture` delivers BGR natively, so no `cvtColor` on capture (unlike the original picamera2 plan).

### Task 4.3 — HSV background

Camera produces BGR. Thresholding in BGR is unreliable because lighting changes shift all three channels together. HSV separates the dimensions:

- **Hue** (0–179 in OpenCV — half the usual 0–359 so it fits in a byte) is the color itself
- **Saturation** (0–255) is vividness (0 = grey)
- **Value** (0–255) is brightness (0 = black)

Thresholding tightly on Hue with loose Saturation/Value finds the color across a wide range of lighting. That's what `tune_detector.py` is for — finding the right ranges empirically.

### Task 4.4 — tune_detector.py ✅

[tune_detector.py](../../tune_detector.py). Three windows (controls + live feed with centroid overlay + binary mask), six trackbars, `s` prints copy-pasteable values, `q` quits. Mirrors `detector.build_mask()`'s pipeline exactly so what you see in the mask window is what `detect()` will see at runtime.

Manual copy-paste of the values into `config.py` is intentional — auto-writing Python source from a tuning tool is fragile (a runaway slider during shutdown could overwrite good values).

### Task 4.5 — config.py ✅

[config.py](../../config.py). Holds frame geometry (`FRAME_WIDTH`, `FRAME_HEIGHT`, centers), placeholder `HSV_LOWER` / `HSV_UPPER`, `MIN_CONTOUR_AREA = 200`, `FIRE_PIXEL_THRESHOLD = 15`. Will grow with PID gains (Phase 5) and boresight offset (Phase 7).

### Task 4.6 — detector.py ✅

[detector.py](../../detector.py). Owner module for target detection.

Public API:
- `detect(frame)` → `(x, y)` pixel coords of target centroid, or `None`
- `build_mask(frame)` → binary mask (exposed for debugging)

Algorithm: 5×5 Gaussian blur → BGR→HSV → `cv2.inRange(HSV_LOWER, HSV_UPPER)` → erode×2 → dilate×2 → `findContours(RETR_EXTERNAL)` → largest by area → reject if `< MIN_CONTOUR_AREA` → centroid from `cv2.moments`.
