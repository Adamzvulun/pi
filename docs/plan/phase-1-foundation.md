# Phase 1 — Foundation ✅ COMPLETE

## Goal

Get a usable Raspberry Pi development environment: OS, system packages, Python venv, hardware interfaces enabled (I2C, SSH, VNC), and a working laptop ↔ GitHub ↔ Pi code-sync loop.

## What we built

**OS and system packages.** Raspberry Pi OS 64-bit (Bookworm) on a Pi 4B (8GB). Hostname `LaserPi`, user `adam`. Apt packages: `python3-picamera2`, `python3-opencv`, `python3-numpy`, `python3-gpiozero`, `rpicam-apps`, `python3-pip`, `python3-venv`, `git`, `i2c-tools`. SSH, VNC, and I2C enabled via `raspi-config`.

**Python venv.** Created with `python3 -m venv --system-site-packages venv`. The `--system-site-packages` flag is essential because picamera2 / cv2 / numpy are apt-installed system packages, not pip-installable.

**Pip dependencies** (`requirements.txt`):
- `adafruit-circuitpython-pca9685`
- `adafruit-circuitpython-servokit`
- `adafruit-blinka`
- `simple-pid`

**Three-machine workflow.** Code is edited on the laptop (`C:\Projects\pi`) → pushed to GitHub → Pi auto-pulls every minute via cron. Code is NEVER edited directly on the Pi.

## Decisions made and why

- **Raspberry Pi OS 64-bit Bookworm** rather than Bullseye: current LTS, better libcamera support, native Python 3.11.
- **`--system-site-packages` for the venv:** the alternative is pip-installing picamera2 inside the venv, which is complicated. Letting the venv see system packages is simpler and reliable.
- **Auto-pull via cron every minute** rather than git hooks or manual pulls: simplest possible sync. 60-second latency is fine for hardware iteration.
- **Hostname `LaserPi.local` via mDNS** rather than fixed IP: works on any network without IP lookup.

## Files created

| File | Purpose |
|------|---------|
| `requirements.txt` | Pip packages list |
| `docs/setup-pi.md` | One-shot Pi setup walkthrough |
| `.gitignore` | Excludes venv, `__pycache__`, secrets |
| `README.md` | Project overview |
| `CLAUDE.md` | Project context for Claude Code sessions |
| `CHANGELOG.md` | Session log |
| `HANDOFF.md` | Session quickstart — refreshed each significant milestone |
| `main.py` | Placeholder |

## Final state / outputs

- `python3 -c "import cv2, numpy, picamera2, board; from adafruit_pca9685 import PCA9685; print('OK')"` succeeds
- Auto-pull cron runs every minute, logs to `~/pi/logs/autopull.log`
- SSH and VNC reachable at `LaserPi.local`

## Operating procedures

See [`docs/setup-pi.md`](../setup-pi.md) for the one-time setup walkthrough. For daily workflow commands (SSH, push, run), see [`docs/operating-guide.md`](../operating-guide.md).
