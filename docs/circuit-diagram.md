# Laser Tracker — Circuit Diagram

Diagrams below use **Mermaid**, which GitHub renders as real visual diagrams.
View this file on GitHub (or in any Markdown viewer with Mermaid support) to see
the rendered graphics. If you only see code blocks, your viewer doesn't support
Mermaid — open the file on github.com instead.

All diagrams reflect the **actual current wiring** (post problem 001 — MB102
removed, LM2596 for servo power, Pi GPIO 5V for chip logic, LifeCam USB webcam).

---

## 1. System overview

Everything in one picture — what connects to what.

```mermaid
flowchart TB
    classDef power fill:#ffe4b5,stroke:#d2691e,color:#000,stroke-width:2px
    classDef pi fill:#c8e6c9,stroke:#2e7d32,color:#000,stroke-width:2px
    classDef driver fill:#bbdefb,stroke:#1565c0,color:#000,stroke-width:2px
    classDef servo fill:#f8bbd0,stroke:#ad1457,color:#000,stroke-width:2px
    classDef laser fill:#ffcdd2,stroke:#c62828,color:#000,stroke-width:2px
    classDef camera fill:#d1c4e9,stroke:#4527a0,color:#000,stroke-width:2px
    classDef rail fill:#fff9c4,stroke:#f57f17,color:#000,stroke-width:1px

    PSU12["⚡ 12V 5A PSU<br/>(wall adapter)"]:::power
    USBC["⚡ Pi USB-C adapter<br/>5V 3A"]:::power

    LM2596["LM2596 buck converter<br/>12V → 5V<br/>(up to 3A, set with trimpot)"]:::power

    Pi["Raspberry Pi 4B<br/>(8GB)"]:::pi
    PCA["PCA9685<br/>16-channel PWM driver<br/>I2C address 0x40"]:::driver

    PanServo["DS3225 servo<br/>PAN (channel 0)"]:::servo
    TiltServo["DS3225 servo<br/>TILT (channel 1)"]:::servo

    Cam["Microsoft LifeCam HD-3000<br/>USB webcam (640×480 BGR)"]:::camera

    MOSFET["IRLZ44N<br/>N-channel MOSFET"]:::laser
    Laser["5 mW 650 nm bare diode<br/>(awaiting replacement)"]:::laser

    LogicRail([5V logic rail — from Pi GPIO]):::rail
    ServoRail([5V servo rail — from LM2596]):::rail
    GndRail([GND rail — common]):::rail

    PSU12 -->|"12V"| LM2596
    USBC -->|"5V via USB-C"| Pi

    Pi -->|"GPIO pin 2 (5V)"| LogicRail
    LM2596 -->|"5V (up to 3A)"| ServoRail
    LM2596 -.->|"GND"| GndRail
    Pi -.->|"GPIO pin 6 (GND)"| GndRail

    LogicRail -->|"VCC"| PCA
    ServoRail -->|"V+"| PCA
    GndRail -->|"GND"| PCA

    Pi -->|"GPIO2 / pin 3 — SDA"| PCA
    Pi -->|"GPIO3 / pin 5 — SCL"| PCA

    Pi -->|"GPIO18 / pin 12"| MOSFET
    LogicRail -->|"5V via 100Ω"| Laser
    Laser -->|"laser −"| MOSFET
    MOSFET -.->|"source"| GndRail

    PCA -->|"channel 0 PWM"| PanServo
    PCA -->|"channel 1 PWM"| TiltServo

    Cam -.->|"USB-A"| Pi
```

---

## 2. Power distribution (where each Amp comes from)

Two power domains, both grounded to a common rail.

