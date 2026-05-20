# Problem 001 — MB102 Cannot Power DS3225 Servos

## What went wrong

The MB102 breadboard power supply has an onboard voltage regulator (typically AMS1117 or similar)
that maxes out at ~700mA output at 5V. The two DS3225 servos draw 600–900mA combined during
normal tracking movements, and can spike to 2A+ per servo if they stall or hit a hard stop.

**Symptom:** servos hum, twitch, or refuse to move. Pi may also reset or freeze.

The 12V 5A PSU has plenty of raw power — the MB102's regulator chip is the bottleneck,
not the PSU. No amount of fiddling with the PSU fixes this.

---

## Root cause diagram

```
  12V 5A PSU
      │
      ▼
  ┌────────────┐
  │   MB102    │  ← onboard regulator here
  │  AMS1117   │    rated ~700mA max
  │  12V → 5V  │
  └─────┬──────┘
        │ 5V (~700mA ceiling)
        │
   ─────┴──────────────────────────────
   │                                  │
   ▼                                  ▼
PCA9685 VCC                     PCA9685 V+
(chip logic, fine)         (servo rail — WRONG, overloaded)
                                       │
                            ┌──────────┴──────────┐
                            ▼                     ▼
                       Servo ch0             Servo ch1
                      DS3225 pan           DS3225 tilt
                      (~300–900mA)         (~300–900mA)

  TOTAL POSSIBLE DRAW: up to 2A+  ←  MB102 limit: 700mA  ✗
```

---

## The fix — LM2596 buck converter → PCA9685 V+

An LM2596 step-down (buck) converter takes the 12V PSU input and efficiently steps it
down to a stable 5V at up to 3A. This is the **correct solution** because:

- Servo power is **completely isolated from the Pi's power rail** — servo spikes cannot
  affect Pi stability at all
- The 12V 5A PSU has 25W+ of headroom, far more than two servos will ever need
- The LM2596 handles stall current (2A+ per servo) without affecting anything else
- Pi USB-C adapter powers the Pi only, with no servo load competing on that rail

The PCA9685 board has two **completely separate** power rails:

| Terminal | Powers | Current needed |
|----------|--------|----------------|
| **VCC**  | PCA9685 chip logic only | ~50mA — MB102 handles this fine |
| **V+**   | All 16 servo header pins | High current — this is what the LM2596 feeds |

These two rails have **no internal connection** between them on the board.

---

## Fixed wiring diagram

```
  12V 5A PSU
      │
      ├──────────────────────────────────────────────────────┐
      │                                                      │
      ▼                                                      ▼
  ┌────────────┐                                    ┌─────────────────┐
  │   MB102    │                                    │  LM2596 module  │
  │  12V → 5V  │                                    │   IN+     OUT+  │
  └─────┬──────┘                                    │   IN-     OUT-  │
        │                                           └────┬────────┬───┘
        │ 5V (logic only, ~50mA)                        │        │
        │                                             GND rail  5V out
        ▼                                                         │
   PCA9685 VCC  ← logic power, MB102, no change                  │
                                                                  ▼
                                                           PCA9685 V+  ← servo power
                                                                  │
                                                       ┌──────────┴──────────┐
                                                       ▼                     ▼
                                                  Servo ch0             Servo ch1
                                                 DS3225 pan           DS3225 tilt
                                                 (~300–900mA)         (~300–900mA)

  Pi USB-C adapter (5V 3A) → Pi only, no servo load on this rail at all  ✓
```

---

## LM2596 module layout

The LM2596 module is a small board (roughly 4cm × 2cm) with:

```
  ┌──────────────────────────────────────────┐
  │              LM2596 module               │
  │                                          │
  │   IN+  IN-          OUT+  OUT-           │
  │    │    │              │    │            │
  │   [+] [-]   [coil]  [+] [-]             │
  │                  ┌────────┐              │
  │                  │trimpot │ ← blue screw │
  │                  └────────┘   turn to    │
  │                               set volts  │
  └──────────────────────────────────────────┘

  IN+  ← wire from 12V PSU positive
  IN-  ← wire from 12V PSU negative (GND)
  OUT+ ← wire to PCA9685 V+
  OUT- ← wire to GND rail (shared ground)
```

The trimpot (blue screw on top) adjusts the output voltage.
Clockwise usually increases voltage, counter-clockwise decreases.
Check with a multimeter before connecting anything.

---

## Step-by-step wiring and setup

**Do everything with power off until told otherwise.**

### Step 1 — Set the LM2596 output voltage

You must set the output voltage BEFORE connecting it to the servos or PCA9685.

1. Wire LM2596 **IN+** to the 12V PSU positive terminal (or MB102 input + rail)
2. Wire LM2596 **IN-** to GND (negative rail)
3. Power on the 12V PSU only
4. Put a multimeter on LM2596 **OUT+** and **OUT-**
5. Turn the trimpot slowly until the multimeter reads **5.0V**
   - Clockwise raises voltage on most modules, counter-clockwise lowers it
   - Go slowly — the trimpot is sensitive
6. Power off the PSU once you have 5.0V confirmed

### Step 2 — Wire to PCA9685 V+

7. LM2596 **OUT+** → PCA9685 **V+** terminal (a short jumper wire)
8. LM2596 **OUT-** → breadboard GND rail (shared with everything else)

