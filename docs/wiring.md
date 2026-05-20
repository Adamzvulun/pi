# Wiring Reference

## Power architecture

MB102 breadboard power module on the breadboard, fed by a 12V 5A PSU via the DC barrel jack.
Both MB102 jumpers set to 5V. Red rail = +5V, blue rail = GND.
The Pi has its own USB-C power supply and is NOT connected to the MB102 5V rail.

## Built and verified

### MB102 power module
- Input: 12V 5A PSU → DC barrel jack on MB102
- Both voltage selector jumpers: 5V position
- Output polarity confirmed correct (red = +, blue = −)

### PCA9685 PWM driver
- GND → blue (−) rail
- VCC → red (+) rail
- SDA → breadboard row j14 (stub, not yet connected to Pi)
- SCL → breadboard row j13 (stub, not yet connected to Pi)
- Green terminal block wired to red and blue rails (power for servos)

### Servos
- Channel 0: Pan servo (bottom of pan-tilt bracket, left-right motion)
- Channel 1: Tilt servo (top of pan-tilt bracket, up-down motion)
- Both plugged into PCA9685 channels, wire colors match

### Laser driver circuit
```
Pi GPIO18 (pin 12) ──[220Ω]──┬── MOSFET gate  (c50 → c45 area)
                              │
                           [100kΩ]
                              │
                             GND

MOSFET (IRLZ44N):
  Gate   → c45  (via 220Ω from row 50)
  Drain  → c46  (laser − terminal connects here when added)
  Source → c47  (jumper to GND rail)
```
Circuit is built and soldered. Laser module itself is not yet attached (cable length TBD during mounting).

## NOT yet wired (do this with Pi powered off)

These four connections must be made before any I2C or laser code will work.
The first three are needed now. GPIO18 is left until the laser module is physically attached.

| Pi pin | Pi signal   | Breadboard destination | Purpose                          |
|--------|-------------|------------------------|----------------------------------|
| Pin 3  | GPIO2 (SDA) | j14                    | I2C data to PCA9685              |
| Pin 5  | GPIO3 (SCL) | j13                    | I2C clock to PCA9685             |
| Pin 6  | GND         | blue (−) rail          | Common ground                    |
| Pin 12 | GPIO18      | row 50                 | Laser MOSFET gate (add later)    |

To find the right pins: hold the Pi with the USB ports facing away from you. The 40-pin GPIO header is the double row of pins on the top-left. Pin 1 is the corner pin closest to the SD card slot and is marked with a small triangle on the board. Pins are numbered left-to-right, top row first (1, 3, 5 … along the top; 2, 4, 6 … along the bottom).

Pin 3 (SDA) and Pin 5 (SCL) are in the top row, second and third from the left. Pin 6 (GND) is directly below Pin 5 in the bottom row.

## Notes

- Servos are running at 5V (spec allows 4.8–6.8V). This is intentional to save cost.
  Torque will be reduced and brownouts are possible under heavy load — code handles this gracefully.
- DS3225 servo pulse range: 500–2500 µs at 50 Hz. Neutral (center) = 1500 µs.
- PCA9685 I2C address: 0x40 (default, no address bridges soldered).
