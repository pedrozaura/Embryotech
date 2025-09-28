//Programa: Sensor de temperatura I2C MLX90614 Arduino
//Autor: Arduino e Cia

#include <Wire.h>
#include <Adafruit_MLX90614.h>

Adafruit_MLX90614 mlx = Adafruit_MLX90614();


//Array que desenha o simbolo de grau
byte grau[8] = {B00110, B01001, B01001, B00110,
                B00000, B00000, B00000, B00000,};

double temp_amb;
double temp_obj;

void setup()
{
  Serial.begin(9600);
  Serial.println("Sensor de temperatura MLX90614");

  //Inicializa o MLX90614
  mlx.begin();
}

void loop()
{
  //Leitura da temperatura ambiente e do objeto
  //(para leitura dos valores em Fahrenheit, utilize
  //mlx.readAmbientTempF() e mlx.readObjectTempF() )
  temp_amb = mlx.readAmbientTempC();
  temp_obj = mlx.readObjectTempC();

  //Mostra as informacoes no Serial Monitor
  Serial.print("Ambiente = ");
  Serial.print(temp_amb);
  Serial.print("*CtObjeto = ");
  Serial.print(temp_obj); Serial.println("*C");

  //Aguarda 1 segundo ate nova leitura
  delay(1000);
}