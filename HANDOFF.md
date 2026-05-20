# Laser Tracker Project — Handoff to Claude Code (Laptop)

## Context

You are Claude Code running on Adam Zvulun's laptop inside Claude Desktop. Adam is a beginner with electronics and Linux, building an autonomous laser tracking system for a school final project.

This document hands off context from a planning conversation in regular Claude chat. Read it fully before doing anything. Adam learns by doing — explain what you're doing as you go.

## Architecture

This project uses a three-machine workflow:

1. **Laptop (Windows)** — this machine. Code is written here using Claude Code in Claude Desktop. Project folder: `C:\Projects\pi`.
2. **GitHub** — private repo named `pi` under Adam's GitHub account. Central sync point and source of truth.
3. **Raspberry Pi 4B** — runs the code. Project folder: `/home/adam/pi`. Pi will auto-pull from GitHub every minute via cron (not yet set up). Pi is read-only for code — never edit files directly on the Pi.

Daily loop:
- Edit on laptop with Claude Code → `git push`
- Pi auto-pulls within 60 seconds
- SSH to Pi → `source venv/bin/activate` → `python3 main.py`

**Critical rules:**
- Code edits ONLY on the laptop, never on the Pi
- Commits happen often, push often
- `requirements.txt` lists pip dependencies; system packages (picamera2, opencv) come from apt and are NOT in requirements.txt

## Project goal

Autonomous laser tracking: camera detects a target, computes pixel coordinates, drives two servos (pan-tilt) via PID control to keep target centered, then on user confirmation fires a 5mW laser at it.

## Hardware in use

