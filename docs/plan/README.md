# Project Plan — Phase Index

Each phase has its own file. Click into one for detail.

| Phase | Title | Status |
|-------|-------|--------|
| 1 | [Foundation](phase-1-foundation.md) — OS, libraries, dev workflow | ✅ Complete |
| 2 | [Initial hardware build](phase-2-hardware.md) — breadboard wiring | ✅ Complete (superseded by Phase 3 rework) |
| 3 | [Servo control](phase-3-servo-control.md) — `test_servo.py`, `calibrate_servo.py`, `servo.py` | ✅ Complete |
| 4 | [Camera + detection](phase-4-camera.md) — `camera.py`, `detector.py`, HSV tuning | ✅ Complete |
| 5 | [PID tracking](phase-5-pid-tracking.md) — `tracker.py`, PID gain tuning | ✅ Complete |
| 6 | [Laser integration](phase-6-laser.md) — 3 V module direct on GPIO18, `laser.py` | ✅ Complete (MOSFET driver path abandoned — see problem 002) |
| 7 | [Mounting + boresight](phase-7-mounting.md) — laser physically aligned on camera, boresight tool | ✅ 7B complete / ⏳ 7A skipped |
| 8 | [Final integration](phase-8-integration.md) — `main.py`, full demo state machine | ✅ Complete |

## Status — demo-ready

All eight phases functionally complete (7A — permanent mounting — was skipped as cosmetic-only). Full tracking + firing demo runs from the operator GUI. Tested 2026-05-27.

The previous-session handoff is in [`latest-changesV1.md`](../../latest-changesV1.md) — explains the MOSFET drop, the boresight tool's current "unused but available" state, and the AE-disable fix for bracket dance during firing.

## How to read these files

- **✅ Complete** phases read as retrospectives: "what we built, what we decided, what went wrong."
- **⏳ In-progress** phases mix current state with remaining tasks.
- **⏸ Future** phases carry forward-looking task spec.

For practical commands and procedures, see [`docs/operating-guide.md`](../operating-guide.md). For physical wiring, see [`docs/wiring.md`](../wiring.md). For visual circuit diagrams, see [`docs/circuit-diagram.md`](../circuit-diagram.md). For problems encountered and their fixes, see [`problems/`](../../problems/).
