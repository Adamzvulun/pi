# Phase 7 — Mechanical Mounting + Boresight

## Status

- **Phase 7B (boresight calibration tool) ✅ COMPLETE 2026-05-27.** `calibrate_boresight.py` written and works from the GUI ("Boresight calibration..." button in the Laser section). Tool fires the laser, captures a frame, auto-detects the dot, lets the operator click to relocate, and writes `BORESIGHT_X_OFFSET` / `BORESIGHT_Y_OFFSET` to `config.py`. The actual measured offsets are currently 0/0 because Adam physically aligned the laser (taped on top of the camera, crosses aligned) so software compensation isn't needed. The infrastructure is there if alignment ever drifts.
- **Phase 7A (permanent base + electronics mounting) ⏳ NOT DONE.** Electronics still on the temporary breadboard / wood-base layout. Cosmetic only; nothing blocks the demo. Skippable if presentation deadline is tight.

The rest of this file is the original planning document — preserved for reference.

## Goal

Turn the loose assembly into a stable, presentable, transportable single unit. Mount everything to a wooden base (Pi, PCA9685, LM2596, breadboard, pan-tilt assembly). Mount the camera and laser onto the tilt plate. Calibrate the camera–laser angular offset (boresight) so the laser actually lands where the camera says the target is.

## Prerequisites

- **Phase 6 complete** (for laser mounting + boresight) — currently blocked on a dead laser diode ([problem 002](../../problems/002-laser-dead.md))
- **Phase 4 complete** ✅ — USB webcam on `/dev/video0`, 3D-printed camera mount already holds the LifeCam HD-3000 rigid on the tilt plate
- Phase 7A (base + electronics mounting) can start anytime — independent of the laser blocker

## Structure

This phase is split into two halves:

- **Phase 7A — Permanent base + electronics mounting** (independent of camera)
- **Phase 7B — Sensor / emitter mounting** (camera, laser, cables, boresight)

---

# Phase 7A — Permanent base + electronics mounting

## What needs mounting

| Component | Why mount it | Movement during operation? |
|---|---|---|
| Pan servo | Reference frame for everything else | Internal — must be rigidly held |
| Tilt servo | Already on pan output (kit) | Sweeps with pan |
| Camera | Stable alignment with tilt | Sweeps with tilt |
| Laser | Stable alignment with camera | Sweeps with tilt |
| Pi 4B | Don't want it dangling | None |
| PCA9685 | Short jumpers to Pi, clean servo cable routing | None |
| LM2596 | Hot 12V/5V rail — secure to avoid shorts | None |
| Breadboard (laser MOSFET) | Otherwise flops with cables | None |
| 12V PSU brick | Cable strain relief | None (off-board) |
| Cables | Routing, no binding during sweep | Bracket-side flex |

## Timing — when to do this

**Not all at once.** Recommended sequence:

1. **Now / in parallel with Phase 6's blocker:** Design and 3D-print the pan servo base. Cut/sand the wooden board to size. Mount Pi, PCA9685, LM2596 with proper routing and cable management. This is the bulk of Phase 7A — all independent of the laser.
2. **After Phase 6 resolves (replacement laser arrives and `test_laser.py` produces a 1 s dot):** Mount the laser onto the tilt plate. Mount the breadboard near the laser (short MOSFET-to-laser run). This kicks off Phase 7B.
3. **Boresight calibration (Task 7B.4):** runs after both the camera (already mounted via 3D-printed mount, Phase 5) and the laser are on the tilt plate.

Don't mount everything prematurely — rework on a finished board is annoying. Pan base + base board + electronics holders are safe to print/build now, since their footprints and positions don't depend on the laser path.

## Task 7A.1 — Pan servo base (3D printed)

3D print a holder that:
- Snug socket for DS3225 body (40×20×40 mm including ears)
- Pass-through screw holes for the servo's 4 mounting tabs
- Wider mounting base (4-corner screw holes for wood screws into the board)
- Cable channel underneath so the servo wire exits cleanly without being pinched
- Optional: internal channel for routing the I2C cables out the back

**Wider base = less tipping.** The pan-tilt assembly with payload creates a small inertia load when accelerating. Base should be ~2× the servo footprint at minimum.

## Task 7A.2 — Wood base

Suggested: **30 × 40 cm plywood, 12 mm thick.** Big enough for pan sweep clearance + components + cable routing. Thick enough not to flex when you drive screws into it.

**Rough layout** (looking down, pan-tilt at "front"):

```
              ┌───────────────────────────────────┐
              │                                   │
   (rear)     │  [Pi 4B]    [breadboard]          │  ← electronics row
              │                                   │
              │  [PCA]   [LM2596]   [12V jack]    │  ← driver row
              │   |        |                      │
              │  cables route forward to:         │
              │                                   │
              │           [Pan servo]             │  ← pan-tilt at front center
              │             ↺ 170°                │
              │                                   │
              │       pan sweep clearance         │
              │                                   │
   (front)    └───────────────────────────────────┘
```

Notes:
- Pan-tilt at front center: unobstructed sweep arc
- Electronics in two rows at the back: short cable runs, room for Pi heat dissipation
- 12V jack near LM2596: minimizes high-current wire length
- Cable runs forward from PCA to pan-tilt: predictable bend radius

**Optional aesthetics:** sand edges, round corners with a file, coat of stain or paint. Makes the demo look intentional.

## Task 7A.3 — Per-component mounting recommendations

### Pi 4B

