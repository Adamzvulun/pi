# Project Plan — Phase Index

Each phase has its own file. Click into one for detail.

| Phase | Title | Status |
|-------|-------|--------|
| 1 | [Foundation](phase-1-foundation.md) — OS, libraries, dev workflow | ✅ Complete |
| 2 | [Initial hardware build](phase-2-hardware.md) — breadboard wiring | ✅ Complete (superseded by Phase 3 rework) |
| 3 | [Servo control](phase-3-servo-control.md) — `test_servo.py`, `calibrate_servo.py`, `servo.py` | ✅ Complete |
| 4 | [Camera + detection](phase-4-camera.md) — `camera.py`, `detector.py`, HSV tuning | ✅ Complete |
| 5 | [PID tracking](phase-5-pid-tracking.md) — `tracker.py`, PID gain tuning | ✅ Complete |
| 6 | [Laser integration](phase-6-laser.md) — MOSFET driver circuit, `laser.py` | ⏸ Blocked — dead laser diode ([problem 002](../../problems/002-laser-dead.md)) |
| 7 | [Mounting + boresight](phase-7-mounting.md) — wood base, 3D-printed mounts, alignment | ⏸ Future |
| 8 | [Final integration](phase-8-integration.md) — `main.py`, end-to-end test | ⏸ Future |

## Currently working on

**Phase 7A** — permanent base + electronics mounting. Independent of the laser; can proceed in parallel with waiting for a replacement laser diode. Cut/sand the wooden base, 3D-print the pan-servo holder and component standoffs, mount Pi + PCA9685 + LM2596 + breadboard, route cables. Full plan in [`phase-7-mounting.md`](phase-7-mounting.md).

**Phase 6 blocked** — laser diode dead. MOSFET driver and code are both ready and waiting; just need a working laser. See [`problems/002-laser-dead.md`](../../problems/002-laser-dead.md).

**Phase 7B (laser mount + boresight)** still gated on Phase 6.

## Next available work when the current item blocks

- **Phase 7A** (permanent base) is independent of camera/laser progress. Can start anytime in parallel.

## How to read these files

- **✅ Complete** phases read as retrospectives: "what we built, what we decided, what went wrong."
- **⏳ In-progress** phases mix current state with remaining tasks.
- **⏸ Future** phases carry forward-looking task spec.

For practical commands and procedures, see [`docs/operating-guide.md`](../operating-guide.md). For physical wiring, see [`docs/wiring.md`](../wiring.md). For visual circuit diagrams, see [`docs/circuit-diagram.md`](../circuit-diagram.md). For problems encountered and their fixes, see [`problems/`](../../problems/).
