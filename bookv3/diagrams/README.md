# diagrams/ — review, placement, and rendering notes

This folder holds all 11 Mermaid (`.mmd`) source files used as figures in the v3 book. Each file is a standalone Mermaid flowchart that you render to PNG/SVG externally (mermaid-cli, mermaid.live, or VS Code preview) and embed into the relevant chapter.

This README captures:

1. The review that was done on each diagram against the ground truth (`CLAUDE.md` and the actual code in the repo).
2. Exactly which chapter each diagram belongs in.
3. A one-line "what is this" for each diagram.
4. The global edge-style change applied to all 11 files.

## Global change — straight lines instead of bezier curves

All 11 `.mmd` files now start with:

```
%%{init: {'flowchart': {'curve': 'linear', 'nodeSpacing': ..., 'rankSpacing': ...}}}%%
```

Mermaid's default edge style is `basis` (smooth bezier), which renders edges as squiggly curves. Switching to `linear` forces straight polylines with sharp right-angle bends where the dagre layout engine needs to route around blocks. `nodeSpacing` and `rankSpacing` are bumped per diagram so labels don't collide and edges have room to bend cleanly.

Dagre already routes edges *around* nodes — actual edge-through-block overlaps are rare. Where edges visually cross *each other* in dense diagrams (`full-schematic`, `software-topdown`), the extra rank spacing gives them room.

## Per-diagram review

### 1. `system-overview.mmd` — top-level block diagram

- **Data:** ✅ Matches `CLAUDE.md` exactly (12V PSU → LM2596 → servo rail; USB-C → Pi → logic rail; PCA9685, DS3225 ch0/ch1, LifeCam, IRLZ44N + 5mW 650nm laser, GPIO18).
- **Place in:** **Chapter 8 — תיאור החלופה הנבחרת** (`chapters/08-selected-alternative.md`), as the opening figure of "this is the architecture we built." Also reusable as the headline figure of **Chapter 11**.
- **What it is:** Single-page bird's-eye of the whole system. The "anchor diagram" the reader should see first.

### 2. `proposal-block-diagram.mmd` — proposal-era block diagram (Hebrew)

- **Data:** ⚠️ Intentionally shows **"Pi Camera v3"** (CSI), not LifeCam USB. This is correct — it is the *original proposal*. Chapter 1 already explains the later switch to USB.
- **Place in:** **Chapter 1 — הצעת הפרויקט שאושרה** (`chapters/01-approved-proposal.md`, §1.5). Already referenced there as `proposal-block-diagram.png` — render this `.mmd` to that PNG.
- **What it is:** Historical/proposal version. Do not "fix" its camera to LifeCam; the gap between this and `system-overview.mmd` is part of the story the book tells.

### 3. `hardware-topdown.mmd` — hierarchical HW breakdown

- **Data:** ✅ All 6 subsystems (Power / Compute / Sensing / Actuation / Emitter / Mechanical) and all leaf components match. Servo angle limits are not shown here (they belong in calibration text, not topology). MB-102 breadboard listed under Emitter is fine — it is the physical mount for the MOSFET circuit, just currently unwired pending Phase 6.
- **Place in:** **Chapter 10 — הסבר רכיבים** (`chapters/10-components.md`), at the top of the chapter as a "you-are-here" map before the per-component prose. Also good in **Chapter 11** "ארכיטקטורה חומרתית" section.
- **What it is:** Top-down decomposition. Helps the reader navigate ch.10's component-by-component prose.

### 4. `software-topdown.mmd` — hierarchical SW breakdown

- **Data:** ✅ All owner modules, all test/calibration scripts, all third-party libs match `CLAUDE.md` "Module design pattern" table and the ownership table in chapter 11. `main.py` correctly marked "final integration entry."
- **Place in:** **Chapter 11 — תיאור הארכיטקטורה** (`chapters/11-architecture.md`), inside the "ארכיטקטורת תוכנה" section right after the ownership table. Also good as opener of **Chapter 13 — הסבר ספריות**.
- **What it is:** Shows owner-modules + their libs + the test scripts that exercise them. Mirrors the table in ch.11 visually.

### 5. `functional-diagram.mmd` — functional / signal flow

- **Data:** ✅ Modules and dependencies correct. Lists tkinter, `cv2 + numpy`, `simple-pid`, ServoKit/Blinka explicitly. Subgraphs cleanly separate Orchestration / Logic / HW Abstraction / Config / Third-Party.
- **Place in:** **Chapter 15 — תיעוד הפתרון** (`chapters/15-solution-documentation.md`), **§15.5 תרשים פונקציונלי**. Already referenced there.
- **What it is:** The מחוון-required Functional Diagram. Has its placeholder in the book already.

### 6. `full-schematic.mmd` — wiring schematic

- **Data:** ✅ Pi pins all correct (2 = 5V, 3 = SDA, 5 = SCL, 6 = GND, 12 = GPIO18, 4 = 5V for laser). Resistor values (220 Ω gate, 100 kΩ pulldown, 100 Ω current-limit) match. Topology correct. *Minor stylistic*: the pulldown is drawn as `MOSFET -.-> R100k -.-> GND` rather than as a parallel side branch from a dedicated Gate node — that's fine, this is the high-level schematic and the detailed view is in `laser-driver.mmd`.
- **Place in:** **Chapter 15 — תיעוד הפתרון** (`chapters/15-solution-documentation.md`), **§15.1 שרטוט חשמלי**. Already referenced there.
- **What it is:** The "wiring drawing" the מחוון requires. Placeholder for it already exists in the chapter.