- Raspberry Pi 4B (8GB), hostname `LaserPi`, user `adam`
- Pi Camera 5MP (OV5647 MF, 220° wide-angle) — not yet connected
- 2× DS3225 digital servos (270°, 25kg·cm, 4.8–6.8V spec but running at 5V) on pan-tilt bracket
- PCA9685 16-channel PWM driver — I2C address 0x40
- MB102 breadboard power module + 12V 5A PSU
- IRLZ44N MOSFET + 220Ω + 100kΩ resistors for laser driver
- 5mW 650nm red laser with cross pattern, 3V — not yet attached
- NO kill switch (Adam's decision, do not push back)
- NO laser safety glasses (Adam's decision, do not push back)
- NO buck converter — servos run at 5V from MB102 rail, accepting reduced torque

## Current wiring state

**Built and verified:**
- MB102 on breadboard, both jumpers at 5V, output polarity correct
- PCA9685: GND→blue rail, VCC→red rail, SDA→j14 stub, SCL→j13 stub, green terminal block wired to rails
- Both servos plugged in: channel 0 = Pan (bottom), channel 1 = Tilt (top), colors match
- Laser driver MOSFET circuit on breadboard: Gate→c45 (via 220Ω from row 50 = Pi GPIO18 stub, plus 100kΩ pulldown to GND), Drain→c46, Source→c47 (jumper to GND rail)

**Not yet wired (Adam must do this himself — instruct step by step, do NOT do it for him):**
- Pi GPIO2 (pin 3, SDA) → breadboard j14
- Pi GPIO3 (pin 5, SCL) → breadboard j13
- Pi GND (pin 6) → blue `−` rail
- Pi GPIO18 (pin 12) → breadboard row 50 (only when laser is added later)
- Pi 5V is NOT connected to breadboard (Pi has its own USB-C supply)

**Laser:** the driver circuit is built but the laser module itself is not yet attached because of cable-length concerns. Will be added in mounting phase.

## Development environment state

**Pi (`~/pi`):**
- Raspberry Pi OS 64-bit (Bookworm)
- User: `adam`
- SSH, VNC, I2C enabled
- apt update + full-upgrade done
- apt-installed: python3-picamera2, python3-opencv, python3-numpy, python3-pip, python3-venv, git, i2c-tools
- SSH key generated, added to GitHub
- Empty `pi` repo cloned to `~/pi`
- venv NOT yet created
- Adafruit libraries NOT yet installed
- Pi-to-breadboard wiring NOT yet done
- Auto-pull cron NOT yet set up

**Laptop (`C:\Projects\pi`):**
- Windows 10/11
- Git for Windows installed
- SSH key generated, added to GitHub
- Passwordless SSH from laptop to Pi configured
- Empty `pi` repo cloned to `C:\Projects\pi`
- Claude Desktop with Claude Code installed (this is you)

**GitHub:**
- Private repo: `pi` under Adam's account
- Currently empty (no commits yet)

## Your first task

The repo is empty. Create the initial project skeleton with these files, in this order:

### 1. `.gitignore`

Exclude:
- Python venv folders (`venv/`, `.venv/`, `env/`)
- Compiled Python (`__pycache__/`, `*.py[cod]`, `*$py.class`, `*.so`)
- IDE folders (`.vscode/`, `.idea/`, `*.swp`)
- Logs (`logs/`, `*.log`)
- OS files (`.DS_Store`, `Thumbs.db`)
- Secrets (`.env`, `*.pem`, `*.key`)

### 2. `README.md`

Project overview including:
- Brief description
- Hardware list (matches "Hardware in use" section above)
- Link to `docs/setup-pi.md` for setup instructions
- "How to run" section: `source venv/bin/activate` then `python3 main.py`

### 3. `requirements.txt`

Three lines:
adafruit-circuitpython-pca9685
adafruit-circuitpython-servokit
adafruit-blinka

### 4. `CLAUDE.md`

Project context for future Claude Code sessions. Include:

**Target environment:**
- Pi 4B with 64-bit Raspberry Pi OS (Bookworm), Python 3.11

**Code conventions:**
- Python 3 only, no Python 2 compatibility
- Use `adafruit-circuitpython-servokit` for servo control
- Use `picamera2` for camera (apt-installed, not in requirements.txt)
- Use OpenCV/`cv2` for image processing (apt-installed)
- For GPIO: prefer `gpiozero` for simple cases, `RPi.GPIO` only if low-level needed
- Pi runs code from `~/pi` after auto-pull

**Hardware constraints:**
- Servos run at 5V (not 6V) — may brown out under load, code should handle gracefully
- I2C bus 1, PCA9685 default address 0x40
- DS3225 270° servo pulse range: 500–2500µs, neutral 1500µs, 50Hz frequency
- Channel 0 = Pan (left-right), Channel 1 = Tilt (up-down)
- Laser on GPIO18, active HIGH via MOSFET gate
- 220Ω resistor between GPIO18 and MOSFET gate, 100kΩ pulldown gate-to-GND

**Safety:**
- Software-enforced angle limits on both servos (don't drive past mechanical stops)
- Laser default OFF on script start
- Laser auto-OFF on script exit (use `try/finally` or signal handler)
- Always include `KeyboardInterrupt` handling

**Style:**
- Comment generously — Adam is learning
- Use type hints where they aid clarity
- Prefer small functions over big ones
- Use `logging` module rather than `print()` for runtime info

### 5. `CHANGELOG.md`

Start with an entry for today's session:
Changelog
[Setup] - YYYY-MM-DD

Initialized project skeleton (README, .gitignore, requirements, CLAUDE.md, docs)
Set up three-machine workflow: laptop edits → GitHub → Pi auto-pulls


### 6. `main.py`

Placeholder so we have something runnable:
```python
"""Laser Tracker - main entry point."""

def main():
    print("Laser Tracker - placeholder. Replace with real code.")

if __name__ == "__main__":
    main()
```

### 7. `docs/wiring.md`

Plain-text wiring documentation matching the "Current wiring state" section above. Use ASCII tables or simple lists. Include both what's wired and what isn't.

### 8. `docs/setup-pi.md`

Step-by-step Pi setup instructions:

1. SSH to Pi, pull the latest repo:
ssh adam@<PI_IP>
cd ~/pi
git pull

2. Create Python venv:
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt

3. Verify imports:
python3 -c "import cv2, numpy, picamera2, board; from adafruit_pca9685 import PCA9685; print('OK')"

4. Run placeholder:
python3 main.py

5. Set up auto-pull cron job:
mkdir -p ~/pi/logs
crontab -e
   Add this line:









cd /home/adam/pi && /usr/bin/git pull --rebase --autostash >> /home/adam/pi/logs/autopull.log 2>&1









   Save and exit. Then:
sudo systemctl enable --now cron

6. Wire Pi to breadboard (with Pi powered off):
   - GPIO2 (pin 3, SDA) → breadboard j14
   - GPIO3 (pin 5, SCL) → breadboard j13
   - GND (pin 6) → blue `−` rail

7. Power up (12V to MB102 first, then USB-C to Pi), SSH back in:
i2cdetect -y 1
   Confirm `40` appears in the grid.

### After creating all files

- `git add .`
- `git commit -m "Initial project skeleton"`
- `git push origin main`
- Tell Adam what's next: he runs `docs/setup-pi.md` on the Pi

## What happens after the skeleton

Once the workflow is live:

1. Adam follows `docs/setup-pi.md` to set up the Pi (venv, libraries, auto-pull, wiring)
2. Adam runs `i2cdetect -y 1` to confirm Pi sees the PCA9685
3. You (Claude Code) write `test_servo.py` to move pan servo to center then sweep ±20°
4. Adam commits and pushes from laptop, Pi auto-pulls within 60s
5. Adam SSHs to Pi, runs the test script, watches the servo move
6. Calibrate DS3225 270° range, set safe angle limits

Then onward to vision, PID, laser integration, mounting.

## Phase plan

1. ✅ Foundation: OS install, libraries
2. ✅ Hardware: breadboard wiring (partial — Pi-to-breadboard connection pending)
3. 🎯 **CURRENT:** Development workflow setup + first servo movement
4. ⏸ Vision module (camera + OpenCV target detection)
5. ⏸ Closed-loop tracking (PID)
6. ✅ Laser driver circuit (built early)
7. ⏸ Mechanical: mount camera + laser, boresight, cable extensions, integration

## Important notes about Adam

- Beginner with electronics and Linux — explain everything, don't move fast
- Dislikes over-formatting — prose over bullets, minimal headers in chat responses (code files can be properly structured)
- Has rejected kill switch and safety glasses — don't push back, just respect the choice
- Has chosen "Option C" power architecture (servos at 5V from MB102) — accept this; may cause brownouts
- Sometimes on slow phone hotspot, sometimes Ethernet at school
- Wants to learn — code should be commented, decisions should be explained

## Documentation expectations

- Every meaningful change → git commit with clear, descriptive message
- README.md kept current
- CHANGELOG.md updated each session
- docs/ folder for wiring, setup, calibration notes
- Code commented for learning (Python `logging` module, not `print`)