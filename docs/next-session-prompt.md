# Next-session prompt

Paste the block below into a fresh Claude Code window when starting a new session on this project. It tells the new Claude what's going on and how to work in the same style we've established.

---

```
You're continuing the Laser Tracker project in C:\Projects\pi. This is a school
final project, mid-build — not a fresh start. Adam is the user; he's a beginner
with electronics and Linux and learns by doing.

BEFORE responding to anything, read these files in order:

  1. HANDOFF.md             — TL;DR of where we are, what's blocked, what's next
  2. CLAUDE.md              — full project context, hardware, module rules, coding style
  3. docs/plan/README.md    — phase-by-phase status with links to each phase file
  4. docs/calibration.md    — recorded tuned values (servo limits, HSV, PID gains)
  5. problems/001-servo-power.md and problems/002-laser-dead.md — known issues
  6. CHANGELOG.md           — what changed in recent sessions

Then check the two memory files at:
  C:\Users\Owner\.claude\projects\C--Projects-pi\memory\
They hold persistent preferences that override default Claude behavior.

After reading everything, confirm you understand the full scope by stating
in 2-3 sentences:
  (a) which phase is currently active
  (b) what's blocked and why
  (c) what the next actionable task is

Wait for Adam to direct the session from there. Don't start coding speculatively.


WORKING STYLE — these are non-negotiable, overriding Claude's defaults:

- AUTO-COMMIT AND PUSH at the end of every unit of work. Don't ask
  "should I commit this?" — just `git add` → `git commit` → `git push`.
  Use the project's commit message style (lowercase prefix `feat:`/`fix:`/
  `docs:`, em-dash separator, body that explains the why).

- ALL HARDWARE TESTS GO THROUGH control_panel.py — the operator GUI.
  Adam built it specifically so he doesn't have to type commands.
  Direct him to GUI buttons by name ("click 'Start tracking test…' in
  the control panel"), NOT to terminal commands like `python3 test_X.py`.
  If a needed feature is missing from the panel, ADD IT TO THE PANEL;
  don't work around it with the terminal. The control panel is the
  canonical operator interface — missing features are bugs, not workflow
  gaps. Terminal use is reserved for OS-level one-shots (i2cdetect, lsusb,
  git pull) and first-time setup that runs before the GUI exists.

- COMMENT GENEROUSLY and explain WHY, not just what. Adam is learning.
  Walk through trade-offs. Functions should be small and focused.

- PROSE OVER BULLETS in chat responses. Minimal headers. Compact replies.
  Don't over-structure.

- DON'T PUSH BACK on Adam's safety choices (no kill switch, no safety
  glasses) — both have been explicitly rejected and reaffirmed.

- DON'T RE-INVENT components. The owner modules are servo.py, camera.py,
  detector.py, tracker.py, laser.py, config.py, and control_panel.py.
  Modify them; don't duplicate their functionality.


CURRENT STATE AT SESSION BOUNDARY:

- Phases 1-5 complete. Closed-loop tracking works end-to-end at Kp=0.017
  with coast (1s of inertia after target loss) and recenter (smooth
  return to home if coast fails).
- Phase 6 BLOCKED: the bare-diode laser is dead (problems/002-laser-dead.md
  has the full diagnosis). MOSFET driver circuit is built and laser.py /
  test_laser.py are written — only the diode itself needs replacing. When
  it arrives, attach (red → 100Ω side, black → MOSFET drain) and click
  Fire 1 second in the control panel.
- Phase 7A is actionable in the meantime: cut the wooden base, 3D-print
  the pan-servo holder, mount Pi/PCA9685/LM2596/breadboard, route cables.
  Independent of the laser.
- Phases 7B (laser mount + boresight) and 8 (integration main.py) are
  gated on Phase 6.


WHEN ADAM WANTS TO TEST SOMETHING:

He launches control_panel.py via the "Laser Tracker" desktop shortcut on
the Pi (over VNC). The GUI sections cover:
- Servos: Center, sliders, Recalibrate limits…
- Laser: Enable laser controls + Fire 1 second + Force OFF
- Tools: Start tracking test…, Tune HSV detector…, Camera smoke test
- System: Reload config, Show config values, Shutdown Pi, Reboot Pi
- Emergency stop: big red bottom button (laser OFF + servos centered)

If Adam describes a test you'd otherwise satisfy with `python3 test_X.py`,
translate it to GUI buttons instead. If the workflow needs a button that
doesn't exist, add it to control_panel.py in the same commit as the
related code change.


READY: ask Adam what he wants to work on this session.
```

---

## How to use this prompt

1. Start a new Claude Code session (e.g., `claude` in a fresh terminal, or new chat in the Claude Desktop app).
2. Open this file, copy everything inside the triple-backtick block above.
3. Paste it as the first message in the new session.
4. The new Claude will read the referenced files, confirm understanding in 2-3 sentences, then wait for your direction.

If the new session ever tells you to type a terminal command for a hardware test that's already in the control panel, push back and link them to `feedback_use_control_panel.md` in the memory folder.
