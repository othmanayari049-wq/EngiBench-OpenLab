// EngiBench OpenLab - ESP32 JSON telemetry example

const int ADC_PIN = 34;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
}

void loop() {
  const int raw = analogRead(ADC_PIN);
  const float voltage = raw * (3.3 / 4095.0);

  Serial.print("{\"adc_raw\":");
  Serial.print(raw);
  Serial.print(",\"voltage_V\":");
  Serial.print(voltage, 4);
  Serial.println("}");

  delay(100);
}
