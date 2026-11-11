const int PWM_PIN = PA1;
int value = 0;

void setup() {
  pinMode(PWM_PIN, OUTPUT);

  Serial.begin(115200);
  delay(1000);

  Serial.println("Voltage Control");
  Serial.println("Enter a value from 0 to 255:");
}

void loop() {
  if (Serial.available() > 0) {
    int v = Serial.parseInt();

    if (v >= 0 && v <= 255) {
      value = v;
      analogWrite(PWM_PIN, value);

      float voltage = 3.3 * value / 255.0;

      Serial.print("Value: ");
      Serial.print(value);
      Serial.print(" | Average voltage: ");
      Serial.print(voltage, 2);
      Serial.println(" V");
    } else {
      Serial.println("Error: enter a value from 0 to 255");
    }

    while (Serial.available() > 0) {
      Serial.read();
    }
  }
}