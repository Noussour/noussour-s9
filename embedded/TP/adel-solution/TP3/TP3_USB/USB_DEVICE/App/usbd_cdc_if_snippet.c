/*
 * Snippet for USB_DEVICE/App/usbd_cdc_if.c (and usbd_cdc_if.h)
 * Paste these into the CubeMX-generated file inside the USER CODE blocks.
 */

/* 1) Inside USER CODE BEGIN EXPORTED_VARIABLES (around line 251 of usbd_cdc_if.c): */
/* USER CODE BEGIN EXPORTED_VARIABLES */
extern void USB_CDC_RxCallback(uint8_t *data, uint32_t len);
/* USER CODE END EXPORTED_VARIABLES */

/* 2) Inside CDC_Receive_FS() -> USER CODE BEGIN 6 (around line 263 of usbd_cdc_if.c): */
static int8_t CDC_Receive_FS(uint8_t* Buf, uint32_t *Len)
{
  /* USER CODE BEGIN 6 */
  USB_CDC_RxCallback(Buf, *Len);
  USBD_CDC_SetRxBuffer(&hUsbDeviceFS, &Buf[0]);
  USBD_CDC_ReceivePacket(&hUsbDeviceFS);
  return (USBD_OK);
  /* USER CODE END 6 */
}
