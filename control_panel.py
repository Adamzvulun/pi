"""
control_panel.py — central operator GUI for the laser tracker.

A tkinter window that wraps all the project's hardware subsystems
(servo, laser) and dev scripts (test_tracking, tune_detector,
calibrate_servo) so day-to-day operation doesn't require remembering
which terminal command does what.

How to run on the Pi (needs a GUI — use VNC):

    cd ~/pi && source venv/bin/activate
    python3 control_panel.py

Sections:
    - Status header: live pan/tilt angles, laser state, init state.
    - Servo controls: center, slider-driven move, launch calibrator.
    - Laser controls: hidden behind an "Enable" checkbox, has a
      confirmation dialog before firing. Force-OFF always works.
    - Tools: launch tracking test / HSV tuner / camera smoke test as
      subprocesses (so their cv2 windows don't conflict with tkinter).
    - System: reload config, show config, shutdown / reboot Pi.
    - Log pane: scrolling capture of logging output.
    - Emergency stop: big red button — laser OFF + servos centered.

Safety / design notes:
    - Hardware is initialized LAZILY via the "Initialize hardware"
      button. Just opening the GUI doesn't snap servos or claim GPIO18.
    - Laser controls require BOTH hardware-initialized AND the "Enable
      laser controls" checkbox before anything can fire.
    - Servo controls disable themselves while a tracking subprocess is
      running, so two processes don't fight over the PCA9685.
    - Window close handler runs cleanup: laser off, servos centered,
      devices released. Same pattern as test_tracking.py's finally block.

No new dependencies — tkinter is stdlib.
"""

import importlib
import logging
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Optional

import config
import laser
import servo

# Lazy-imported (heavy: cv2): camera, detector, tracker.

# ---- Logging setup --------------------------------------------------------
# Capture root logger so anything that uses `logging.getLogger(__name__)`
# inside servo.py / laser.py / etc. shows up in the GUI's log pane.

log = logging.getLogger(__name__)

_log_queue: "queue.Queue[str]" = queue.Queue()


