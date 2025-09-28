// Defina o pino ADC que será usado (exemplo: GPIO 34 é somente entrada analógica)
const int analogInPin = 23;   // Pino analógico do ESP32 (ADC1_CH6)

// Variáveis
int sensorValue = 0;          // Valor lido do sensor
int setpoint = 2000;          // Ajuste de acordo com a intensidade de luz desejada (0 a 4095 no ESP32)

void setup() {
  Serial.begin(115200);       // ESP32 geralmente trabalha bem em 115200 bps
}

void loop() {
  // Leitura do ADC (0–4095 por padrão no ESP32 de 12 bits)
  sensorValue = analogRead(analogInPin);

  // Imprime valor bruto do sensor
  Serial.print("Sensor = ");
  Serial.println(sensorValue);

  // Compara com setpoint e envia mensagem pela serial
  if (sensorValue < setpoint) {
    Serial.println(">> Sensor abaixo do limite (LOW)");
  } else {
    Serial.println(">> Sensor acima do limite (HIGH)");
  }

  delay(200);   // Aguarda 200 ms entre leituras
}