The Pi has 4 standard M2.5 mounting holes on a 49 × 58 mm pattern.
- **M2.5 brass standoffs** screwed into wood — clean and accessible
- **3D-printed Pi case/tray** with mounting feet for the wooden board
- **3D-printed standoffs** if brass not available
- Keep USB-C, HDMI, micro-HDMI, audio, and Ethernet jacks accessible
- Pi 4 runs warm under sustained CPU. Leave ~15 mm clearance above. A small fan helps for long runs.

### PCA9685

Small board (~62 × 25 mm) with 4 M3 mounting holes.
- M3 brass standoffs into wood
- Or 3D-printed holder
- Place near the pan-tilt assembly so servo cables stay short

### LM2596

Tiny board (~43 × 21 mm). Mounting holes vary by module variant.
- M3 standoffs if holes present
- 3D-printed PCB-edge clip if not
- Double-sided foam tape works but heat-conducts poorly
- Hot glue is a permanent last resort
- Place near the 12V input jack to keep the high-current wire run short

### Breadboard (laser MOSFET driver)

The MB-102 has adhesive backing. Stick it to wood. Place near the laser and near the GPIO ribbon strain-relief point.

If you ever want to free up the breadboard, you could replace with a small perfboard. Not urgent.

### 12V PSU brick

Stays off-board. Just add a cable clip / zip-tie to the board's edge so the PSU's pull is taken up before stressing the 12V input jack.

## Task 7A.4 — Cable routing

- **Servo cables (PCA → pan-tilt):** flex slightly with pan rotation. Leave a service loop of slack so they don't kink. Route with the I2C lines if convenient.
- **Camera ribbon (later):** flat ribbons hate sharp folds. Gentle curves only. Service loop on the tilt plate so motion doesn't pull on the CSI connector. May need a longer ribbon than stock.
- **Laser wires:** thin, flexible. Pair with the camera ribbon's routing.
- **I2C lines (Pi → PCA9685):** keep short to reduce noise. Twist the data + clock pair if 20 cm or more.
- **12V power line:** keep AWAY from signal lines — high di/dt during servo motion induces noise.
- **Cable management hardware:** small 3D-printed clips screwed to the board, or adhesive zip-tie mounts, or zip-ties through drilled holes.

## Task 7A.5 — Clearance and movement gotchas

- Pan rotates 170° (PAN_MIN=50 to PAN_MAX=220). **Nothing in that sweep arc on the board higher than the kit's lower bracket plate.** Mock-up the layout and sweep the bracket through full range BEFORE drilling holes.
- Tilt sweeps 90° (115° to 205°). Camera + laser need clear field of view forward. Don't mount the breadboard or Pi where the camera lens points at them.
- Provide ~5 cm of cable slack between fixed mount points and the pan-tilt assembly's moving cable bundle.

---

# Phase 7B — Sensor / emitter mounting

## Task 7B.1 — Mount the camera to the tilt plate

The camera needs to be attached to the tilt plate (the part that moves up and down) and pointed forward.

Things to aim for:
- Camera lens roughly centered on the bracket's rotation axis (reduces image "swing" when tilting)
- Cable routed so it doesn't bind during full bracket range
- Secure enough that the camera doesn't wobble

**After mounting:** run `calibrate_servo.py` and sweep pan from `PAN_MIN=50` to `PAN_MAX=220` and tilt from `TILT_MIN=115` to `TILT_MAX=205`. If a cable binds within the previously-calibrated range, reduce the limits in `servo.py` and `docs/calibration.md`.

## Task 7B.2 — Mount the laser to the tilt plate

Mount the laser on the same tilt plate as the camera, pointing in roughly the same direction. Doesn't need pixel-perfect camera alignment — boresighting (Task 7B.4) handles that.

Route laser wires the same way as the camera cable. Make sure neither binds during movement.

## Task 7B.3 — Extend cables if needed

After mounting, check whether the existing wires (camera USB cable, laser wires, servo wires) have enough length to reach connections while allowing full bracket movement.

- Camera USB cable too short → use a USB-A extension cable, or an active USB extender if the run is over ~2 m. Cheap and easy.
- Laser wires too short → splice or solder extensions with thin hookup wire.
- Servo wires usually have plenty of length from the kit.

## Task 7B.4 — Boresight calibration

The camera and laser are physically offset on the bracket — they don't point at exactly the same spot. Boresighting measures that offset so the tracker can compensate.

**Create `boresight.py`:**

Behavior:
1. Show live camera feed with crosshairs drawn at frame center (320, 240)
2. Adam aims the bracket at a target until crosshair is centered on it
3. Fire laser for 0.5 seconds
4. Adam notes where the laser dot landed relative to the target
5. Adam uses arrow keys to move a second on-screen cursor to where the laser dot was
6. Difference between (320, 240) and the cursor position is the boresight offset
7. Save `BORESIGHT_X_OFFSET` and `BORESIGHT_Y_OFFSET` to `config.py` and `docs/calibration.md`

**Update `tracker.py`** to subtract the boresight offset from pixel error before feeding to the PIDs. This makes the tracker aim slightly "ahead" of the camera target so the laser lands on the actual target.

---

## Acceptance criteria (whole phase)

- All electronics mounted to the wooden base — no loose components
- Pan-tilt sweeps through `PAN_MIN`..`PAN_MAX` and `TILT_MIN`..`TILT_MAX` without cable binding
- Camera + laser both mounted to tilt plate, both pointing forward
- `boresight.py` produces stable offset values
- Tracking + firing produces a laser dot on the actual target (not the camera's exact aim point)
- All calibrated values recorded in `docs/calibration.md`

## Operating procedures

Cable management and clearance gotchas covered in this file. For day-to-day workflow, see [`docs/operating-guide.md`](../operating-guide.md).
