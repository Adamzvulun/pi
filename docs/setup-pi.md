# Pi Setup Guide

Follow these steps in order on a fresh clone. Do everything from the laptop's SSH terminal unless a step says otherwise.

---

## Step 1 — SSH to the Pi and pull the latest code

```bash
ssh adam@<PI_IP>
cd ~/pi
git pull
```

Replace `<PI_IP>` with the Pi's current IP address (check your router or run `hostname -I` on the Pi).

---

## Step 2 — Create the Python virtual environment

The `--system-site-packages` flag is important — it lets the venv see `picamera2`, `cv2`, and `numpy`, which were installed via apt and aren't in requirements.txt.

```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
```

You'll see pip download the three Adafruit libraries. This takes a minute or two.

---

## Step 3 — Verify all imports work

```bash
python3 -c "import cv2, numpy, picamera2, board; from adafruit_pca9685 import PCA9685; print('OK')"
```

You should see `OK`. If you get a `ModuleNotFoundError`, the most likely cause is either the venv wasn't created with `--system-site-packages`, or `pip install -r requirements.txt` failed partway through.

---

## Step 4 — Run the placeholder

```bash
python3 main.py
```

Expected output: `Laser Tracker - placeholder. Replace with real code.`

---

## Step 5 — Set up the auto-pull cron job

This makes the Pi pull new code from GitHub automatically every minute.

First, create the logs folder:

```bash
mkdir -p ~/pi/logs
```

Then open the crontab editor:

```bash
crontab -e
```

Add this line at the bottom (select nano if it asks for an editor):

```
* * * * * cd /home/adam/pi && /usr/bin/git pull --rebase --autostash >> /home/adam/pi/logs/autopull.log 2>&1
```

Save and exit (in nano: Ctrl+O, Enter, Ctrl+X).

Then make sure the cron service is running:

```bash
sudo systemctl enable --now cron
```

To test it: push a small change from the laptop, wait 60 seconds, then check `~/pi/logs/autopull.log` on the Pi.

---

## Step 6 — Wire the Pi to the breadboard

**Do this with the Pi powered off (unplug the USB-C cable first).**

You need three jumper wires:

| Pi physical pin | Pi signal | Breadboard destination | Why |
|-----------------|-----------|------------------------|-----|
| Pin 3           | GPIO2 (SDA) | j14 | I2C data line to PCA9685 |
| Pin 5           | GPIO3 (SCL) | j13 | I2C clock line to PCA9685 |
| Pin 6           | GND         | blue (−) rail | Shared ground |

The GPIO18 laser wire (pin 12 → row 50) is left for later, when the laser module is physically attached.

See [docs/wiring.md](wiring.md) for the full wiring diagram.

---

## Step 7 — Power up and confirm the PCA9685 is detected

Power on in this order:
1. Plug in the 12V PSU to the MB102 first
2. Then plug the USB-C cable into the Pi

Wait ~30 seconds for the Pi to boot, then SSH back in:

```bash
ssh adam@<PI_IP>
i2cdetect -y 1
```

You should see a grid with `40` in it — that's the PCA9685. If the grid is all dashes, double-check the three wires from Step 6 and confirm I2C is enabled (`sudo raspi-config` → Interface Options → I2C).

---

## What's next

Once `40` appears in i2cdetect, you're ready for the first real code: `test_servo.py` to move the pan servo to center and sweep ±20°. Adam will ask Claude Code to write that.
