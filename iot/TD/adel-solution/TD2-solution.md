# IoT — TD2 Solution

Statement: [TD2.pdf](../TD2.pdf). The class correction is in [TD2-sol.pdf](../TD2-sol.pdf); this solution also fixes the weak points of that correction (parking sensors, DC motor speed, robotic arm, ADC value).

## Exercise 1 — ESP32 + DHT22 + LED + Wi-Fi

1. Roles
   - ESP32: microcontroller. It reads the sensor, runs the program, decides and drives the LED.
   - DHT22: measures temperature and relative humidity.
   - LED: visual indicator (e.g. ON when temperature is above a threshold).
   - Wi-Fi: sends the measures to a server/cloud/dashboard and receives commands. On the ESP32 the Wi-Fi radio is integrated.

2. Classification

| Component | Class |
| --- | --- |
| DHT22 | Input |
| ESP32 | Processing |
| LED | Output |
| Wi-Fi | Communication |

3. Block diagram

```text
                 power supply (USB / battery)
                            |
 [DHT22] --data (1 GPIO)--> [ESP32] --GPIO + resistor--> [LED]
  input                    processing                    output
                              |
                           Wi-Fi radio
                              |
                     [Router / Gateway] ---> [Cloud / Dashboard]
                          communication   (data up, commands down)
```

## Exercise 2 — Sensors

| Sensor | Measures / detects | Output type |
| --- | --- | --- |
| DHT22 | Temperature and relative humidity | Digital (single-wire serial protocol) |
| LDR | Light intensity (resistance falls when light rises) | Analog (voltage divider → ADC) |
| PIR | Motion of a warm body (infrared change) | Digital (HIGH when motion detected) |
| HC-SR04 | Distance by ultrasonic echo (2 cm – 4 m) | Digital pulse: echo duration ∝ distance (d = t × 340 m/s / 2) |
| MQ-2 | Combustible gas and smoke (LPG, methane, H₂, smoke) | Analog (AO); modules also give a digital threshold output (DO) |

## Exercise 3 — Battery lifetime

1. Average current over one cycle of 60 s (remaining time = 60 − 2 − 3 = 55 s):

```text
I_avg = (10×2 + 20×3 + 0.1×55) / 60
      = (20 + 60 + 5.5) / 60
      = 85.5 / 60
      = 1.425 mA
```

2. Lifetime:

```text
T = 3000 mAh / 1.425 mA ≈ 2105 h
T ≈ 2105 / 24 ≈ 87.7 days  (≈ 3 months)
```

This value is theoretical: self-discharge, temperature, ageing and Wi-Fi current peaks reduce it.

3. Ways to increase lifetime:
   - Use deep-sleep mode between measures (ESP32 deep sleep ≈ 10 µA instead of 0.1 mA).
   - Measure and transmit less often, or only on events (e.g. when the value changes more than a threshold).
   - Shorten active time (faster processing, power off the sensor between measures).
   - Use a low-power radio (BLE, LoRa) instead of Wi-Fi, or a bigger battery / solar panel.

## Exercise 4 — Potentiometer and ADC

1. Analog: it gives a continuous voltage between 0 and 3.3 V.
2. The ADC samples the voltage and converts it into a digital number that the microcontroller can process.
3. 12 bits → 2¹² = **4096** values (0 to 4095).
4. Ideal conversion:

```text
N = V / Vref × (2^12 − 1) = 1.65 / 3.3 × 4095 = 2047.5 ≈ 2048
```

Answer: about **2047–2048** (half scale). With the convention N = V/Vref × 4096, N = 2048. The real ESP32 ADC is not linear near 0 V and 3.3 V, so the measured value can differ.

## Exercise 5 — Topologies

1. Network A: **star**. Network B: **mesh**. Network C: **point-to-point**.
2. The **mesh** topology: if a node or link fails, data takes another path through neighbor nodes.
3. The gateway is a single point of failure: no sensor can send data any more, so the whole network stops (unless sensors store data locally until it comes back). Solution: a redundant gateway.

## Exercise 6 — Connected door lock

1. Hardware: ESP32, RFID reader (e.g. RC522, SPI), RFID cards/tags, electronic lock (solenoid or electromagnetic), relay or MOSFET driver, power supply. Optional: buzzer/LED for feedback, flyback diode.
2. Software functions:
   - Read the card UID from the RFID reader.
   - Authenticate: compare the UID with the list of authorized users (local memory or server).
   - Control the lock: open for a few seconds, then close again.
   - Also useful: log every access attempt, manage users remotely, notify on refused access.
3. Verification: the user presents the card → the reader reads its UID and sends it to the ESP32 → the ESP32 compares the UID with the authorized list → if it matches, the ESP32 activates the relay and the door opens for a limited time, and the event is logged; else access is refused (red LED/buzzer). A UID alone is easy to clone, so a secure system uses encrypted cards or a second factor (PIN).
4. An ESP32 GPIO gives only 3.3 V and a few mA (about 12 mA recommended, 40 mA max). A lock needs 12 V and hundreds of mA, and its coil creates voltage spikes. The relay/driver switches the lock's separate power supply, isolates the microcontroller, and the flyback diode protects it.

## Exercise 7 — Smart parking (20 spaces)

1. Presence sensors per space: ultrasonic HC-SR04 (distance to car), infrared obstacle sensor, magnetometer buried in the ground (detects the car's metal), or one camera with image processing for several spaces. A PIR is not suitable: it detects motion, so a parked car that does not move is not detected.
2. Processing: microcontroller (ESP32) per group of spaces, possibly a gateway (Raspberry Pi) that aggregates data, and a server/cloud that stores states and hosts the dashboard. Communication: Wi-Fi (small lot), LoRaWAN or Zigbee (large lot, battery nodes), MQTT or HTTP to the server.
3. Architecture

```text
[Sensor 1..20] --> [ESP32 nodes] --Wi-Fi/LoRa--> [Gateway] --Internet/MQTT--> [Server + DB] --> [Web dashboard]
    sense             process                     communicate                    store           display
```

4. The dashboard must show the space as **"unknown / sensor fault"** (e.g. grey), not as free or occupied. It should also raise a maintenance alert and keep the last known value with its time. A missing value is not proof that the space is free.
5. Energy reduction: deep sleep between measures, send only when a state changes (event-driven), lower measurement frequency at night, use low-power radio (LoRa, BLE), solar panel for the nodes.

## Exercise 8 — Actuators

| Application | Component | Justification |
| --- | --- | --- |
| Irrigation valve open/close | **Solenoid valve** driven by a relay or MOSFET | Electrically opened/closed valve; it needs more power than a GPIO gives |
| DC motor speed | **PWM + motor driver** (H-bridge L298N or MOSFET) | PWM changes the average voltage, so the speed; the H-bridge also gives direction ("DWM" in the class correction means PWM) |
| Pump ON/OFF | **Relay** (or MOSFET / solid-state relay) | Simple ON/OFF switching of a high-power load with isolation |
| Robotic arm to an angle | **Servomotor** (or stepper motor) | Servo has a position feedback loop: a PWM pulse width gives an exact angle. A simple DC motor cannot hold an angle |
| LED brightness | **PWM** on a GPIO (with resistor; transistor for strong LEDs) | Duty cycle changes average power, so perceived brightness |
