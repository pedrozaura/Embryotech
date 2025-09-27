/*

    Comando para buscar todos os endereços conectados ao barramento I2C

*/



#include <Wire.h>
 
void setup() {
	Wire.begin();
	Serial.begin(9600);
	while (!Serial);
	Serial.println("\nI2C Scanner");
}
 
void loop() {
	byte error, address;
	int nDevices = 0;
	Serial.println("Procurando dispositivos I2C...");
 
	for (address = 1; address < 127; address++) {
		Wire.beginTransmission(address);
		error = Wire.endTransmission();
		if (error == 0) {
			Serial.print("Dispositivo encontrado no endereço 0x");
			if (address < 16) Serial.print("0");
			Serial.println(address, HEX);
			nDevices++;
		}
 
	}
	if (nDevices == 0) {
		Serial.println("Nenhum dispositivo I2C encontrado.");
	} else {
		Serial.println("Varredura concluída.");
	}
	delay(5000);
}