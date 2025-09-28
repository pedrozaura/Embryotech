// Definição dos pinos
const int dirPin = 13;   // Pino direção conectado ao DIR+ do TB6600
const int stepPin = 12;  // Pino passo conectado ao PUL+ do TB6600
const int pinoEnable = 15;

const int tempoVelocidade = 1500; 
const int numeroPassos = 200;

void setup() {
  pinMode(dirPin, OUTPUT);
  pinMode(stepPin, OUTPUT);
  pinMode(pinoEnable, OUTPUT);
  digitalWrite(pinoEnable, HIGH); // estando em HIGH o motor fica livre. 

  digitalWrite(dirPin, LOW);  // Define direção inicial (LOW = sentido 1)
}
 
void loop() {

  // Gira o motor em um sentido por 1000 passos
  digitalWrite(dirPin, HIGH);  // Define direção (HIGH = sentido 2)
  digitalWrite(pinoEnable, LOW); // LOW para ligardo
  for(int i = 0; i < numeroPassos; i++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(tempoVelocidade);     // Controla a velocidade (tempo entre pulsos)
    digitalWrite(stepPin, LOW);
    delayMicroseconds(tempoVelocidade);
  }
  digitalWrite(pinoEnable, HIGH);
  delay(5000); // Pausa de 1 segundo
 
  // Gira o motor no sentido contrário por 1000 passos
  digitalWrite(dirPin, LOW);   // Define direção (LOW = sentido 1)
  digitalWrite(pinoEnable, LOW);
  for(int i = 0; i < numeroPassos; i++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(tempoVelocidade);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(tempoVelocidade);
  }
  digitalWrite(pinoEnable, HIGH);
  delay(5000); // Pausa de 1 segundo
}