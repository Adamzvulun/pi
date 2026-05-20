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

## The fix — Pi GPIO 5V → PCA9685 V+

The PCA9685 board has two **completely separate** power rails:

| Terminal | Powers | Current needed |
|----------|--------|----------------|
| **VCC**  | PCA9685 chip logic only | ~50mA — MB102 handles this fine |
| **V+**   | All 16 servo header pins | High current needed — this is what we fix |

These two rails have **no internal connection** between them on the board.

The Raspberry Pi's USB-C power adapter (item 17 in your parts list) outputs **5V at 3A**.
The Pi uses ~600mA for itself, leaving ~2.4A of headroom.
The Pi's GPIO header exposes this same 5V supply on physical **pins 2 and 4**.

**One jumper wire solves the problem:**
Pi GPIO pin 2 (5V) → PCA9685 V+ terminal

---

## Fixed wiring diagram

```
  12V 5A PSU
      │
      ▼
  ┌────────────┐
  │   MB102    │
  │  12V → 5V  │
  └─────┬──────┘
        │ 5V (logic only now, low current)
        │
        ▼
   PCA9685 VCC  ← MB102 still handles this, no change


  Pi USB-C adapter (5V 3A)
      │
      ▼
  ┌─────────────────────────────┐
  │      Raspberry Pi 4B        │
  │                             │
  │  [GPIO header]              │
  │   pin2 (5V) ──┐             │
  │   pin6 (GND)  │  (GND       │
  └───────────────│──────────── ┘
                  │
                  │  ← NEW jumper wire (female on Pi pin 2, male into PCA9685 V+)
                  │
                  ▼
            PCA9685 V+  ← servo power now comes from 3A adapter
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
  Servo ch0             Servo ch1
 DS3225 pan           DS3225 tilt
 (~300–900mA)         (~300–900mA)

  TOTAL TYPICAL DRAW: ~1.2–1.5A  ←  headroom: 2.4A  ✓
```

---

## Pi GPIO pin layout

Hold the Pi with USB ports facing AWAY from you.
The 40-pin header is on your left. Pin 1 is the corner closest to the SD card slot.
**Top row = odd pins. Bottom row = even pins. Both count left to right.**

```
        SD card slot side
              │
  ┌───────────▼──────────────────────────────────────────────┐
  │  [1 ][3 ][5 ][7 ][9 ][11][13][15][17][19][21][23]...    │ ← top row (odd)
  │  [2 ][4 ][6 ][8 ][10][12][14][16][18][20][22][24]...    │ ← bottom row (even)
  └──────────────────────────────────────────────────────────┘
   ↑    ↑    ↑
  3.3V 5V  5V   ← pins 1, 2, 4
       │    │
   pin 2   pin 4 ← either works, use pin 2 (first in bottom row)
   (5V)    (5V)

  Relevant pins for this project:
  ┌──────┬─────────┬──────────────────────────────────────┐
  │ Pin  │ Signal  │ Used for                             │
  ├──────┼─────────┼──────────────────────────────────────┤
  │  1   │ 3.3V    │ (not used)                           │
  │  2   │ 5V      │ ← NEW: PCA9685 V+ (servo power)      │
  │  3   │ SDA     │ I2C data → PCA9685 SDA               │
  │  4   │ 5V      │ spare 5V (backup if needed)          │
  │  5   │ SCL     │ I2C clock → PCA9685 SCL              │
  │  6   │ GND     │ Common ground → breadboard GND rail  │
  │ 12   │ GPIO18  │ Laser MOSFET gate (Phase 6)          │
  └──────┴─────────┴──────────────────────────────────────┘
```

---

## PCA9685 board power terminals

The left side of the PCA9685 board has a row of 6 pins:

```
  ┌─────────────────────────────────────────────────────┐
  │  PCA9685                                            │
  │                                                     │
  │  GND  OE  SCL  SDA  VCC  V+                        │
  │   │              │    │    │                        │
  │   │              │    │    └── servo power rail     │
  │   │              │    └─────── chip logic power     │
  │   │              └──────────── I2C (from Pi GPIO)   │
  │   └─────────────────────────── ground               │
  │                                                     │
  │  [ch0] [ch1] [ch2] ... [ch15]  ← servo headers     │
  │    │                                                │
  │    └── each header has 3 pins: GND / 5V / Signal   │
  │        the 5V pin on each header comes from V+      │
  └─────────────────────────────────────────────────────┘
```

**Important:** Some PCA9685 boards have a solder jumper labeled something like
`VCC_SRV` or a small bridge pad that, if shorted, connects V+ directly to VCC.
If yours has this and it is bridged, the fix won't fully work (Pi 5V would feed back
into MB102). Check your board for any such jumper and confirm it is OPEN (not bridged).

---

## Wiring steps (everything powered off first)

1. Unplug the USB-C cable from the Pi
2. Unplug the 12V PSU from the MB102
3. Take one female-to-male jumper wire
4. Female end → Pi GPIO **pin 2** (bottom row, first pin from left = 5V)
5. Male end → PCA9685 **V+** terminal
6. Confirm GND is shared: Pi GND (pin 6) → breadboard GND rail → PCA9685 GND
   (this should already be done from Task 3.1 I2C wiring)
7. MB102 5V → PCA9685 VCC stays connected, no change

**Before powering back on, verify:**
```
MB102 5V  ──────────────────→  PCA9685 VCC   (logic power, no change)
Pi GPIO pin 2 (5V)  ────────→  PCA9685 V+    (servo power, new wire)
Common GND across Pi, MB102, PCA9685          (already done)
```

---

## Power budget (after fix)

```
  Pi USB-C adapter: 5V × 3A = 15W total capacity

  ├── Pi 4B (typical load):          ~600mA
  ├── DS3225 pan servo (tracking):   ~300–500mA
  ├── DS3225 tilt servo (tracking):  ~300–500mA
  │
  └── TOTAL typical:                 ~1.2–1.5A  ✓ well within 3A

  Stall (both servos hit hard stop): ~4A+ — EXCEEDS adapter  ✗
  → This is why calibration (Task 3.3) must be done carefully.
    Never command past the physical bracket stops.
```

---

## Warnings

- **Stall = danger.** If a servo hits a mechanical stop it can draw 2A+. Two stalled
  servos exceed the adapter's 3A limit. The Pi may reset or the adapter may shut down.
  Task 3.3 calibration finds the safe angle limits — complete it before any tracking code.

- **Servo.py must enforce angle limits.** The clamp inside `move_pan()` and `move_tilt()`
  is not just a software nicety — it is the protection against stall damage.

- **This fix is sufficient for this project** because the tracking loop makes small
  continuous corrections (servos are almost never near stall conditions during tracking).

---

## Status

- [ ] Wire Pi GPIO pin 2 → PCA9685 V+
- [ ] Confirm GND is shared between Pi, MB102, and PCA9685
- [ ] Proceed to Task 3.1: wire I2C jumpers, run `i2cdetect -y 1`