class _QueueHandler(logging.Handler):
    """logging.Handler that pushes formatted records into a queue. The
    GUI's tick loop drains the queue into the scrolling text widget on
    the main tkinter thread (tk widgets aren't thread-safe)."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            msg = record.getMessage()
        _log_queue.put(msg)


# Wire the queue handler into the root logger.
_handler = _QueueHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s",
                                        "%H:%M:%S"))
logging.getLogger().addHandler(_handler)
logging.getLogger().setLevel(logging.INFO)


# ---- Subprocess helpers ---------------------------------------------------
# Long-running cv2 scripts (test_tracking, tune_detector, calibrate_servo)
# are launched in their own Python process. We track the Popen object so
# the GUI can detect when they finish and re-enable the servo controls.

PROJECT_DIR = os.path.expanduser("~/pi")


def _launch_script(filename: str) -> subprocess.Popen:
    """Launch a script in a new Python process under the venv. Returns
    the Popen so the caller can poll for completion.

    We use sys.executable so the GUI's interpreter (already in the venv)
    is reused — no `source venv/bin/activate` shell layer needed.
    """
    log.info("Launching %s as subprocess", filename)
    return subprocess.Popen(
        [sys.executable, filename],
        cwd=PROJECT_DIR,
    )


# ---- Main GUI class -------------------------------------------------------

class ControlPanel:
    """Top-level tkinter app. One instance per process."""

    POLL_INTERVAL_MS = 200  # how often _tick runs

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Laser Tracker — Control Panel")
        self.root.geometry("560x780")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Hardware state — None until "Initialize hardware" is clicked.
        self.kit = None
        self.laser_dev: Optional[laser.LED] = None

        # Tracks any cv2-heavy subprocess we've launched (tracking, tuner,
        # calibration). When set, servo controls are disabled.
        self.active_subprocess: Optional[subprocess.Popen] = None

        # tkinter Variables — bound to widgets, read in callbacks.
        self.var_pan = tk.DoubleVar(value=servo.PAN_CENTER)
        self.var_tilt = tk.DoubleVar(value=servo.TILT_CENTER)
        self.var_laser_enabled = tk.BooleanVar(value=False)

        # All widgets that should be disabled until hardware is initialized.
        self._hw_widgets: list = []
        # Widgets disabled while a subprocess is running.
        self._busy_widgets: list = []
        # Laser-control widgets — disabled unless hw initialized AND laser
        # controls enabled checkbox is ticked.
        self._laser_widgets: list = []

        self._build_ui()
        self._tick()

    # -- UI construction ----------------------------------------------------

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}

        # Status header
        header = ttk.LabelFrame(self.root, text="Status")
        header.pack(fill="x", **pad)

        self.lbl_init = ttk.Label(header, text="Hardware: not initialized")
        self.lbl_init.grid(row=0, column=0, sticky="w", padx=6, pady=2)

        self.lbl_pan = ttk.Label(header, text="Pan:  ---°")
        self.lbl_pan.grid(row=1, column=0, sticky="w", padx=6, pady=2)

        self.lbl_tilt = ttk.Label(header, text="Tilt: ---°")
        self.lbl_tilt.grid(row=1, column=1, sticky="w", padx=6, pady=2)

        self.lbl_laser = ttk.Label(header, text="Laser: --")
        self.lbl_laser.grid(row=2, column=0, sticky="w", padx=6, pady=2)

        self.btn_init = ttk.Button(header, text="Initialize hardware",
                                   command=self._on_init_hw)
        self.btn_init.grid(row=0, column=1, padx=6, pady=2, sticky="e")

        # Servo controls
        servo_frame = ttk.LabelFrame(self.root, text="Servos")
        servo_frame.pack(fill="x", **pad)

        btn_center = ttk.Button(servo_frame, text="Center", command=self._on_center)
        btn_center.grid(row=0, column=0, padx=6, pady=4)
        self._hw_widgets.append(btn_center)
        self._busy_widgets.append(btn_center)

        ttk.Label(servo_frame, text="Pan:").grid(row=1, column=0, sticky="e")
        slider_pan = ttk.Scale(
            servo_frame, from_=servo.PAN_MIN, to=servo.PAN_MAX,
            orient="horizontal", variable=self.var_pan, length=320,
        )
        slider_pan.grid(row=1, column=1, padx=6, pady=2, sticky="we")
        self.lbl_slider_pan = ttk.Label(servo_frame, width=6,
                                        text=f"{self.var_pan.get():.1f}°")
        self.lbl_slider_pan.grid(row=1, column=2, padx=6)
        self.var_pan.trace_add("write", lambda *a:
                               self.lbl_slider_pan.config(text=f"{self.var_pan.get():.1f}°"))
        self._hw_widgets.append(slider_pan)
        self._busy_widgets.append(slider_pan)

        ttk.Label(servo_frame, text="Tilt:").grid(row=2, column=0, sticky="e")
        slider_tilt = ttk.Scale(
            servo_frame, from_=servo.TILT_MIN, to=servo.TILT_MAX,
            orient="horizontal", variable=self.var_tilt, length=320,
        )
        slider_tilt.grid(row=2, column=1, padx=6, pady=2, sticky="we")
        self.lbl_slider_tilt = ttk.Label(servo_frame, width=6,
                                         text=f"{self.var_tilt.get():.1f}°")
        self.lbl_slider_tilt.grid(row=2, column=2, padx=6)
        self.var_tilt.trace_add("write", lambda *a:
                                self.lbl_slider_tilt.config(text=f"{self.var_tilt.get():.1f}°"))
        self._hw_widgets.append(slider_tilt)
        self._busy_widgets.append(slider_tilt)

        btn_apply = ttk.Button(servo_frame, text="Move to slider values",
                               command=self._on_apply_sliders)
        btn_apply.grid(row=3, column=0, columnspan=2, padx=6, pady=4, sticky="w")
        self._hw_widgets.append(btn_apply)
        self._busy_widgets.append(btn_apply)

        btn_recal = ttk.Button(servo_frame, text="Recalibrate limits...",
                               command=self._on_recalibrate)
        btn_recal.grid(row=3, column=2, padx=6, pady=4)
        self._busy_widgets.append(btn_recal)

        # Laser controls
        laser_frame = ttk.LabelFrame(self.root, text="Laser")
        laser_frame.pack(fill="x", **pad)

        chk_enable = ttk.Checkbutton(
            laser_frame, text="Enable laser controls",
            variable=self.var_laser_enabled,
            command=self._on_laser_enable_toggle,
        )
        chk_enable.grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=2)
        self._hw_widgets.append(chk_enable)

        btn_fire = ttk.Button(laser_frame, text="Fire 1 second",
                              command=self._on_fire)
        btn_fire.grid(row=1, column=0, padx=6, pady=4)
        self._laser_widgets.append(btn_fire)

        btn_force_off = ttk.Button(laser_frame, text="Force OFF",
                                   command=self._on_laser_off)
        btn_force_off.grid(row=1, column=1, padx=6, pady=4)
        self._hw_widgets.append(btn_force_off)  # always-available safety

        btn_boresight = ttk.Button(laser_frame, text="Boresight calibration...",
                                   command=self._on_boresight)
        btn_boresight.grid(row=1, column=2, padx=6, pady=4)
        # Boresight requires laser controls enabled (it fires the laser)
        self._laser_widgets.append(btn_boresight)
        self._busy_widgets.append(btn_boresight)

        # Tools
        tools = ttk.LabelFrame(self.root, text="Tools")
        tools.pack(fill="x", **pad)

        btn_track = ttk.Button(tools, text="Start tracking test...",
                               command=self._on_tracking)
        btn_track.grid(row=0, column=0, padx=6, pady=4)
        self._busy_widgets.append(btn_track)

        btn_tune = ttk.Button(tools, text="Tune HSV detector...",
                              command=self._on_tune_detector)
        btn_tune.grid(row=0, column=1, padx=6, pady=4)
        self._busy_widgets.append(btn_tune)

        btn_cam = ttk.Button(tools, text="Camera smoke test",
                             command=self._on_camera_test)
        btn_cam.grid(row=0, column=2, padx=6, pady=4)

        # System
        system = ttk.LabelFrame(self.root, text="System")
        system.pack(fill="x", **pad)

        ttk.Button(system, text="Reload config",
                   command=self._on_reload_config).grid(row=0, column=0, padx=6, pady=4)
        ttk.Button(system, text="Show config values",
                   command=self._on_show_config).grid(row=0, column=1, padx=6, pady=4)
        ttk.Button(system, text="Shutdown Pi",
                   command=self._on_shutdown).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(system, text="Reboot Pi",
                   command=self._on_reboot).grid(row=0, column=3, padx=6, pady=4)

        # Log pane
        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.pack(fill="both", expand=True, **pad)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state="disabled",
                                                  font=("Courier", 9))
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # Emergency stop
        estop = tk.Button(
            self.root, text="EMERGENCY STOP  (laser OFF + center servos)",
            bg="#cc0000", fg="white", font=("Helvetica", 12, "bold"),
            command=self._on_estop, height=2,
        )
        estop.pack(fill="x", **pad)

        # Apply initial enable/disable state.
        self._refresh_widget_states()

    # -- Widget state management -------------------------------------------

    def _refresh_widget_states(self) -> None:
        """Recompute enabled/disabled for every gated widget."""
        hw_ready = self.kit is not None
        busy = self.active_subprocess is not None
        laser_ok = (
            hw_ready
            and self.laser_dev is not None
            and self.var_laser_enabled.get()
            and not busy
        )

        for w in self._hw_widgets:
            w.state(["!disabled" if hw_ready else "disabled"])
        for w in self._busy_widgets:
            # busy disables on top of hw — both must allow.
            w.state(["!disabled" if (hw_ready and not busy) else "disabled"])
        for w in self._laser_widgets:
            w.state(["!disabled" if laser_ok else "disabled"])

    # -- Event handlers ----------------------------------------------------

    def _on_init_hw(self) -> None:
        """Initialize servo (snaps to center) and laser hardware."""
        if not messagebox.askyesno(
            "Initialize hardware",
            "This will snap the servos to their calibrated centers and "
            "claim GPIO18 for the laser. The bracket may move suddenly. "
            "Continue?",
        ):
            return

        try:
            log.info("Initializing servos...")
            self.kit = servo.init()
        except Exception:
            log.exception("Servo init failed")
            messagebox.showerror("Servo init failed",
                                 "Check the 12V PSU is on, I2C wiring, and "
                                 "that PCA9685 appears in `i2cdetect -y 1`.")
            return

        try:
            log.info("Initializing laser...")
            self.laser_dev = laser.init()
        except Exception:
            log.exception("Laser init failed")
            messagebox.showwarning(
                "Laser init failed",
                "Servos are up but laser GPIO setup failed. Laser controls "
                "will stay disabled. Servo controls still work.",
            )

        self.lbl_init.config(text="Hardware: initialized ✓")
        self.btn_init.config(state="disabled")
        self._refresh_widget_states()
        log.info("Hardware ready.")

    def _on_center(self) -> None:
        try:
            servo.center(self.kit)
        except Exception:
            log.exception("Center failed")

    def _on_apply_sliders(self) -> None:
        pan_target = self.var_pan.get()
        tilt_target = self.var_tilt.get()
        log.info("Moving to slider values: pan=%.1f° tilt=%.1f°", pan_target, tilt_target)
        try:
            # Use ramp=True (default) for human-controlled moves — smoother.
            servo.move_pan(self.kit, pan_target)
            servo.move_tilt(self.kit, tilt_target)
        except Exception:
            log.exception("Slider move failed")

    def _on_recalibrate(self) -> None:
        """Launch calibrate_servo.py in a new terminal so it's interactive."""
        if not messagebox.askyesno(
            "Recalibrate limits",
            "This opens calibrate_servo.py in a new terminal. After "
            "finding new limits, you'll need to edit servo.py manually "
            "and commit. Continue?",
        ):
            return
        # lxterminal is the default Bookworm-desktop terminal. Fall back
        # to xterm if absent.
        cmd = (
            f"cd {PROJECT_DIR} && source venv/bin/activate && "
            "python3 calibrate_servo.py; echo; read -p 'Press Enter to close...'"
        )
        for term in ("lxterminal", "xterm"):
            try:
                subprocess.Popen([term, "-e", "bash", "-lc", cmd])
                log.info("Opened %s with calibrate_servo.py", term)
                return
            except FileNotFoundError:
                continue
        messagebox.showerror("No terminal found",
                             "Neither lxterminal nor xterm is installed. "
                             "Open a terminal manually and run "
                             "`python3 calibrate_servo.py`.")

    def _on_laser_enable_toggle(self) -> None:
        if self.var_laser_enabled.get():
            log.warning("Laser controls ENABLED — fire button is live.")
        else:
            log.info("Laser controls disabled.")
        self._refresh_widget_states()

    def _on_fire(self) -> None:
        if not messagebox.askyesno(
            "Fire laser?",
            "Laser will fire for 1 second.\n\n"
            "Confirm the beam path is safe — pointed at a matte wall, "
            "no people, pets, mirrors, or windows in the path.",
        ):
            return
        try:
            laser.fire(self.laser_dev)
            # Schedule the off in 1 second without blocking the UI.
            self.root.after(1000, lambda: laser.off(self.laser_dev))
        except Exception:
            log.exception("Fire failed")

    def _on_laser_off(self) -> None:
        try:
            laser.off(self.laser_dev)
        except Exception:
            log.exception("Force-off failed")

    def _on_tracking(self) -> None:
        if not messagebox.askyesno(
            "Run tracking test",
            "Launches test_tracking.py. The bracket may snap to center "
            "on startup. Servo controls in this panel will be disabled "
            "while it runs.",
        ):
            return
        # If we already initialized servos in this process, release them
        # first so test_tracking can claim them without conflict.
        if self.kit is not None:
            try:
                log.info("Releasing servos so subprocess can claim them.")
                servo.cleanup(self.kit)
            except Exception:
                log.exception("Pre-launch cleanup failed (continuing)")
            self.kit = None
            self.lbl_init.config(text="Hardware: not initialized")
            self.btn_init.config(state="normal")
        self.active_subprocess = _launch_script("test_tracking.py")
        self._refresh_widget_states()

    def _on_tune_detector(self) -> None:
        self.active_subprocess = _launch_script("tune_detector.py")
        self._refresh_widget_states()

    def _on_boresight(self) -> None:
        """Launch calibrate_boresight.py to measure camera↔laser pixel offset.

        Needs the laser GPIO (which we currently hold), so release it
        first; the subprocess will re-claim it. We re-init the laser
        ourselves once the subprocess exits — see _tick()."""
        if not messagebox.askyesno(
            "Boresight calibration",
            "This launches calibrate_boresight.py in a new window.\n\n"
            "Before continuing:\n"
            "  • Aim the bracket at a matte target ~1-2 m away using the\n"
            "    servo sliders (the cyan crosshair should be on the target)\n"
            "  • Confirm the beam path is safe — no people, pets, mirrors\n"
            "    or windows in line with the laser\n\n"
            "Inside the tool: press 'f' to fire and capture, click the\n"
            "laser dot if auto-detection missed it, press 's' to save.\n\n"
            "Continue?",
        ):
            return

        # Release the laser GPIO so the subprocess can claim it. We do NOT
        # release the servos — boresight reads camera only, and we want the
        # operator to keep aiming via control-panel sliders if needed (after
        # the subprocess exits).
        if self.laser_dev is not None:
            try:
                log.info("Releasing laser GPIO so boresight subprocess can claim it.")
                laser.cleanup(self.laser_dev)
            except Exception:
                log.exception("Pre-launch laser cleanup failed (continuing)")
            self.laser_dev = None
            # The lgpio kernel release isn't always visible to a child
            # process that starts within a few ms. A short pause gives the
            # release time to propagate before the subprocess calls LED(18).
            # laser.init() also retries internally for belt-and-braces.
            time.sleep(0.2)

        self.active_subprocess = _launch_script("calibrate_boresight.py")
        self._refresh_widget_states()

    def _on_camera_test(self) -> None:
        """Capture one frame and report its shape (proves cam works)."""
        try:
            import camera as cam_mod
            cap = cam_mod.init()
            frame = cam_mod.capture_frame(cap)
            cam_mod.release(cap)
            log.info("Camera smoke test OK — frame shape %s", frame.shape)
        except Exception:
            log.exception("Camera smoke test failed")

    def _on_reload_config(self) -> None:
        """Re-import config so HSV/PID changes take effect live."""
        try:
            importlib.reload(config)
            log.info("Config reloaded.")
        except Exception:
            log.exception("Config reload failed")

    def _on_show_config(self) -> None:
        """Dump current config to the log."""
        log.info("=== Current config ===")
        log.info("Frame: %dx%d (center %d,%d)",
                 config.FRAME_WIDTH, config.FRAME_HEIGHT,
                 config.FRAME_CENTER_X, config.FRAME_CENTER_Y)
        log.info("HSV: lower=%s upper=%s", config.HSV_LOWER, config.HSV_UPPER)
        log.info("Detection: MIN_CONTOUR_AREA=%d FIRE_PIXEL_THRESHOLD=%d",
                 config.MIN_CONTOUR_AREA, config.FIRE_PIXEL_THRESHOLD)
        log.info("PID: Kp=%.4f Ki=%.4f Kd=%.4f output_limit=%.1f deadband=%d",
                 config.KP_PAN, config.KI_PAN, config.KD_PAN,
                 config.PID_OUTPUT_LIMIT, config.TRACKING_DEADBAND_PX)
        log.info("Servo limits (from servo.py): PAN %g-%g TILT %g-%g",
                 servo.PAN_MIN, servo.PAN_MAX, servo.TILT_MIN, servo.TILT_MAX)
        log.info("Boresight: dx=%+d dy=%+d (run boresight calibration to update)",
                 config.BORESIGHT_X_OFFSET, config.BORESIGHT_Y_OFFSET)

    def _on_shutdown(self) -> None:
        if not messagebox.askyesno("Shutdown Pi",
                                   "Shut down the Raspberry Pi now?"):
            return
        log.warning("Shutting down Pi.")
        self._cleanup_hardware()
        subprocess.Popen(["sudo", "shutdown", "-h", "now"])

    def _on_reboot(self) -> None:
        if not messagebox.askyesno("Reboot Pi",
                                   "Reboot the Raspberry Pi now?"):
            return
        log.warning("Rebooting Pi.")
        self._cleanup_hardware()
        subprocess.Popen(["sudo", "reboot"])

    def _on_estop(self) -> None:
        """Emergency stop — laser off, servos centered. No confirmation."""
        log.warning("EMERGENCY STOP triggered.")
        if self.laser_dev is not None:
            try:
                laser.off(self.laser_dev)
            except Exception:
                log.exception("E-stop: laser off failed")
        if self.kit is not None:
            try:
                servo.center(self.kit)
            except Exception:
                log.exception("E-stop: center failed")

    # -- Window close / cleanup --------------------------------------------

    def _cleanup_hardware(self) -> None:
        """Drive laser off, center servos, release devices."""
        if self.laser_dev is not None:
            try:
                laser.cleanup(self.laser_dev)
            except Exception:
                log.exception("Laser cleanup failed")
            self.laser_dev = None
        if self.kit is not None:
            try:
                servo.cleanup(self.kit)
            except Exception:
                log.exception("Servo cleanup failed")
            self.kit = None

    def _on_close(self) -> None:
        log.info("Closing control panel — cleaning up hardware.")
        # Terminate any subprocess we own.
        if self.active_subprocess is not None and self.active_subprocess.poll() is None:
            log.info("Terminating subprocess pid=%d", self.active_subprocess.pid)
            self.active_subprocess.terminate()
        self._cleanup_hardware()
        self.root.destroy()

    # -- Periodic tick (status refresh + log drain + subprocess poll) -------

    def _tick(self) -> None:
        # Drain log queue into the text widget.
        while not _log_queue.empty():
            try:
                msg = _log_queue.get_nowait()
            except queue.Empty:
                break
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")

        # Refresh status labels.
        pan = servo.current_pan()
        tilt = servo.current_tilt()
        self.lbl_pan.config(text=f"Pan:  {pan:.1f}°" if pan is not None else "Pan:  ---°")
        self.lbl_tilt.config(text=f"Tilt: {tilt:.1f}°" if tilt is not None else "Tilt: ---°")

        if self.laser_dev is None:
            self.lbl_laser.config(text="Laser: --")
        else:
            on = bool(self.laser_dev.is_active)
            self.lbl_laser.config(text=f"Laser: {'ON ⚠' if on else 'OFF'}")

        # Poll any active subprocess — when it exits, re-enable controls.
        if self.active_subprocess is not None:
            if self.active_subprocess.poll() is not None:
                rc = self.active_subprocess.returncode
                log.info("Subprocess exited with code %d.", rc)
                self.active_subprocess = None

                # If we released the laser GPIO for a subprocess (boresight),
                # re-claim it now so the Fire button works again without
                # forcing the operator back through "Initialize hardware".
                # Only attempt this if servos are still up — otherwise we're
                # in the post-tracking state and need a full re-init anyway.
                if self.laser_dev is None and self.kit is not None:
                    try:
                        self.laser_dev = laser.init()
                        log.info("Re-claimed laser GPIO after subprocess exit.")
                    except Exception:
                        log.exception("Re-init laser failed — click Initialize hardware again.")

                # Reload config so any values the subprocess wrote
                # (HSV from tuner, boresight from calibrator, etc.) become
                # visible to this process on the next read.
                try:
                    importlib.reload(config)
                except Exception:
                    log.exception("Auto-reload of config after subprocess failed (continuing)")

                self._refresh_widget_states()

        self.root.after(self.POLL_INTERVAL_MS, self._tick)


def main() -> int:
    root = tk.Tk()
    try:
        # Some Bookworm desktops default to ugly tk theming. 'clam' is a
        # reasonable cross-platform choice that doesn't look like 1995.
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    ControlPanel(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
