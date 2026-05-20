# Laser Tracker

An autonomous laser tracking system running on a Raspberry Pi 4B. A camera detects a target, computes its pixel coordinates, and drives two servos (pan and tilt) via PID control to keep the target centered. On user confirmation, a 5mW laser fires at the target.

This is Adam's school final project.

## Hardware

| Component | Details |
|---|---|
| Raspberry Pi 4B (8GB) | Hostname: `LaserPi`, user: `adam` |
| Camera | Pi Camera 5MP (OV5647 MF, 220° wide-angle) |
| Servos | 2× DS3225 digital servo, 270°, 25kg·cm |
| PWM driver | PCA9685 16-channel, I2C address 0x40 |
| Power | MB102 breadboard module + 12V 5A PSU |
| Laser driver | IRLZ44N MOSFET + 220Ω + 100kΩ resistors |
| Laser | 5mW 650nm red laser, cross pattern, 3V |

## Setup

See [docs/setup-pi.md](docs/setup-pi.md) for full step-by-step Pi setup instructions: creating the venv, installing libraries, wiring the Pi to the breadboard, and confirming the PCA9685 is detected.

## How to run

SSH to the Pi, then:

```bash
source venv/bin/activate
python3 main.py
```

The auto-pull cron job keeps the Pi's code in sync with GitHub — just push from the laptop and wait up to 60 seconds.
