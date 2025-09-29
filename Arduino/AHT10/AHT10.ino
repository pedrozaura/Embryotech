#include <Wire.h>
#include <Adafruit_AHTX0.h>

Adafruit_AHTX0 aht;

void setup() {
  Serial.begin(9600);
  Serial.println("AHT10 Sensor Test");

  if (!aht.begin()) {
    Serial.println("Failed to find AHT10 sensor!");
    while (1) delay(10);
  }
  Serial.println("AHT10 found and initialized.");
}

void loop() {
  sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);  // Read temperature and humidity

  Serial.print("Temperature: ");
  Serial.print(temp.temperature);
  Serial.println(" °C");

  Serial.print("Humidity: ");
  Serial.print(humidity.relative_humidity);
  Serial.println(" %");

  delay(2000);  // Wait 2 seconds before next reading
}