### Step 3 — Confirm VCC stays on MB102

9. MB102 5V output → PCA9685 **VCC** — leave this as-is, no change

### Step 4 — Confirm shared ground

Everything must share the same ground reference:
- MB102 GND rail → PCA9685 GND ✓
- LM2596 OUT- → GND rail ✓
- Pi GPIO pin 6 (GND) → GND rail ✓  (done in Task 3.1)

### Step 5 — Final check before power on

```
  Source          →  Destination         Purpose
  ─────────────────────────────────────────────────────────
  MB102 5V        →  PCA9685 VCC         chip logic power
  LM2596 OUT+(5V) →  PCA9685 V+          servo power
  LM2596 OUT-     →  GND rail            ground
  Pi USB-C        →  Pi board only        Pi power (no change)
  Common GND across: MB102, LM2596, PCA9685, Pi GPIO pin 6
```

---

## PCA9685 board power terminals reference

```
  ┌─────────────────────────────────────────────────────┐
  │  PCA9685                                            │
  │                                                     │
  │  GND  OE  SCL  SDA  VCC  V+                        │
  │   │              │    │    │                        │
  │   │              │    │    └── servo power rail ←── LM2596 OUT+
  │   │              │    └─────── chip logic power ←── MB102 5V
  │   │              └──────────── I2C (from Pi GPIO)
  │   └─────────────────────────── ground ←── GND rail
  │                                                     │
  │  [ch0] [ch1] [ch2] ... [ch15]  ← servo headers     │
  │    │                                                │
  │    └── each header: GND / 5V(from V+) / Signal     │
  └─────────────────────────────────────────────────────┘
```

**Important:** Some PCA9685 boards have a solder jumper labeled `VCC_SRV` or a small
bridge pad. If shorted, it connects V+ directly to VCC — which would feed 5V from the
LM2596 back into the MB102. Check your board and confirm this jumper is OPEN.

---

## Pi GPIO pin reference

Hold the Pi with USB ports facing AWAY from you.
Top row = odd pins (1, 3, 5…). Bottom row = even pins (2, 4, 6…). Both count left to right.

```
        SD card slot side
              │
  ┌───────────▼──────────────────────────────────────────────┐
  │  [1 ][3 ][5 ][7 ][9 ][11][13][15][17][19][21][23]...    │ ← top row (odd)
  │  [2 ][4 ][6 ][8 ][10][12][14][16][18][20][22][24]...    │ ← bottom row (even)
  └──────────────────────────────────────────────────────────┘
   3.3V  SDA SCL                                (odd row)
    5V   5V  GND                                (even row)

  Relevant pins:
  ┌──────┬─────────┬──────────────────────────────────────┐
  │ Pin  │ Signal  │ Used for                             │
  ├──────┼─────────┼──────────────────────────────────────┤
  │  3   │ SDA     │ I2C data → PCA9685 SDA               │
  │  5   │ SCL     │ I2C clock → PCA9685 SCL              │
  │  6   │ GND     │ Common ground → GND rail             │
  │ 12   │ GPIO18  │ Laser MOSFET gate (Phase 6)          │
  └──────┴─────────┴──────────────────────────────────────┘

  (Pi 5V pins 2 and 4 are no longer used for servo power — LM2596 handles that)
```

---

## Power budget (after fix)

```
  12V 5A PSU: 60W total capacity
  │
  ├── MB102 → PCA9685 VCC (logic):       ~50mA      tiny
  └── LM2596 → PCA9685 V+ (servos):
        ├── DS3225 pan servo (tracking):  ~300–500mA
        ├── DS3225 tilt servo (tracking): ~300–500mA
        └── TOTAL typical:               ~600–1000mA  ✓ LM2596 rated 3A
        └── Both stalled (worst case):   ~4A          ✗ exceeds LM2596 3A limit
            → Stall is prevented by angle limits in servo.py (Task 3.4)

  Pi USB-C adapter: 5V 3A → Pi board only
        Pi 4B typical load:              ~600mA      plenty of headroom, no servo load
```

---

## Warnings

- **Set voltage before connecting.** If the LM2596 trimpot is at the wrong position
  it could output 12V directly to the servo headers and destroy the servos instantly.
  Always verify 5.0V with a multimeter on the output before wiring to the PCA9685.

- **Stall = danger.** Both servos stalled simultaneously can exceed the LM2596's 3A
  rating. The LM2596 will current-limit or overheat. The software angle limits in
  `servo.py` are the protection — do Task 3.3 calibration before running tracking code.

- **Shared ground is required.** LM2596 OUT-, MB102 GND, and Pi GPIO GND must all
  connect to the same GND rail on the breadboard. Without a shared ground the I2C
  signals have no reference and communication will fail.

---

## Status

- [ ] Set LM2596 output to 5.0V with multimeter (before connecting anything)
- [ ] Wire LM2596 IN+ → 12V PSU, IN- → GND rail
- [ ] Wire LM2596 OUT+ → PCA9685 V+, OUT- → GND rail
- [ ] Confirm MB102 5V still connected to PCA9685 VCC
- [ ] Confirm shared GND: MB102 + LM2596 + Pi GPIO pin 6 → same GND rail
- [ ] Proceed to Task 3.1: wire I2C jumpers (pins 3/5/6), run `i2cdetect -y 1`
