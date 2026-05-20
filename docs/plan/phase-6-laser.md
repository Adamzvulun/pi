# Phase 6 — Laser Integration ⏳ IN PROGRESS

## Goal

Wire the laser through a MOSFET driver controlled by GPIO18, write `laser.py` as the safe gateway to the laser, verify the laser fires under software control with safety defaults (OFF on start, OFF on exit).

## Hardware context (current state)

- Breadboard removed during Phase 3 servo work. Needs to be reintroduced.
- IRLZ44N MOSFET driver circuit was previously built but is no longer wired.
- Laser module on hand is a **bare diode** (no PCB, no built-in driver/resistor) — 650nm, 5mW, ~3V forward.
- 5V available from the LM2596 output rail (also feeds PCA9685 V+) or directly from a Pi GPIO 5V pin.
- GND is shared across Pi, LM2596, and PCA9685.

---

## Task 6.1 — Verify laser voltage and pick series resistor ✅ DONE

**Outcome:**
- Laser is a bare diode — no PCB, no on-board components, two raw wires only.
- Wires: red = anode (+), black = cathode (−). Standard convention.
- **100Ω series resistor mandatory** between the 5V rail and laser (+). With 3V forward drop, this gives ~20mA — conservative for a 5mW laser. Can drop to 68Ω later if the dot is too dim.
- Direct connection to 5V without the resistor would destroy the diode instantly.

---

## Task 6.2 — Build the MOSFET driver circuit ⏳ IN PROGRESS

**Do everything with power off first** — unplug 12V PSU and Pi USB-C.

**Components:**
- Breadboard (MB102 board from Item 6)
- IRLZ44N N-channel MOSFET (Item 12)
- 220Ω resistor (gate current limiter)
- 100kΩ resistor (gate pulldown — keeps laser OFF when GPIO is floating)
- 100Ω resistor (laser current limiter — from Task 6.1)
- Female-to-male jumper wires (~4) for Pi GPIO → breadboard
- Male-to-male jumpers for breadboard internal connections
- Multimeter recommended for pre-power verification

**Circuit:**

```
Pi GPIO18 (pin 12) ──[220Ω]──┬── MOSFET GATE
                              │
                           [100kΩ]
                              │
                             GND ←── pulldown, keeps laser OFF if GPIO floats

5V rail ──[100Ω]── Laser(+) red
                  Laser(−) black ── MOSFET DRAIN
                                   MOSFET SOURCE ── GND
```

**How it works:**
- GPIO18 HIGH (3.3V) → MOSFET conducts → current flows from 5V → 100Ω → laser → drain → source → GND → laser ON
- GPIO18 LOW (0V) → MOSFET cut off → no current → laser OFF
- 100kΩ pulldown holds the gate at 0V whenever GPIO18 isn't actively driving — laser is OFF by default at boot, after script exits, and on any indeterminate GPIO state

**IRLZ44N pinout** (flat face toward you, leads down): G – D – S left to right. The metal tab at the back is electrically the drain.

**Power sourcing for the breadboard:**
- 5V rail: jumper from Pi GPIO pin 4 (5V) to the red (+) rail. Pin 2 is already used for PCA9685 VCC; pin 4 is currently unused. Pi USB-C supply has plenty of headroom for ~20mA.
- GND rail: jumper from Pi GPIO pin 14 (any GND pin will do — pin 6 is occupied by PCA9685 GND) to the blue (−) rail.
- GPIO18 signal: jumper from Pi GPIO pin 12 to the gate-side stub.

**Build order:**
1. Power off everything.
2. Insert MOSFET into breadboard.
3. 220Ω from GPIO18 stub → gate row.
4. 100kΩ from gate row → GND rail.
5. Source pin → GND rail.
6. 100Ω from 5V rail → laser (+) anchor point.
7. Drain pin → laser (−) anchor point.
8. Pi GPIO jumpers: pin 4 → red rail, pin 14 → blue rail, pin 12 → gate stub.
9. **Before connecting the laser:** power on the Pi (not 12V PSU yet). With multimeter:
   - Red rail to blue rail: ~5V
   - Gate stub to GND: ~0V (GPIO18 is LOW by default; pulldown holds it)
10. Power off the Pi again.
11. Connect the laser: red → 100Ω side, black → drain side.
12. Power on the Pi. **Laser should be OFF.** If it's ON before any code runs, the pulldown isn't working or the gate is floating. Power off and recheck the 100kΩ.

**Acceptance:** with the Pi powered on and no laser code running, the laser is OFF.

---

## Task 6.3 — Write laser.py ⏸ NEXT

Owner module for the laser. The only file that imports `gpiozero` for GPIO18.

**Public API:**
- `init() → laser_dev` — sets up GPIO18 as output, starts LOW (OFF), returns the device object
- `fire(laser_dev)` — drives GPIO18 HIGH (ON)
- `off(laser_dev)` — drives GPIO18 LOW (OFF)
- `cleanup(laser_dev)` — calls `off()`, closes the device

**Safety pattern used everywhere a laser is involved:**

```python
laser_dev = laser.init()
try:
    # ... do things ...
finally:
    laser.cleanup(laser_dev)
```

This guarantees the laser turns off even if an exception is raised or the script is interrupted.

**Naming convention:** the variable holding the device object MUST be `laser_dev`, never `laser`. Naming it `laser` would shadow the module — `laser = laser.init()` works once, but then `laser.cleanup(...)` fails because `laser` is now the device object, not the module. CLAUDE.md flags this.

---

## Task 6.4 — Write test_laser.py ⏸ NEXT

Standalone laser test.

**Behavior:**
- Initialize laser
- Print "Firing in 3... 2... 1..."
- Fire for exactly 1 second
- Turn off
- Confirm in terminal

**Acceptance criteria for phase complete:**
- Laser dot visibly appears on a wall for 1 second
- Laser turns off cleanly
- `try/finally` works: Ctrl+C during fire turns the laser off (don't actually test by Ctrl+C-ing while laser is on — just verify in the code that the finally is present)

---

## Open questions / known unknowns

- **Where to source 5V for the breadboard rail:** Pi GPIO 5V (pin 4) is the current plan. Alternative: tap the LM2596 output. Both work; Pi GPIO is simpler.
- **Final laser brightness with 100Ω:** if the dot is too faint at testing distance, swap to 68Ω (~30mA) or 47Ω (~42mA). 47Ω is approximately rated current for a 5mW diode.

## After this phase

- Laser is wired and code-controllable
- Phase 7B (mount the laser onto the tilt plate) becomes actionable
- Boresight calibration (Task 7.4) needs both camera + laser mounted, so it waits for Phase 4 to unblock
