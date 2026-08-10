// EngiBench OpenLab - Arduino JSON telemetry example
// Sends three named channels at 10 Hz using only the Arduino core.

void setup() {
  Serial.begin(115200);
}

void loop() {
  const float t = millis() / 1000.0;
  const float sensor = analogRead(A0);
  const float voltage = sensor * (5.0 / 1023.0);

  Serial.print("{\"analog_raw\":");
  Serial.print(sensor, 0);
  Serial.print(",\"voltage_V\":");
  Serial.print(voltage, 3);
  Serial.print(",\"time_s\":");
  Serial.print(t, 3);
  Serial.println("}");

  delay(100);
}
