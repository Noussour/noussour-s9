#define LED_PIN PC13
void setup() {
  pinMode(LED_PIN, OUTPUT);

  Serial.begin(115200);
  delay(1000);
  Serial.println("STM32F411 started");
}
void loop() {
  digitalWrite(LED_PIN, LOW);
  Serial.println("LED ON");
  delay(500);

  digitalWrite(LED_PIN, HIGH);
  Serial.println("LED OFF");
  delay(500);
}