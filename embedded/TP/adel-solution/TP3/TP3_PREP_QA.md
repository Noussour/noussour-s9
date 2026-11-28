# TP3 — Interrupts, UART & USB CDC Prep Guide (STM32F411CEUx Black Pill)

## 1. Fixes Applied Compared to `TP3_USB_Captures.pdf`
1. **Removed blocking `HAL_Delay(1000)` in `while (1)`:** Replaced with non-blocking `TIM4` interrupt (`timer_event` flag) so button presses and serial commands respond immediately.
2. **Fixed `TIM4` period math:** `Prescaler = 9599`, `Period = 4999` on a `96 MHz` APB1 timer clock gives `96,000,000 / 9600 / 5000 = 2 Hz` (every **500 ms**). (`Period = 9999` would be 1 s).
3. **Added `volatile` to all ISR-shared variables:** `usb_rx_buf`, `usb_rx_head`, `usb_rx_tail`, `uart_rx_buf`, `uart_rx_head`, `uart_rx_tail`, `button_event`, `timer_event`.
4. **Ignored `'\r'` in RX line parsing:** Prevents trailing `\r` from breaking command matching when terminals send `\r\n`.
5. **Added an event-driven command parser:** Supports `LED ON`, `LED OFF`, `LED TOGGLE`, `BLINK ON`, `BLINK OFF`, `STATUS`, and `HELP` (in addition to echoing `Received: <cmd>`).

---

## 2. Step-by-Step STM32CubeIDE Setup (Both Projects)

### Common Configuration (`STM32F411CEUx`)
* **SYS → Debug:** `Serial Wire` (`PA13` SWDIO, `PA14` SWCLK)
* **RCC → HSE:** `Crystal/Ceramic Resonator` (`25 MHz` on `PH0`/`PH1`)
* **GPIO:**
  * `PC13` → `GPIO_Output`, Label: `LED` (Active Low: `0` = ON, `1` = OFF)
  * `PA0` → `GPIO_EXTI0`, Mode: `External Interrupt Mode with Falling edge trigger detection`, Pull: `Pull-up`, Label: `BUTTON`
* **Timers → TIM4:** Clock Source = `Internal Clock`, `Prescaler = 9599`, `Counter Period = 4999` (500 ms)
* **Clock Configuration:**
  * `HSE = 25 MHz` → `PLLM = /25` (`1 MHz`) → `PLLN = ×192` (`192 MHz` VCO)
  * `PLLP = /2` → **`96 MHz` SYSCLK**
  * `PLLQ = /4` → **`48 MHz` USB**
  * `APB1 Prescaler = /2` (`48 MHz` APB1 peripherals, **`96 MHz` APB1 Timers**)

### Project A: `TP3_USB` (USB CDC Virtual COM Port)
* **Connectivity → `USB_OTG_FS`:** `Device_Only` (`PA11` DM, `PA12` DP)
* **Middleware → `USB_DEVICE`:** `Communication Device Class (Virtual Port Com)`
* **NVIC:** Enable `EXTI0_IRQn`, `TIM4_IRQn`, `OTG_FS_IRQn`
* **Code:** Paste `TP3_USB/USB_DEVICE/App/usbd_cdc_if_snippet.c` into `usbd_cdc_if.c`, and paste `TP3_USB/Core/Src/main.c` `USER CODE` blocks into `main.c`.

### Project B: `TP3_UART` (Hardware `USART1`)
* **Connectivity → `USART1`:** `Asynchronous` (`PA9` TX, `PA10` RX), `115200 Bits/s`, `8N1`
* **NVIC:** Enable `EXTI0_IRQn`, `TIM4_IRQn`, `USART1_IRQn`
* **Code:** Paste `TP3_UART/Core/Src/main.c` `USER CODE` blocks into `main.c`.

---

## 3. Oral Exam Q&A (MX Configuration & Code)