```mermaid
flowchart LR
    classDef src fill:#ffecb3,stroke:#ff8f00,color:#000,stroke-width:2px
    classDef reg fill:#ffe0b2,stroke:#e65100,color:#000,stroke-width:2px
    classDef rail fill:#fff9c4,stroke:#f57f17,color:#000,stroke-width:1px
    classDef load fill:#c5e1a5,stroke:#558b2f,color:#000
    classDef pi fill:#c8e6c9,stroke:#2e7d32,color:#000,stroke-width:2px

    P12["12V 5A wall PSU<br/>60W total"]:::src
    Pusb["Pi USB-C adapter<br/>5V 3A — 15W"]:::src

    BK["LM2596<br/>12V→5V buck<br/>up to 3A"]:::reg

    PiB["Pi 4B board<br/>~600mA"]:::pi
    PiPin2["Pi GPIO pin 2<br/>(5V tap)"]:::pi

    LR(("5V LOGIC rail<br/>~50mA load")):::rail
    SR(("5V SERVO rail<br/>up to 1A load")):::rail
    GND(("GND<br/>common reference")):::rail

    Vcc["PCA9685 VCC<br/>(chip logic)"]:::load
    Vp["PCA9685 V+<br/>(servo power)"]:::load
    PanS["Pan servo<br/>~500mA"]:::load
    TiltS["Tilt servo<br/>~500mA"]:::load

    P12 ==>|"12V positive"| BK
    P12 -.->|"PSU negative"| GND
    Pusb ==>|"5V USB-C"| PiB

    PiB ==> PiPin2
    PiPin2 ==>|"~50mA tap"| LR
    BK ==>|"5V out (regulated, set with multimeter)"| SR
    BK -.-> GND
    PiB -.->|"GPIO pin 6"| GND

    LR --> Vcc
    SR --> Vp
    Vp --> PanS
    Vp --> TiltS
```

**Why two 5V sources for the same nominal voltage?**
The DS3225 servos draw 600–900mA combined under load and can spike to 2A+
under stall. The LM2596 buck converter handles that off the 12V PSU
without touching the Pi's rail. The PCA9685's chip-logic side (~50mA)
runs off the Pi's GPIO 5V — clean, regulated, already there, and one
fewer power module to configure. Common GND across all three (Pi,
LM2596 OUT−, PCA9685 GND) keeps I2C signals referenced correctly.

(The MB102 module from the original Phase 2 design is no longer in the
circuit — see [problem 001](../problems/001-servo-power.md).)

---

## 3. I2C signal path (Pi ↔ PCA9685)

Just three wires from the Pi to the PCA9685 carry all servo commands.

```mermaid
flowchart LR
    classDef pi fill:#c8e6c9,stroke:#2e7d32,color:#000,stroke-width:2px
    classDef pca fill:#bbdefb,stroke:#1565c0,color:#000,stroke-width:2px

    subgraph PiGPIO["Pi GPIO header"]
        direction TB
        P3["Pin 3 — GPIO2 (SDA)"]:::pi
        P5["Pin 5 — GPIO3 (SCL)"]:::pi
        P6["Pin 6 — GND"]:::pi
    end

    subgraph PCAside["PCA9685 power/signal block"]
        direction TB
        SDA["SDA"]:::pca
        SCL["SCL"]:::pca
        PCAGND["GND"]:::pca
    end

    P3 -->|"data line"| SDA
    P5 -->|"clock line"| SCL
    P6 -.->|"shared reference"| PCAGND
```

**Note:** SDA and SCL only need pull-up resistors if the PCA9685 board doesn't
already have them onboard. Most Adafruit-compatible breakout boards include them —
no external pull-ups needed for this project.

---

## 4. Servo connections (PCA9685 → DS3225)

Each servo plugs into a 3-pin header on the PCA9685. The PCA9685 routes
GND / V+ / Signal automatically per channel.

