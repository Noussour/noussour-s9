#define LED_PIN PC13

int delayTime = 500;

void setup() {
  pinMode(LED_PIN, OUTPUT);

  Serial.begin(115200);
  delay(1000);

  Serial.println("STM32F411 started");
  Serial.println("Enter delay in milliseconds:");
}

void loop() {
  if (Serial.available() > 0) {
    int value = Serial.parseInt();

    if (value > 0) {
      delayTime = value;
      Serial.print("New delay: ");
      Serial.print(delayTime);
      Serial.println(" ms");
    }

    while (Serial.available() > 0) {
      Serial.read();
    }
  }

  digitalWrite(LED_PIN, LOW);
  Serial.println("LED ON");
  delay(delayTime);

  digitalWrite(LED_PIN, HIGH);
  Serial.println("LED OFF");
  delay(delayTime);
}