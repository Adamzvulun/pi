# Wiring Reference

This file reflects the **current** state of the rig. As phases progress
(camera, laser, mounting), new sections will be added at the bottom.

For visual diagrams of the full target system, see [`circuit-diagram.md`](circuit-diagram.md).

---

## Current state (Phase 3 — Servo bring-up complete)

Both DS3225 servos are powered and verified working. The breadboard is
temporarily out of the rig; the laser MOSFET circuit will be reassembled
on it in Phase 6.

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

Pan-tilt bracket has been **reassembled with both servos held at electrical 135°**
during mounting. Electrical center now corresponds to physical center on both
axes (within one spline tooth, ~15°). The safe edge limits will be hardcoded
into `servo.py` (Task 3.4) once recorded from `calibrate_servo.py` output.

---

## Removed from the circuit

These were part of the original plan but are no longer wired:

- **MB102 breadboard power module** — replaced by LM2596 for servo power
  and Pi GPIO 5V for logic power. May return for the laser circuit if
  convenient.
- **Breadboard itself** — temporarily out. Will be reintroduced for the
  laser MOSFET circuit in Phase 6.
- **Laser MOSFET driver circuit** — was previously built on the breadboard
  but disconnected when the board was removed. Will be rebuilt in Phase 6.

---

## Not yet wired (later phases)

### Phase 6 — laser

| Pi pin | Pi signal | Destination | Purpose |
|--------|-----------|-------------|---------|
| 12     | GPIO18    | MOSFET gate (via 220Ω) | Laser switch control |

Laser circuit components (when rebuilt):
- IRLZ44N N-channel MOSFET (G/D/S leftmost-to-rightmost with flat face toward you)
- 220Ω resistor between GPIO18 and MOSFET gate
- 100kΩ pulldown from MOSFET gate to GND (keeps laser OFF when GPIO floats)
- Laser (+) to 5V rail, laser (−) to MOSFET drain, source to GND

### Phase 4 — camera

Pi Camera connects via CSI ribbon cable directly to the Pi (not through the breadboard).

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