```mermaid
flowchart LR
    classDef pca fill:#bbdefb,stroke:#1565c0,color:#000
    classDef servo fill:#f8bbd0,stroke:#ad1457,color:#000

    subgraph PCAch["PCA9685 channels"]
        direction TB
        Ch0["Channel 0 header<br/>[GND][V+][PWM signal]"]:::pca
        Ch1["Channel 1 header<br/>[GND][V+][PWM signal]"]:::pca
    end

    PanServo["DS3225 PAN<br/>brown=GND<br/>red=V+<br/>orange=PWM"]:::servo
    TiltServo["DS3225 TILT<br/>brown=GND<br/>red=V+<br/>orange=PWM"]:::servo

    Ch0 ==>|"3-wire plug"| PanServo
    Ch1 ==>|"3-wire plug"| TiltServo
```

**Wire colors on DS3225:**
- Brown = GND
- Red = V+ (5V from PCA9685 V+ rail)
- Orange (or yellow) = PWM signal from PCA9685

Plug orientation matters. The PCA9685 silkscreen shows which pin is GND on each header.

---

## 5. Laser switching circuit (GPIO18 → MOSFET → laser)

The GPIO pin doesn't power the laser directly. It opens/closes a MOSFET
which acts as a switch.

```mermaid
flowchart LR
    classDef pi fill:#c8e6c9,stroke:#2e7d32,color:#000
    classDef res fill:#fff,stroke:#000,color:#000
    classDef mos fill:#ffcdd2,stroke:#c62828,color:#000
    classDef power fill:#ffe0b2,stroke:#e65100,color:#000
    classDef gnd fill:#e0e0e0,stroke:#424242,color:#000

    Pin12["Pi GPIO18<br/>(pin 12)"]:::pi
    R220["220Ω<br/>gate resistor"]:::res
    Gate["MOSFET<br/>GATE (G)"]:::mos
    R100k["100kΩ<br/>pulldown to GND"]:::res
    Drain["MOSFET<br/>DRAIN (D)"]:::mos
    Source["MOSFET<br/>SOURCE (S)"]:::mos
    R100["100Ω<br/>current limiter"]:::res
    Pin4["Pi 5V<br/>(pin 4)"]:::power
    LaserPos["Laser (+, red)"]:::power
    LaserNeg["Laser (−, black)"]:::power
    GND[("GND rail<br/>(Pi pin 14)")]:::gnd

    Pin4 ==>|"5V supply"| R100
    R100 ==> LaserPos
    LaserPos ==>|"forward bias when MOSFET conducts"| LaserNeg
    LaserNeg ==>|"laser current"| Drain
    Source ==>|"current to ground"| GND

    Pin12 -->|"3.3V control signal"| R220
    R220 --> Gate
    Gate -.->|"hold LOW when GPIO floats"| R100k
    R100k -.-> GND
```

**How it works (in plain English):**

1. The 220Ω resistor between GPIO18 and the MOSFET gate limits current into
   the gate if the pin floats — protects the Pi.
2. The 100kΩ resistor between gate and GND **pulls the gate low** whenever
   GPIO18 is not actively driving high. Without this, the gate could float
   to an unknown voltage at boot and the laser could turn on unintentionally.
   Verified working — the laser does not flash at boot.
3. The 100Ω resistor between the 5V rail and the laser anode limits the
   diode's forward current to ~20 mA (conservative for a 5 mW bare diode).
4. When the Pi sets GPIO18 HIGH (3.3V), the gate voltage rises, the MOSFET
   conducts between drain and source, and current flows through the laser
   to GND → laser turns ON.
5. When the Pi sets GPIO18 LOW (0V), the gate is pulled back low by the 100kΩ,
   the MOSFET stops conducting, and the laser turns OFF.

The current diode is dead and awaiting replacement — see
[problem 002](../problems/002-laser-dead.md). The driver path itself is
verified up to the diode terminals.

**IRLZ44N pinout (TO-220 package, flat face toward you, leads down):**

