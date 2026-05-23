# Phase 6 — Laser Integration ⏸ PAUSED

## Status

Code is written (`laser.py`, `test_laser.py`) and pushed. The bare diode laser, the resistor value (100Ω series), and the polarity (red = +, black = −) are all confirmed. **What's left is physical** — rebuild the MOSFET driver circuit on the breadboard, wire it to the Pi, attach the laser, and run `test_laser.py`.

**Why paused:** working on Phase 5 first now that the 3D-printed camera mount is in place. Phase 6 is independent of the camera and can resume anytime — the runbook below stays valid.

## What's done and what's left

| Step | Status |
|------|--------|
| Resistor + polarity confirmed (100Ω, red=+, black=−) | ✅ |
| `laser.py` written | ✅ |
| `test_laser.py` written | ✅ |
| **Gather parts** | ⏳ |
| **Build MOSFET driver circuit on breadboard** | ⏳ |
| **Wire Pi GPIO18 / 5V / GND to breadboard** | ⏳ |
| **Verify gate is LOW with Pi powered (multimeter)** | ⏳ |
| **Attach the laser diode** | ⏳ |
| **Run `test_laser.py` — observe dot for 1s** | ⏳ |

Reference details for the built modules are at the bottom of this file.

---

# Safety first — read this before powering anything

The laser is **5 mW, 650 nm, Class IIIa equivalent**.

- Brief exposure relies on the blink reflex. Direct staring into the beam can damage the retina.
- Adam has chosen not to use safety glasses — accepted, but the behavioral rules below still apply.
- **Before running `test_laser.py`:** point the diode at a matte wall, ~1 m away. Not at a person, pet, or mirror. Not at a window where it could exit into a reflective car windscreen outside.
- **Don't look into the bare diode** before it's pointing where you want it.
- The driver circuit itself is low-voltage (5V) and low-current (≤30 mA through the laser). Electrically it's safer than the servo rail. Optically it's the more dangerous half — treat the laser as the hazard, not the wires.

---

# What to do now — step by step

## Step 1 — Gather the parts

Lay out on the desk before starting:

| Part | Notes |
|------|-------|
| Breadboard (MB-102) | The original one used in Phase 2. Currently uninstalled. |
| IRLZ44N N-channel MOSFET | Pinout (flat face toward you, leads down): G – D – S. Metal tab is electrically the drain. |
| 220 Ω resistor | Gate current limiter (between GPIO18 and MOSFET gate). |
| 100 kΩ resistor | Gate pulldown (gate-to-GND). Keeps laser OFF when GPIO is floating. |
| 100 Ω resistor | Laser current limiter (between 5V rail and laser anode). |
| 5 mW 650 nm laser diode | Bare diode, two wires. Red = anode (+), black = cathode (−). |
| Female-to-male jumpers | ~4 — for Pi GPIO → breadboard. |
| Male-to-male jumpers | For breadboard internal connections. |
| Multimeter | Strongly recommended for the pre-power check (Step 5). |

If the breadboard's power rails aren't already split into two halves with jumpers, that's fine — we only need a couple of rows.

## Step 2 — Power EVERYTHING off

Before touching wires:

- Unplug the Pi's USB-C power.
- Unplug the 12V PSU brick (servos won't be active in this test, but better safe).

Don't skip this. A live GPIO pin shorted to 5V can damage the Pi.

## Step 3 — Build the MOSFET driver circuit

Reference diagram:

```
Pi GPIO18 (pin 12) ──[220Ω]──┬── MOSFET GATE (G)
                              │
                           [100kΩ]
                              │
                             GND (blue rail) ←── pulldown, keeps laser OFF
                                                  if GPIO floats

5V rail ──[100Ω]── Laser(+) red
                  Laser(−) black ── MOSFET DRAIN (D)
                                    MOSFET SOURCE (S) ── GND (blue rail)
```

**Build order (no laser attached yet):**

1. Insert the IRLZ44N MOSFET into the breadboard. Note which row each leg lands in (G, D, S, left to right with flat face toward you).
2. **220 Ω resistor:** one leg in the gate row, other leg in a free row that you'll later jumper to GPIO18.
3. **100 kΩ resistor:** one leg in the gate row (or the GPIO18-stub row — either works electrically, since the 220 Ω is small compared to 100 kΩ; gate row is cleaner). Other leg in the blue (−) rail.
4. **Source pin (S):** jumper to the blue (−) rail.
5. **100 Ω resistor:** one leg in the red (+) rail. Other leg in a free row — this will be the laser anode anchor point. Don't connect the laser yet.
6. **Drain pin (D):** jumper to a free row — this will be the laser cathode anchor point.
7. **Pi GPIO jumpers (female-to-male — Pi end is female, breadboard end is male):**
   - **Pi pin 4 (5V)** → breadboard **red (+)** rail
   - **Pi pin 14 (GND)** → breadboard **blue (−)** rail  *(any GND pin works; pin 6 is in use by the PCA9685)*
   - **Pi pin 12 (GPIO18)** → the GPIO18-stub row (the free end of the 220 Ω resistor)

Don't connect the Pi end yet — leave the female ends floating until Step 4. Build the breadboard side first.

## Step 4 — Connect the Pi-side jumpers

Pi still powered off. Plug the three female ends onto pins 4, 14, and 12 of the GPIO header. Double-check:

- Pin 4 = 5V (second pin from the corner on the 5V side — the side with pin 2)
- Pin 14 = GND (any GND pin will do; pin 14 is convenient)
- Pin 12 = GPIO18

[Pi pinout reference](https://pinout.xyz/pinout/pin12_gpio18). Pin 1 is the corner closest to the SD card slot.

## Step 5 — Pre-power multimeter check

**Before connecting the laser**, with the Pi powered on (but no scripts running) and the 12V PSU still unplugged:

1. Power on the Pi (USB-C).
2. Wait for it to fully boot (~30 s).
3. Multimeter, DC voltage mode:
   - **Probe between the red (+) rail and the blue (−) rail** → should read ~5.0 V (Pi's 5V GPIO output).
   - **Probe between the gate row and the blue (−) rail** → should read ~0 V (the 100 kΩ pulldown is holding the gate low because GPIO18 isn't being actively driven).

If both readings look right, the circuit is safe to connect the laser to.

If the gate reads anything above ~0.5 V with no script running, the pulldown isn't working — recheck the 100 kΩ wiring before continuing. A floating gate could turn the laser ON the moment you plug it in.

## Step 6 — Power off again and attach the laser

1. Power off the Pi (`sudo shutdown -h now` over SSH, then unplug USB-C).
2. Attach the laser:
   - **Red wire → 100 Ω resistor side** (the laser anode goes to the resistor; the resistor goes to the 5V rail).
   - **Black wire → MOSFET drain side** (the cathode goes to the drain; the drain switches it to ground when the MOSFET conducts).

Triple-check polarity. Reversing red and black will not destroy the diode immediately (the MOSFET in the path stops it from being a dead short), but the laser will not emit.

## Step 7 — Power up and confirm laser is OFF

1. Plug the Pi back in.
2. Wait for boot.
3. **Look at the laser diode.** It must be OFF. If it's emitting before any code has run, the gate is being held HIGH by something (likely a wiring error). Power off immediately and recheck the gate pulldown.

## Step 8 — Pull the Phase 6 code and run test_laser.py

SSH to the Pi:

```bash
ssh adam@LaserPi.local
cd ~/pi
git log -1 --oneline    # should show the Phase 6 commit
```

If the auto-pull hasn't run yet, force it:

```bash
git pull --rebase --autostash
```

Now run the test:

```bash
source venv/bin/activate
python3 test_laser.py
```

Expected output:

```
2026-MM-DD HH:MM:SS INFO laser: Laser initialized on GPIO18 (OFF)
2026-MM-DD HH:MM:SS INFO __main__: Firing in 3...
2026-MM-DD HH:MM:SS INFO __main__: Firing in 2...
2026-MM-DD HH:MM:SS INFO __main__: Firing in 1...
2026-MM-DD HH:MM:SS INFO __main__: FIRING — laser ON for 1.0 s
2026-MM-DD HH:MM:SS INFO laser: Laser ON
2026-MM-DD HH:MM:SS INFO laser: Laser OFF
2026-MM-DD HH:MM:SS INFO __main__: Fire sequence complete.
2026-MM-DD HH:MM:SS INFO laser: Laser cleanup complete (GPIO18 released)
```

**Point the laser at a matte wall before running.** During the 1-second fire, you should see the red dot. Then it disappears.

If the dot is faint, the laser is working but underpowered — we chose 100 Ω as a conservative starting value. After the first successful test, we can drop to 68 Ω (~30 mA) or 47 Ω (~42 mA) to get more brightness. Don't go below 47 Ω.

## Step 9 — Phase 6 done

When the laser fires for 1 second and turns off cleanly, Phase 6 is complete:

- ✅ Laser hardware-software path works end-to-end.
- ✅ Safety contracts hold: laser is OFF by default, OFF on script exit, OFF after Ctrl+C.

No calibration to record for Phase 6 — there's nothing to tune. Just note the resistor value you ended up with (100 Ω or lower) in `docs/calibration.md` if you change it from the default.

---

# Acceptance criteria

- Laser dot visibly appears on a wall for exactly 1 second.
- Terminal log shows the full sequence (init → countdown → ON → OFF → cleanup).
- Laser is off before the script runs, during cleanup, and at all times when no script is running (verifies the 100 kΩ pulldown is doing its job).
- `Ctrl+C` during the fire window turns the laser off (the `finally` block in `test_laser.py` ensures this — don't test it deliberately with the laser pointed somewhere unsafe, but verify the code path is there).

---

# Troubleshooting

**Laser is ON before any script runs** — gate is floating or being pulled HIGH. Power off immediately. Confirm the 100 kΩ resistor is between the gate row and the blue (−) rail, both legs are firmly seated. Confirm GPIO18's jumper isn't accidentally going to a 3.3V or 5V pin instead.

**Laser never lights during the FIRE step** — most likely polarity reversed (swap red and black at the diode end), or the MOSFET orientation is wrong (recheck G-D-S with the flat face toward you), or the 100 Ω resistor is open / not seated.

**Laser stays ON after the script exits** — `gpiozero` should leave the pin in a defined state, and the 100 kΩ pulldown should hold it low even if it doesn't. If the laser stays on, the pulldown is missing or the MOSFET is damaged (gate-drain short — IRLZ44N can be destroyed by ESD if handled without precautions). Check with a multimeter; replace MOSFET if needed.

**`ImportError: No module named 'gpiozero'`** — gpiozero is apt-installed system-wide on Bookworm. The venv was created with `--system-site-packages` so it should see it. If it doesn't, run `pip install gpiozero` inside the venv as a fallback.

**`PermissionError: ... /dev/gpiomem`** — the `adam` user needs to be in the `gpio` group. `groups adam` should list it. If not, `sudo usermod -a -G gpio adam` then log out + back in.

**Dot is too dim to see** — reduce the laser series resistor. 100 Ω → 68 Ω (~30 mA) → 47 Ω (~42 mA). Don't go below 47 Ω; the 5 mW diode is rated for ~50 mA continuous and shortens its life beyond that.

---

# Reference: what was already built

### laser.py ✅

[laser.py](../../laser.py). Owner module for GPIO18. The only file that imports `gpiozero` for the laser pin.

Public API:
- `init()` → `gpiozero.LED` (OFF). Configures GPIO18 as output, explicitly drives LOW.
- `fire(laser_dev)` → drives HIGH.
- `off(laser_dev)` → drives LOW.
- `cleanup(laser_dev)` → drives LOW + closes the device.

Naming rule: the variable holding the device must be `laser_dev`. Using the name `laser` shadows the module and breaks subsequent `laser.cleanup(...)` calls. CLAUDE.md enforces this.

### test_laser.py ✅

[test_laser.py](../../test_laser.py). Standalone laser test — init → 3-2-1 countdown → fire 1 second → off → cleanup. Wrapped in try/finally so Ctrl+C or an exception still turns the laser off.

### Task 6.1 — Resistor + polarity ✅

Recorded earlier:
- Laser is a bare diode (no PCB).
- 100 Ω series resistor mandatory. 3 V forward drop + 100 Ω gives ~20 mA, conservative for a 5 mW diode. Can drop to 68 Ω or 47 Ω later if dim.
- Red wire = anode (+), black wire = cathode (−).

---

# After this phase

- Laser is wired and code-controllable.
- **Phase 7B (mount the laser onto the tilt plate)** becomes actionable. Same physical challenge as the camera mount — once one is solved, the other usually is.
- **Boresight calibration (Task 7B.4)** needs both camera and laser mounted simultaneously, so it has to wait for both Phase 5's camera mount and Phase 6.
- **Phase 8 (integration)** can use `laser.py` as soon as Phase 5 tuning produces a usable PID — at that point `main.py` becomes the real tracking loop with `'f'` keypress firing.
