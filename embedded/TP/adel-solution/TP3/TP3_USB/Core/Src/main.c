/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : TP3 - Interrupts & USB CDC Virtual COM Port (STM32F411CEUx)
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "usb_device.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "usbd_cdc_if.h"
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
/* USER CODE END Includes */

/* Private variables ---------------------------------------------------------*/
TIM_HandleTypeDef htim4;

/* USER CODE BEGIN PV */
#define RX_BUF_SIZE 128

static volatile uint8_t usb_rx_buf[RX_BUF_SIZE];
static volatile uint16_t usb_rx_head = 0;
static volatile uint16_t usb_rx_tail = 0;

static volatile bool button_event = false;
static volatile bool timer_event = false;
static bool blink_enabled = true;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_TIM4_Init(void);

/* USER CODE BEGIN PFP */
static void usb_print(const char *s);
static void usb_println(const char *s);
static void handle_command(const char *cmd);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
static void usb_print(const char *s)
{
    uint32_t start = HAL_GetTick();
    while (CDC_Transmit_FS((uint8_t *)s, (uint16_t)strlen(s)) == USBD_BUSY)
    {
        if ((HAL_GetTick() - start) > 100U)
        {
            break; // avoid blocking forever if host is not reading
        }
    }
}

static void usb_println(const char *s)
{
    usb_print(s);
    usb_print("\r\n");
}

/**
  * @brief  Hook called from CDC_Receive_FS() in usbd_cdc_if.c (USB RX interrupt).
  */
void USB_CDC_RxCallback(uint8_t *data, uint32_t len)
{
    for (uint32_t i = 0; i < len; i++)
    {
        uint16_t next = (uint16_t)((usb_rx_head + 1U) % RX_BUF_SIZE);
        if (next != usb_rx_tail) // leave one slot empty to distinguish full vs empty
        {
            usb_rx_buf[usb_rx_head] = data[i];
            usb_rx_head = next;
        }
    }
}

static void handle_command(const char *cmd)
{
    usb_print("Received: ");
    usb_println(cmd);

    if (strcmp(cmd, "LED ON") == 0)
    {
        blink_enabled = false;
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_RESET); // active low
        usb_println("OK: LED ON (blink paused)");
    }
    else if (strcmp(cmd, "LED OFF") == 0)
    {
        blink_enabled = false;
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_SET); // active low
        usb_println("OK: LED OFF (blink paused)");
    }
    else if (strcmp(cmd, "LED TOGGLE") == 0)
    {
        HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
        usb_println("OK: LED TOGGLED");
    }
    else if (strcmp(cmd, "BLINK ON") == 0)
    {
        blink_enabled = true;
        usb_println("OK: BLINK ON (500ms)");
    }
    else if (strcmp(cmd, "BLINK OFF") == 0)
    {
        blink_enabled = false;
        usb_println("OK: BLINK OFF");
    }
    else if (strcmp(cmd, "STATUS") == 0)
    {
        GPIO_PinState pin = HAL_GPIO_ReadPin(LED_GPIO_Port, LED_Pin);
        usb_print("LED=");
        usb_print((pin == GPIO_PIN_RESET) ? "ON" : "OFF");
        usb_print(", BLINK=");
        usb_println(blink_enabled ? "ON" : "OFF");
    }
    else if (strcmp(cmd, "HELP") == 0)
    {
        usb_println("Commands: LED ON | LED OFF | LED TOGGLE | BLINK ON | BLINK OFF | STATUS | HELP");
    }
}
/* USER CODE END 0 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    MX_GPIO_Init();
    MX_USB_DEVICE_Init();
    MX_TIM4_Init();

    /* USER CODE BEGIN 2 */
    HAL_TIM_Base_Start_IT(&htim4);
    /* USER CODE END 2 */

    /* USER CODE BEGIN WHILE */
    char buffer[64];
    uint16_t idx = 0;

    while (1)
    {
        /* USER CODE END WHILE */

        /* USER CODE BEGIN 3 */
        if (button_event)
        {
            button_event = false;
            HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
            usb_println("Button pressed");
        }

        if (timer_event)
        {
            timer_event = false;
            if (blink_enabled)
            {
                HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
            }
        }

        while (usb_rx_tail != usb_rx_head)
        {
            char c = (char)usb_rx_buf[usb_rx_tail];
            usb_rx_tail = (uint16_t)((usb_rx_tail + 1U) % RX_BUF_SIZE);

            if (c == '\r')
            {
                continue; // ignore CR in CRLF terminals
            }

            if (c == '\n')
            {
                if (idx > 0U)
                {
                    buffer[idx] = '\0';
                    handle_command(buffer);
                    idx = 0U;
                }
            }
            else if (idx < (sizeof(buffer) - 1U))
            {
                buffer[idx++] = c;
            }
        }
        /* USER CODE END 3 */
    }
}

void SystemClock_Config(void)
{
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    RCC_OscInitStruct.HSEState = RCC_HSE_ON;
    RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
    RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    RCC_OscInitStruct.PLL.PLLM = 25;
    RCC_OscInitStruct.PLL.PLLN = 192;
    RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2; // 96 MHz SYSCLK
    RCC_OscInitStruct.PLL.PLLQ = 4;             // 48 MHz USB OTG FS
    if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
    {
        Error_Handler();
    }

    RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                                  | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2; // 48 MHz APB1, 96 MHz APB1 Timers
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

    if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_3) != HAL_OK)
    {
        Error_Handler();
    }
}

static void MX_TIM4_Init(void)
{
    TIM_ClockConfigTypeDef sClockSourceConfig = {0};
    TIM_MasterConfigTypeDef sMasterConfig = {0};

    htim4.Instance = TIM4;
    htim4.Init.Prescaler = 9599; // 96 MHz / 9600 = 10 kHz
    htim4.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim4.Init.Period = 4999;    // 10 kHz / 5000 = 2 Hz (every 500 ms)
    htim4.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&htim4) != HAL_OK)
    {
        Error_Handler();
    }
    sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
    if (HAL_TIM_ConfigClockSource(&htim4, &sClockSourceConfig) != HAL_OK)
    {
        Error_Handler();
    }
    sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
    sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
    if (HAL_TIMEx_MasterConfigSynchronization(&htim4, &sMasterConfig) != HAL_OK)
    {
        Error_Handler();
    }
}

static void MX_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOH_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_SET); // active low: start OFF

    GPIO_InitStruct.Pin = LED_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_GPIO_Port, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = BUTTON_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_IT_FALLING;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(BUTTON_GPIO_Port, &GPIO_InitStruct);

    HAL_NVIC_SetPriority(EXTI0_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);
}

/* USER CODE BEGIN 4 */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    static uint32_t last_tick = 0;

    if (GPIO_Pin == BUTTON_Pin)
    {
        uint32_t now = HAL_GetTick();
        if ((now - last_tick) > 200U) // 200 ms debounce
        {
            button_event = true;
            last_tick = now;
        }
    }
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM4)
    {
        timer_event = true;
    }
}
/* USER CODE END 4 */

void Error_Handler(void)
{
    __disable_irq();
    while (1)
    {
    }
}
