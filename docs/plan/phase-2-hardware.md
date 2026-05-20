# Phase 2 — Initial Hardware Build ✅ COMPLETE (superseded by Phase 3 rework)

## Goal

Build the initial breadboard rig: MB102 power module, PCA9685, both DS3225 servos, laser MOSFET driver circuit. Get everything ready for Pi-to-breadboard wiring in Phase 3.

## What we built

The original plan was to run everything from a single breadboard powered by an MB102:

- MB102 fed by the 12V 5A PSU, both jumpers at 5V, supplying the breadboard rails
- PCA9685 on breadboard: VCC → red rail, GND → blue rail, SDA/SCL stubs at j14/j13, green terminal block wired to the rails for servo power
- Both DS3225 servos plugged into PCA9685 (channel 0 = pan, channel 1 = tilt)
- IRLZ44N MOSFET driver circuit on breadboard: 220Ω gate resistor + 100kΩ pulldown, ready for the laser

## Decisions made and why

- **All on one breadboard, all powered from MB102:** simplest single-supply design at the time, no buck converter needed in the original plan.
- **MOSFET driver built early** even though the laser wasn't attached: easier to wire when all the components are in front of you, less likely to introduce a mistake later.
- **DS3225 servos at 5V** rather than the recommended 6V: cost-saving, accepted reduced torque. **This turned out to be the wrong call** — see Phase 3 / problem 001.

## What changed in Phase 3

The MB102 turned out to be **underpowered** for DS3225 servo current. Its onboard regulator caps at ~700mA, but two DS3225s draw 600–900mA continuous and spike to 2A+ on stalls. Servos hummed, twitched, or browned out the Pi.

The fix (in Phase 3, [problem 001](../../problems/001-servo-power.md)):
- **MB102 removed** from the circuit entirely
- **LM2596 buck converter** added: 12V PSU → LM2596 (5.0V set via trimpot) → PCA9685 V+. Up to 3A, clean.
- **Pi GPIO 5V (pin 2)** wired directly to PCA9685 VCC for chip logic.
- **Breadboard temporarily removed** to simplify the test rig during servo bring-up. Will return in Phase 6 for the laser MOSFET circuit (which has to be rebuilt).

## Files / artifacts

The Phase 2 build state is gone. See:
- [`problems/001-servo-power.md`](../../problems/001-servo-power.md) for the full story
- [`docs/wiring.md`](../wiring.md) for the current physical state
- [`docs/circuit-diagram.md`](../circuit-diagram.md) for visual diagrams

## Operating procedures

N/A — this phase is superseded.
