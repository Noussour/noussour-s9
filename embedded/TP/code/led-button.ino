#define LED_PIN PC13
#define BUTTON_PIN PA0
bool ledState = false;
bool lastButtonState = HIGH;
void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  digitalWrite(LED_PIN, LOW);  // LED ON
  Serial.begin(115200);
  delay(1000);
  Serial.println("STM32F411 started");
  Serial.println("Press the button to toggle the LED");
}
void loop() {
  bool buttonState = digitalRead(BUTTON_PIN);
  if (lastButtonState == HIGH && buttonState == LOW) {
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState ? LOW : HIGH);
    if (ledState) {
      Serial.println("LED ON");
    } else {
      Serial.println("LED OFF");
    }
    delay(200);  // Simple debounce
  }
  lastButtonState = buttonState;
}