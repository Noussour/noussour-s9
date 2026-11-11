#include <Servo.h>

#define ESC_PIN PA0

Servo esc;
int throttle = 1000;

void setup() {
  Serial.begin(115200);

  esc.attach(ESC_PIN, 1000, 2000);

  // Gaz minimum au démarrage
  esc.writeMicroseconds(1000);
  delay(3000);

  Serial.println("Brushless ESC PWM Control");
  Serial.println("Enter throttle: 1000 to 2000");
}

void loop() {
  if (Serial.available() > 0) {
    int value = Serial.parseInt();

    if (value >= 1000 && value <= 2000) {
      throttle = value;
      esc.writeMicroseconds(throttle);

      Serial.print("PWM pulse: ");
      Serial.print(throttle);
      Serial.println(" us");
    } else {
      Serial.println("Invalid value! Use 1000 to 2000.");
    }

    while (Serial.available() > 0) {
      Serial.read();
    }
  }
}