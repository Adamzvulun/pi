# Pi Setup Guide

Follow these steps in order on a fresh clone. Do everything from the laptop's SSH terminal unless a step says otherwise.

---

## Step 1 — SSH to the Pi and pull the latest code

```bash
ssh adam@<PI_IP>
cd ~/pi
git pull
```

Replace `<PI_IP>` with the Pi's IP address. The easiest way — if you're on the same network — is to use the hostname directly instead of an IP:

```bash
ssh adam@LaserPi.local
```

That works without needing to look up the IP address. If it doesn't resolve, fall back to the IP (check your router admin page, or run `hostname -I` on the Pi while physically logged in).

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

If it asks you to choose an editor, type `1` and press Enter to pick nano.

You'll land inside nano looking at the crontab file. There are probably some comment lines starting with `#`. You need to get to the very bottom of the file and add one new line. Here's how:

1. Press `Ctrl+End` to jump to the last line (or just press the down arrow key until you can't go further).
2. Press `End` to make sure your cursor is at the end of that last line.
3. Press `Enter` once to start a new blank line.
4. Now type (or paste) the cron line. To paste in most SSH terminals, right-click in the terminal window — that pastes whatever is in your clipboard. If right-click doesn't work, try `Shift+Insert`. If you're in Windows Terminal, `Ctrl+Shift+V` also works.

The line to add:

```
* * * * * cd /home/adam/pi && /usr/bin/git pull --rebase --autostash >> /home/adam/pi/logs/autopull.log 2>&1
```

Once the line is in, save and exit nano: press `Ctrl+O`, then `Enter` to confirm the filename, then `Ctrl+X` to close.

Then make sure the cron service is running:

```bash
sudo systemctl enable --now cron
```

To test it: push a small change from the laptop, wait 60 seconds, then check `~/pi/logs/autopull.log` on the Pi.

---

## Step 6 — Wire the Pi to the breadboard

**Do this with the Pi powered off (unplug the USB-C cable first).**

You need three jumper wires. These connect the Pi's I2C bus and ground to the breadboard so it can talk to the PCA9685 servo driver.

**Finding the pins:** hold the Pi with the USB ports facing away from you. The GPIO header is the two rows of pins on the top-left. Pin 1 is the corner closest to the SD card slot (tiny triangle on the board). Top row = odd pins (1, 3, 5…), bottom row = even pins (2, 4, 6…), counting left to right.

| Pi physical pin | Pi signal   | Breadboard destination | Why                         |
|-----------------|-------------|------------------------|-----------------------------|
| Pin 3           | GPIO2 (SDA) | j14                    | I2C data line to PCA9685    |
| Pin 5           | GPIO3 (SCL) | j13                    | I2C clock line to PCA9685   |
| Pin 6           | GND         | blue (−) rail          | Shared ground               |

Pin 3 and Pin 5 are the second and third pins in the top row. Pin 6 is directly below Pin 5.

The GPIO18 laser wire (pin 12 → row 50) is left for later, when the laser module is physically attached.

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
