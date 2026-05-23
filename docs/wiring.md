# Wiring Reference

This file reflects the **current** state of the rig. As phases progress
(camera, laser, mounting), new sections will be added at the bottom.

For visual diagrams of the full target system, see [`circuit-diagram.md`](circuit-diagram.md).

---

## Current state (Phases 1–5 complete, Phase 6 blocked on dead laser diode)

Both DS3225 servos are powered and verified working. The full vision-to-motion
closed loop (camera → HSV detector → PID → servos) runs end-to-end via
`tracker.py` / `test_tracking.py`, with coast and recenter behaviors. The
LifeCam HD-3000 USB webcam is held rigidly on the tilt plate by a 3D-printed
mount. The MB-102 breadboard is reinstalled to carry the Phase 6 laser MOSFET
driver circuit — built and pulldown-verified — but the bare laser diode itself
is dead and waiting on a replacement (see [problem 002](../problems/002-laser-dead.md)).

### Power architecture

```
12V 5A PSU ──► LM2596 buck (output set to 5.0V) ──► PCA9685 V+   (servo power)
                       │
                       └─► GND ──► shared GND rail

Pi USB-C ──► Pi 5V rail ──► GPIO pin 2 ──► PCA9685 VCC           (chip logic)
                            GPIO pin 6 ──► shared GND
```

**Why two separate 5V sources?** The DS3225 servos can draw 2A+ each at
stall; the PCA9685 chip itself draws only ~50mA. Splitting the rails
ensures servo current spikes can never affect the Pi's logic. See
`problems/001-servo-power.md` for the full story.

### Pi ↔ PCA9685 (four wires directly, no breadboard)

| Pi pin | Pi signal | PCA9685 pin | Purpose |
|--------|-----------|-------------|---------|
| 2      | 5V        | VCC         | Chip logic power |
| 3      | GPIO2 SDA | SDA         | I2C data |
| 5      | GPIO3 SCL | SCL         | I2C clock |
| 6      | GND       | GND         | Shared ground |

### Servo power (LM2596 → PCA9685 green terminal)

| LM2596    | PCA9685 V+ terminal | Purpose |
|-----------|---------------------|---------|
| OUT+ (5V) | V+ (positive screw) | Servo rail |
| OUT−      | V− (negative screw) | Servo ground (shared with Pi GND) |

LM2596 input side: IN+ → 12V PSU positive, IN− → 12V PSU negative.
**Voltage was set with a multimeter on the output terminals BEFORE connecting to the PCA9685.**

### Servos plugged into PCA9685

| Channel | Servo | Mount role |
|---------|-------|------------|
| 0 | DS3225 pan | Bottom of bracket — rotates the whole tilt assembly horizontally |
| 1 | DS3225 tilt | Top of bracket — rotates camera/laser plate vertically |

Wire colors on DS3225: brown=GND, red=V+, orange=PWM signal. Polarity matters.

### Mechanical state

Pan-tilt bracket was **reassembled with both servos held at electrical 135°**
during mounting. Electrical center now corresponds to physical center on both
axes (within one spline tooth, ~15°). The safe edge limits are hardcoded in
`servo.py` and recorded in [`docs/calibration.md`](calibration.md):
`PAN_MIN=50, PAN_MAX=220, TILT_MIN=115, TILT_MAX=205`.

### Camera (Phase 4)

- Microsoft LifeCam HD-3000 USB webcam (`045e:0779`) on `/dev/video0`
- Plugged into a USB-A port on the Pi — handled by the in-kernel `uvcvideo` driver, no install needed
- Accessed via `cv2.VideoCapture(0)` from `camera.py` at 640×480 BGR
- Held rigid on the tilt plate by a 3D-printed mount (Phase 5 prerequisite)

The Pi 5 CSI camera on hand is incompatible with the Pi 4's 15-pin CSI ribbon slot and stays shelved. `picamera2` / `rpicam-apps` remain apt-installed but unused.

### Laser MOSFET driver (Phase 6 — built, awaiting working diode)

Built on the MB-102 breadboard:
- IRLZ44N N-channel MOSFET (G/D/S left-to-right with flat face toward you)
- 220Ω resistor between GPIO18 and MOSFET gate
- 100kΩ pulldown from MOSFET gate to GND (verified — laser does not flash at boot)
- 100Ω current limiter between 5V rail and laser anode
- Laser (+, when present) red → 100Ω side; laser (−) black → MOSFET drain; source → GND rail

Pi-side wiring for the laser:

| Pi pin | Pi signal | Destination | Purpose |
|--------|-----------|-------------|---------|
| 4      | 5V        | Breadboard red (+) rail | Laser supply via 100Ω |
| 12     | GPIO18    | 220Ω → MOSFET gate | Laser switch control |
| 14     | GND       | Breadboard blue (−) rail | Shared ground |

Wiring and pulldown are software-verified via clean `test_laser.py` log runs. The diode itself does not emit; awaiting replacement (see [problem 002](../problems/002-laser-dead.md)).

---

## Removed from the circuit

- **MB102 breadboard power module** — replaced by LM2596 for servo power and
  Pi GPIO 5V (pin 2) for PCA9685 chip-logic power. No longer in the circuit
  at all. Detail in [problem 001](../problems/001-servo-power.md).

---

## Notes

- DS3225 servo pulse range: 500–2500 µs at 50 Hz. Neutral (center) = 1500 µs = electrical angle 135°.
- DS3225 operating voltage spec: 4.8–6.8V. Currently running at 5.0V from the LM2596 (within spec).
- PCA9685 I2C address: 0x40 (default).
- Common ground is mandatory across the Pi, LM2596 OUT−, and PCA9685 GND — without it, I2C will fail.

## Finding GPIO pins on the Pi

Hold the Pi with the USB ports facing away from you. The 40-pin GPIO header
is on the top-left. Pin 1 is the corner closest to the SD card slot
(triangle marker on the board). **Top row = odd pins, bottom row = even pins,
both counting left to right.**

- Pin 2 (5V): bottom row, first from left
- Pin 3 (SDA): top row, second from left
- Pin 5 (SCL): top row, third from left
- Pin 6 (GND): bottom row, third from left
- Pin 12 (GPIO18): bottom row, sixth from left (laser, Phase 6)