```
       ┌─────────┐
       │  IRLZ44N│
       │  metal  │
       │   tab   │
       └────┬────┘
            │
       ┌────┴────┐
       │ G  D  S │   ← pins, left to right when flat face is toward you
       └─┬──┬──┬─┘
         │  │  │
         G  D  S
         │  │  │
       [220Ω] │  └── to GND rail
         │   │
      GPIO18 │
            └── laser (−)
```

---

## 6. Camera connection (informational)

The camera is a Microsoft LifeCam HD-3000 USB webcam — **not** a CSI Pi
Camera. It plugs into one of the Pi's USB-A ports and is handled by the
in-kernel `uvcvideo` driver. No install or device-tree config needed.

```mermaid
flowchart LR
    classDef cam fill:#d1c4e9,stroke:#4527a0,color:#000,stroke-width:2px
    classDef pi fill:#c8e6c9,stroke:#2e7d32,color:#000,stroke-width:2px

    Cam["LifeCam HD-3000<br/>USB webcam<br/>640×480 BGR via cv2.VideoCapture"]:::cam
    USB["USB-A cable"]
    USBport["USB-A port on Pi"]:::pi
    PiBoard["Raspberry Pi 4B"]:::pi

    Cam ==> USB
    USB ==> USBport
    USBport ==> PiBoard
```

The camera is held rigidly on the tilt plate of the pan-tilt bracket via a
3D-printed mount — when the servos move, the camera's view moves with them.

The Pi 5 CSI camera + 22-pin ribbon on hand is incompatible with the Pi 4's
15-pin CSI slot and stays shelved. `picamera2` / `rpicam-apps` remain
apt-installed but are unused — handy if a compatible CSI camera ever shows up.

---

## 7. Mechanical layout (pan-tilt bracket)

```mermaid
flowchart TB
    classDef base fill:#e0e0e0,stroke:#424242,color:#000
    classDef servo fill:#f8bbd0,stroke:#ad1457,color:#000
    classDef payload fill:#d1c4e9,stroke:#4527a0,color:#000

    Base["Fixed mounting base"]:::base
    Pan["PAN servo (DS3225)<br/>rotates horizontally<br/>= 'left/right'"]:::servo
    TiltPlate["Tilt plate (moves with pan)"]:::base
    Tilt["TILT servo (DS3225)<br/>rotates vertically<br/>= 'up/down'"]:::servo
    Payload["Camera + (future) Laser<br/>(both mounted to top plate)"]:::payload

    Base --> Pan
    Pan --> TiltPlate
    TiltPlate --> Tilt
    Tilt --> Payload
```

The pan servo is at the bottom; it rotates the entire upper assembly left/right.
The tilt servo sits above it and pivots the camera/laser plate up/down.
This is why pan is channel 0 (the "base" axis) and tilt is channel 1.
The camera is mounted now; the laser will join it on the same plate after Phase 6
unblocks (replacement diode) and Phase 7B (laser mount + boresight) is done.

---

## Legend / color key

| Color | Meaning |
|-------|---------|
| 🟧 Orange | Power source or voltage regulator |
| 🟩 Green | Raspberry Pi 4B and its GPIO pins |
| 🟦 Blue | PCA9685 PWM driver |
| 🟪 Purple | Camera |
| 🟥 Red/Pink | Laser circuit and servos |
| 🟨 Yellow | Shared rails (5V or GND) on the breadboard |

| Arrow style | Meaning |
|-------------|---------|
| `==>` thick arrow | High-current power line |
| `-->` regular arrow | Signal or control line |
| `-.->` dashed arrow | Ground or shared reference |

---

## Notes

- **Common ground is critical.** The Pi, LM2596 OUT−, and PCA9685 must all
  share the same GND rail. Without it, I2C will not communicate.
- **The LM2596 must be set to 5.0V before connecting** — see
  [problems/001-servo-power.md](../problems/001-servo-power.md) for procedure.
- The MB102 module from the original Phase 2 design is removed from the
  circuit and no longer wired anywhere.
