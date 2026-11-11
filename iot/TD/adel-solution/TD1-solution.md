# IoT — TD1 Solution

Statement: [TD1.pdf](../TD1.pdf)

## Exercise 1 — Smart light bulb

a) IoT is a network of physical objects with sensors, processing and connectivity that collect data, exchange it over the Internet and act on their environment with little human intervention.

b) Sensor: power/current sensor (measures consumption); optionally a light sensor. Actuator: the LED driver / dimmer that switches the light on/off and changes intensity or color.

c) A connected object only sends data or receives commands over a network. A smart object also processes data locally and takes decisions (e.g. turns off automatically when consumption is abnormal or when nobody is in the room).

d) Four hardware blocks: sensors/actuators, microcontroller (processing + memory), communication module (Wi-Fi, BLE, Zigbee…), power supply (battery or mains).

## Exercise 2 — Video surveillance (500 cameras)

a)
| Characteristic | Example |
| --- | --- |
| Connectivity | Each camera streams video over Ethernet/4G/Wi-Fi to the central platform |
| Identification | Each camera has a unique ID / IP / MAC address |
| Sensing | Image sensor, motion (PIR) sensor, microphone |
| Intelligence | Edge motion detection, face/plate recognition, automatic alerts |
| Heterogeneity | Different camera brands, resolutions, protocols (RTSP, ONVIF) |
| Scalability | The platform must accept new cameras without redesign |
| Autonomy | Cameras record and detect events alone, reboot automatically |
| Security | Encrypted streams, authentication, access control to video |

b) Yes. 500 cameras already produce a large data flow, and the city will add cameras over time. Storage, bandwidth and processing must grow without loss of service.

c) Limited energy (battery capacity, little sun at night/winter) and limited bandwidth/processing (high-resolution video costs a lot of energy to encode and transmit). Other valid answers: memory, storage, cost.

## Exercise 3 — M2M or IoT

a) M2M: point-to-point link between one device and one dedicated server, proprietary network, closed system.

b) IoT (also M2M at device level): data goes through the Internet to an open platform shared by several applications.

c) M2M: direct machine-to-supplier communication for one specific purpose.

d) IoT: data from heterogeneous sensors is combined on a platform to take smart decisions.

## Exercise 4 — Two domains (example answer)

**Smart home — automatic heating.** Temperature and presence sensors in each room send data to a home gateway. The gateway learns the habits of the residents. It heats only occupied rooms and lowers the temperature at night.
- Sensors: temperature, humidity, PIR presence, door/window contact. Actuators: smart thermostat valves.
- Dominant constraint: energy consumption — battery sensors must last years without maintenance.

**Smart agriculture — irrigation.** Soil moisture sensors are spread across the field. A LoRaWAN gateway collects the measures and sends them to the cloud. The system opens valves only where soil is dry, using weather forecasts.
- Sensors: soil moisture, temperature, rain gauge. Actuators: electric valves, pumps.
- Dominant constraint: communication range — fields cover kilometres with no Wi-Fi (hence LoRa/NB-IoT).

## Exercise 5

a) 1. The sensor node measures the temperature and digitizes it. 2. The node sends the packet over radio to a neighbor node; nodes relay it hop by hop (multi-hop routing). 3. The sink node receives the packet and forwards it to the gateway/server.

b)
- IaaS: provider gives virtual infrastructure (VMs, storage, network); user manages OS and apps. Example: AWS EC2.
- PaaS: provider gives a platform to deploy code; user manages only the application. Example: Google App Engine, Heroku.
- SaaS: complete application used through the browser. Example: Gmail, ThingSpeak dashboard.

c)
| V | Meaning | IoT example |
| --- | --- | --- |
| Volume | Huge amount of data | Millions of smart meters reading every 15 min |
| Velocity | Data arrives fast / in real time | Vehicle sensors streaming every millisecond |
| Variety | Many formats | Video, temperature numbers, GPS, logs |
| Veracity | Data quality / reliability | Faulty sensor sending wrong values |
| Value | Useful knowledge extracted | Predictive maintenance from vibration data |

d) An embedded system is a computer system dedicated to one specific task, integrated inside a larger device. Constraints: limited resources (memory, CPU, energy) and real-time constraints (also: low cost, small size, reliability).

e) Hard real-time constraint: missing the deadline causes a catastrophic failure (injury or death), so the response must always arrive within the limit.

## Exercise 6 — Connected wristband

a) Top-down: start from the global system requirements and split them into smaller subsystems down to components. Bottom-up: start from existing components/modules and assemble them into bigger subsystems up to the full system.

b)
- Hardware: heart-rate optical sensor + analog front end (filtering, ADC), BLE radio, encryption accelerator (AES), power management. Reason: speed, low energy, continuous signal processing.
- Software: heart-rate computation algorithm, user interface, communication protocol logic, firmware updates. Reason: flexibility, easy to update and fix.

c) Dedicated hardware encrypts faster and with much less energy than the CPU. It frees the microcontroller for other tasks. It also stores keys in protected memory and resists software attacks better.

## Exercise 7

a)
- Security: weak devices get hacked; consequence: botnets, privacy leaks (e.g. Mirai).
- Interoperability: devices from different vendors cannot talk; consequence: vendor lock-in, isolated systems.
- Energy: batteries die quickly; consequence: high maintenance cost, data loss.
(Also valid: scalability, privacy, data management.)

b) Mirai scanned the Internet for IoT devices (cameras, routers) with open Telnet and tried a list of factory default usernames/passwords. Infected devices joined a botnet that launched huge DDoS attacks (e.g. Dyn DNS, 2016). Simple measure: force users to change default passwords (and disable Telnet).

c)
- Operating time = 3000 mAh / 0.15 mA = **20,000 h**.
- In years: 20,000 / 8,760 ≈ **2.28 years**.
- Comment: this is theoretical. Real life is shorter because of battery self-discharge, temperature effects, and current peaks during radio transmission. Low-power modes are still essential to reach multi-year autonomy.
