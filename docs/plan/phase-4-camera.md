# Phase 4 — Camera + Target Detection ⏸ BLOCKED

## Status

**Blocked until a Pi 4-compatible camera or CSI adapter cable is available.**

The camera and ribbon cable on hand (parts list items 5 + 7) are labeled "for Raspberry Pi 5 / Zero." Pi 5 / Zero use a 22-pin 0.5mm-pitch CSI connector. Pi 4 uses a 15-pin 1.0mm-pitch connector. They're physically incompatible — no software workaround.

Options explored and rejected (Adam's constraints — no buying, no phone-as-IP-camera):
- USB webcam fallback — none on hand
- Phone-as-IP-camera via IP Webcam / DroidCam — rejected
- CSI adapter cable (~$3) — can't buy

Phase 4 will resume when either:
1. A Pi 4-compatible camera becomes available, OR
2. A 15→22 pin CSI adapter cable becomes available, OR
3. A USB webcam becomes available (would require a `cv2.VideoCapture`-based rewrite of `camera.py`)

In the meantime, **Phase 6 (laser) and Phase 7A (permanent base)** are still actionable.

---

## Prerequisites (when unblocked)

- Compatible camera physically connected to the Pi
- `rpicam-still -o test.jpg` produces a valid image (or `cv2.VideoCapture(0)` opens, if USB)

## Goal

Detect a colored target in the camera frame and return its pixel coordinates. Build `camera.py` and `detector.py` as the only modules that touch the camera and OpenCV directly.

---

## Task 4.1 — Connect the Pi Camera

**Do this with the Pi powered off.**

The Pi Camera connects via a flat ribbon cable into the CSI (Camera Serial Interface) slot on the Pi. The CSI slot is the narrow white connector between the HDMI ports and the USB ports, labeled "CAMERA" on the board.

**How to seat the ribbon cable:**
1. Gently lift the dark locking tab on the CSI connector — it pulls straight up (not a hinge, don't yank it)
2. Slide the ribbon cable in with the metal contacts facing toward the HDMI ports (away from you)
3. Press the locking tab back down firmly

Power the Pi back on, SSH in, and test:

```bash
rpicam-still -o ~/test.jpg
```

**Note on Bookworm:** there is NO "Enable Camera" option in `raspi-config` on Bookworm. The legacy interface was removed because libcamera auto-detects cameras at boot via device tree. If `rpicam-still` errors with "no cameras available," the issue is the ribbon cable seating or hardware compatibility (see top of this file).

**Success:** the command completes without errors and `test.jpg` exists.

---

## Task 4.2 — Write camera.py

The single point of access to the camera for all other code.

**Contains:**
- `init(width=640, height=480)` — starts picamera2, configures resolution, returns the camera object. 640×480 is the right starting resolution: high enough to see detail, low enough for the Pi to process in real time.
- `capture_frame(camera)` — captures one frame and returns it as a numpy array in BGR color format (OpenCV's expected order).
- `release(camera)` — stops and closes the camera cleanly.

**Why BGR not RGB:** OpenCV historically uses BGR order. picamera2 captures in RGB by default, so `camera.py` converts to BGR on capture. The rest of the project doesn't need to think about color order.

**Test:**

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

The saved image should look identical to what `rpicam-still` produced.

---

## Task 4.3 — Understand HSV color detection

Before writing the detector, understand what it's doing.

The camera produces BGR images — each pixel has B, G, R values. Detecting a color in BGR is unreliable because a red ball in bright sun vs. dim room produces wildly different RGB numbers.

HSV (Hue, Saturation, Value) separates color from brightness:
- **Hue** (0–179 in OpenCV) — actual color
- **Saturation** (0–255) — vividness (0 = grey)
- **Value** (0–255) — brightness (0 = black)

Thresholding on Hue (with loose ranges on S and V) finds a color regardless of lighting.

**Choose the target object now.** It should be:
- A single solid color that doesn't appear elsewhere in the scene
- Bright and saturated
- Good options: bright orange, tennis ball yellow-green, bright blue

**Avoid red as the target color.** Red wraps around OpenCV's HSV space (H near 0 AND near 179), so a single `cv2.inRange` call can't capture it cleanly. Every other color is straightforward.

---

## Task 4.4 — Write tune_detector.py

Interactive HSV slider tool. Live camera feed + mask preview, six sliders (H/S/V min/max), find the range that isolates the target as a clean white blob in the mask.

**Contains:**
- Two side-by-side windows: live camera feed and the mask
- Six trackbars: `H_min`, `H_max`, `S_min`, `S_max`, `V_min`, `V_max`
- Mask updates live as sliders move
- Press `s` to print the six values to the terminal
- Press `q` to quit

**How to run:**

Needs a GUI, so use VNC. Connect to `LaserPi.local` via VNC, open a terminal in the Pi's desktop, run:

```bash
python3 tune_detector.py
```

**Tuning procedure:**
1. Point camera at target with your actual operating lighting
2. Sliders start wide; mask shows lots of white
3. Narrow `H_max` down and raise `H_min` until only the target is white
4. Raise `S_min` to drop grey / washed-out pixels
5. Adjust `V_min` / `V_max` for your lighting
6. Press `s` when the mask is clean

Manually copy the six values into `config.py`'s `HSV_LOWER` and `HSV_UPPER`. Hand-editing is intentional — auto-writing Python source is fragile.

---

## Task 4.5 — Write config.py

Shared tuned constants. Other modules import from here.

**Contains:**
- `HSV_LOWER` — numpy array `[H_min, S_min, V_min]`
- `HSV_UPPER` — numpy array `[H_max, S_max, V_max]`
- `FRAME_WIDTH = 640`
- `FRAME_HEIGHT = 480`
- `FRAME_CENTER_X = FRAME_WIDTH // 2`
- `FRAME_CENTER_Y = FRAME_HEIGHT // 2`

Will grow over time to include PID gains (Phase 5) and boresight offset (Phase 7).

---

## Task 4.6 — Write detector.py

The actual detection logic.

**Public API:**
- `detect(frame)` — takes a BGR frame, returns `(x, y)` pixel coordinates of the target center, or `None` if not found.

**Algorithm:**
1. Apply 5×5 Gaussian blur to the BGR frame (smooths sensor noise)
2. Convert BGR → HSV
3. `cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)` produces a binary mask
4. Clean up with `cv2.erode` (kills tiny noise specks) then `cv2.dilate` (fills holes back in)
5. `cv2.findContours` to enumerate blobs
6. If no contours → return None
7. Pick the largest contour by area
8. If area below minimum threshold → return None (filters background noise)
9. Compute center via `cv2.moments`
10. Return `(cx, cy)`

**Test:**

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

Hold target → coordinates print. Move target away → `None`.

---

## Open questions / known unknowns

- **Camera replacement path** — see Status banner at top
- **If a USB webcam becomes the camera:** `camera.py` will use `cv2.VideoCapture(0)` instead of picamera2. Public API stays the same (`init`, `capture_frame`, `release`), so downstream code doesn't change. The branching point is internal to `camera.py`.
- **Wide-angle lens distortion:** the original Pi 5 camera is 220° fisheye. Any replacement may be narrower. Detector code is unaffected, but PID gains in Phase 5 may need rescaling if the angular-degrees-per-pixel ratio changes significantly.

## Acceptance criteria

- `python3 detector.py` (or the test inline) returns valid `(x, y)` for a held-up target
- Returns `None` when target is removed
- Coordinate values are within `(0, 0)` to `(FRAME_WIDTH-1, FRAME_HEIGHT-1)`
- HSV range and target object documented in `docs/calibration.md`