### 7. `power-distribution.mmd` — power rails only

- **Data:** ✅ Two-source split (12V → LM2596 → servo rail; USB-C → Pi → logic rail) with shared GND. Current estimates plausible (Pi ~600 mA, logic rail ~50 mA, servo rail ~1 A typical).
- **Place in:** **Chapter 10 — הסבר רכיבים** (`chapters/10-components.md`), inside the "אספקת חשמל" section. Also a natural companion to **§15.1**.
- **What it is:** Zooms in on just the power topology — the story of why we have two separate 5V rails (problem 001).

### 8. `i2c-chain.mmd` — I²C bus only

- **Data:** ✅ Pi pin 3 = GPIO2/SDA, pin 5 = GPIO3/SCL, pin 6 = GND. Does *not* include VCC (intentional — VCC is power, not bus).
- **Place in:** **Chapter 12 — תיאור פרוטוקולי תקשורת** (`chapters/12-protocols.md`), in the "I²C — בין ה־Pi לבין PCA9685" section.
- **What it is:** Minimal 2-wire bus illustration. Pairs with the I²C protocol prose.

### 9. `laser-driver.mmd` — MOSFET driver detail

- **Data:** ✅ Full low-side switch topology: GPIO18 (pin 12) → 220 Ω → Gate; pulldown 100 kΩ Gate ↔ GND; 5V (pin 4) → 100 Ω → Laser+ → Laser− → Drain; Source → GND (pin 14). All consistent with `CLAUDE.md` hardware table.
- **Place in:** **Chapter 10 — הסבר רכיבים** (`chapters/10-components.md`), inside "מעגל הלייזר: MOSFET IRLZ44N".
- **What it is:** Component-level zoom on the laser driver — the only schematic in the book that shows the gate / pulldown / source / drain explicitly.

### 10. `control-loop.mmd` — closed-loop tracking pipeline

- **Data:** ✅ Camera 640×480 @ 30 Hz, pipeline `blur → HSV → inRange → morph → centroid`, servo clamps `50..220 / 115..205` (matches `PAN/TILT_MIN/MAX` in `config.py`), PCA9685 `50 Hz PWM 500–2500 µs`. "Closes the loop" dotted arrow Mech → Target is the textbook control-loop convention.
- **Place in:** **Chapter 9 — הסבר על הבקר** (`chapters/09-controller.md`), right after the time-budget section. Also a good headline figure for **Chapter 13** when discussing `simple-pid`.
- **What it is:** The canonical "control loop" figure — sensor → controller → actuator → plant → back. Shows the pixel-error → angle-correction path.

### 11. `control-flow.mmd` — main-loop / FSM

- **Data:** ✅ All 5 FSM states present (Tracking / Locked / Coasting / Recentering / Holding) and match `tracker.py`. Loop structure (Init → Capture → Detect → Update → Draw → WaitKey) matches `test_tracking.py`. The dotted side-note for FSM states is a good touch.
- **Place in:** **Chapter 15 — תיעוד הפתרון** (`chapters/15-solution-documentation.md`), **§15.4 תרשים זרימה — לולאת המעקב**. The chapter currently has a simpler inline mermaid block there — **replace it with the rendered output of this file** (it is the better, complete version; the inline one omits Init/Cleanup and `waitKey`).
- **What it is:** Standard מחוון-required flowchart. This is the one to render and embed in §15.4.

## Summary table

| # | File | Place in chapter | Status |
|---|---|---|---|
| 1 | `system-overview.mmd` | ch. 8 (also ch. 11) | ✅ data correct |
| 2 | `proposal-block-diagram.mmd` | ch. 1 §1.5 | ✅ correct as proposal-era snapshot |
| 3 | `hardware-topdown.mmd` | ch. 10 (top) | ✅ data correct |
| 4 | `software-topdown.mmd` | ch. 11 (sw section) | ✅ data correct |
| 5 | `functional-diagram.mmd` | ch. 15 §15.5 | ✅ already referenced |
| 6 | `full-schematic.mmd` | ch. 15 §15.1 | ✅ already referenced |
| 7 | `power-distribution.mmd` | ch. 10 (power section) | ✅ data correct |
| 8 | `i2c-chain.mmd` | ch. 12 (I²C section) | ✅ data correct |
| 9 | `laser-driver.mmd` | ch. 10 (laser section) | ✅ data correct |
| 10 | `control-loop.mmd` | ch. 9 (after time budget) | ✅ data correct |
| 11 | `control-flow.mmd` | ch. 15 §15.4 (replace inline) | ✅ data correct |

## How to render

Pick one of:

- **Mermaid CLI** (`mmdc`) — `mmdc -i diagrams/system-overview.mmd -o diagrams/system-overview.png -w 1600`
- **mermaid.live** — paste the `.mmd` content, export PNG/SVG.
- **VS Code Mermaid preview extension** — render in editor and screenshot.

Place the rendered images alongside the chapter Markdown (e.g. `chapters/system-overview.png`) and reference them with standard Markdown image syntax. The Pandoc `build-book.sh` pipeline does not auto-render Mermaid — pre-rendered images are required for the `.docx` output.
