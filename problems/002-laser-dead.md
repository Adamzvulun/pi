# Problem 002 — Bare laser diode is dead

## What went wrong

The bare 5 mW 650 nm laser diode (red/black wires, no PCB, no driver electronics) does not emit light in any tested configuration, in either polarity, with or without the MOSFET driver in the path.

Found during Phase 6 first-power-up testing.

**Symptom:** No visible red dot from the laser under any test. Software runs without errors. Boot test passed (laser correctly stays OFF before any script runs, confirming the 100 kΩ pulldown is doing its job). Running `test_laser.py` produces clean logs (`init` → `countdown` → `FIRING` → `Laser ON` → `OFF` → `cleanup`) — the GPIO command goes out, the loop completes — but the laser itself never lights.

---

## Diagnosis steps taken

In order, each ruled out a possible cause:

1. **Script execution** — `test_laser.py` logs confirm `init` ran, GPIO18 was driven HIGH at the right moment, then LOW after 1 s, then cleanup released the pin. Software ruled out.
2. **Polarity (with full MOSFET circuit)** — swapped red and black at the breadboard. No light in either polarity. Polarity-as-only-issue ruled out.
3. **Loose connection in laser path** — re-seated both laser wires firmly. No change.
4. **Visual circuit check (photos)** — three resistors present (220 Ω gate, 100 kΩ pulldown, 100 Ω laser limiter), MOSFET present, all jumpers seated. No obvious wiring error.
5. **Bypass test — MOSFET removed from circuit** — laser wired directly: `Pi 5V → 100 Ω → laser red → laser black → Pi GND`. No MOSFET, no GPIO control. Laser should light continuously as soon as the Pi powers up. **No light.** Then swapped polarity: still no light.
6. **Resistor value confirmation** — verified the 100 Ω resistor is actually 100 Ω (color bands: brown-black-brown-gold). Confirmed correct value; the 100 kΩ and 100 Ω look almost identical and are easy to mix up, so this had to be ruled out explicitly.

After step 6, the only remaining failure modes are:

- The Pi's 5 V GPIO rail isn't actually delivering 5 V (ruled out — Pi boots, SSH works, PCA9685 still detected at `0x40`, all of which require working 5 V).
- The laser diode itself is non-functional.

**Conclusion: the laser diode is dead.**

---

## Likely root cause

Hard to say definitively. Plausible candidates:

- **Reverse-bias damage during polarity-swap testing.** A typical 650 nm laser diode has a reverse breakdown voltage around 5 V. With the Pi's 5 V rail and 100 Ω in series, reversed polarity puts the diode right at the edge of its breakdown rating. One pass might survive; multiple swap iterations might not.
- **ESD damage during handling.** Bare diodes (no protective PCB) are sensitive to static. A walk across a carpet before touching the leads can dump enough charge to cook the junction.
- **DOA from the supplier.** Cheap bare diodes sometimes ship dead with no visible damage.

Without a multimeter, we can't distinguish open vs. shorted junction, so root cause stays "dead."

---

## Resolution

**Replace the laser diode.** Phase 6's code (`laser.py`, `test_laser.py`) is correct and proven at the software level. The MOSFET driver circuit is built; we just couldn't fully verify it because the laser was dead. When a working laser arrives, attach it (red = +, black = −) and rerun `test_laser.py` — should work without any other changes.

If the next diode also fails to light, the MOSFET path itself is suspect and the next debugging step is to use a regular LED in series with 100 Ω as a known-good load in place of the laser, then verify the MOSFET conducts when GPIO18 drives the gate.

---

## What changed (Phase 6 status)

| Item | State |
|------|-------|
| `laser.py` (gpiozero owner module) | ✅ Written, pushed, software-verified |
| `test_laser.py` (init → fire 1 s → off) | ✅ Written, pushed, software-verified |
| MOSFET driver circuit on breadboard | ✅ Built (verified pulldown works — gate held LOW at boot) |
| Pi → breadboard wiring (pins 4, 12, 14) | ✅ Verified — `i2cdetect -y 1` still detects PCA9685 |
| Laser diode emits light when commanded | ❌ Dead diode — waiting on replacement |
| Phase 6 acceptance criteria (1-second visible dot on wall) | ⏸ Blocked on replacement |

Phase 6 is paused pending replacement, not blocked on anything we can fix in code or wiring.

---

## Notes for the next session / for the replacement

- When a replacement laser arrives: just attach red wire to the 100 Ω side, black wire to the MOSFET drain, run `python3 test_laser.py`. No code changes needed.
- If a multimeter becomes available before then, use it to verify: (a) Pi 5 V rail actually at 5 V at the breadboard, (b) gate goes HIGH (~3.3 V) when `laser.fire()` is called.
- If buying a replacement, prefer a laser **module** (small PCB with built-in driver) over another bare diode — they're more robust and don't need the external 100 Ω current limiter. The MOSFET driver circuit works with either; just remove the 100 Ω if you go with a module, since the module already has its own current limiting.