### A. STM32CubeMX (`.ioc`) Questions
1. **Why is `PC13` active low?**
   * On the Black Pill board, the LED anode is wired to 3.3V (via a resistor) and the cathode to `PC13`. Writing `0` (`GPIO_PIN_RESET`) sinks current and turns the LED **ON**; writing `1` (`GPIO_PIN_SET`) turns it **OFF**.
2. **Why `PA0` = `GPIO_PULLUP` + `GPIO_MODE_IT_FALLING`?**
   * The `KEY` button connects `PA0` to `GND` when pressed. Internal pull-up keeps `PA0` at `HIGH` (`1`) when released, so pressing it creates a `HIGH → LOW` **falling edge** that triggers `EXTI0`.
3. **Why `PLLM = 25`, `PLLN = 192`, `PLLP = 2`, `PLLQ = 4`?**
   * `HSE` is `25 MHz`. Dividing by `25` gives `1 MHz` PLL input; multiplying by `192` gives `192 MHz` VCO. Dividing by `PLLP = 2` gives `96 MHz` SYSCLK (max is 100 MHz on F411). Dividing by `PLLQ = 4` gives **`48 MHz`**, which is strictly required by `USB_OTG_FS`.
4. **Why is the `TIM4` timer clock `96 MHz` when `APB1` is `48 MHz`?**
   * On STM32F4, when `APB1 Prescaler != 1` (here `/2`), the hardware automatically multiplies the APB1 timer clock by `2` (`48 MHz × 2 = 96 MHz`).
   * Timer frequency = `96,000,000 / ((9599 + 1) × (4999 + 1)) = 2 Hz` → period = `500 ms`.
5. **Difference between `USART1` and `USB_OTG_FS` CDC?**
   * `USART1` (`PA9`/`PA10`) is hardware UART requiring an external USB-to-UART adapter and matching baud rate (`115200`).
   * `USB_OTG_FS` (`PA11`/`PA12`) emulates a Virtual COM Port directly over the Black Pill's USB-C port using the USB CDC class.

### B. C Code Questions
1. **Why keep ISRs short and use flags (`button_event`, `timer_event`)?**
   * Blocking inside an ISR (e.g., `HAL_Delay()` or `usb_print()`) starves lower/equal priority interrupts (like `SysTick`, which `HAL_GetTick()` depends on). The ISR only records the event; `while (1)` does the slow work (GPIO toggle + USB/UART print).
2. **Why `volatile` on `button_event`, `timer_event`, `*_rx_head`, `*_rx_tail`, `*_rx_buf`?**
   * Prevents compiler optimizations from caching the variable in a CPU register, forcing it to re-read from RAM because an ISR can modify it asynchronously.
3. **How does button debouncing work?**
   * `if ((HAL_GetTick() - last_tick) > 200U)` ignores mechanical switch bounces within 200 ms of the previous valid press.
4. **How does the circular ring buffer work?**
   * Producer (RX callback/ISR) writes at `head`; consumer (`while (1)`) reads at `tail`.
   * **Empty:** `head == tail`.
   * **Full:** `(head + 1) % RX_BUF_SIZE == tail` (1 slot is sacrificed so full is distinguishable from empty).
5. **Why does `CDC_Receive_FS()` call `USBD_CDC_SetRxBuffer()` and `USBD_CDC_ReceivePacket()`?**
   * To re-arm the USB OUT endpoint so the USB peripheral can accept the next incoming packet from the host.
6. **Why does `HAL_UART_RxCpltCallback()` call `HAL_UART_Receive_IT(&huart1, &uart_rx_byte, 1)`?**
   * HAL interrupt reception is one-shot; it must be re-armed after each byte to keep receiving continuously.
7. **Why does `usb_print()` have a `100 ms` timeout on `USBD_BUSY`?**
   * If the host PC is not reading the Virtual COM Port, `CDC_Transmit_FS()` keeps returning `USBD_BUSY`; the timeout prevents the firmware from hanging forever.
