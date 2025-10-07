// Pinos dos Fins de Curso
// Torre Direita
#define FIM_CURSO_DIR_SUPERIOR 34 // Marrom
#define FIM_CURSO_DIR_INFERIOR 35 // Cinza

// Torre Esquerda
#define FIM_CURSO_ESQ_SUPERIOR 36 // Roxo
#define FIM_CURSO_ESQ_INFERIOR 39 // Azul

// Mecanismo Central - Indicadores de Andar
#define FIM_CURSO_MECANISMO_MEIO_DIREITA 4    // Verde
#define FIM_CURSO_MECANISMO_MEIO_ESQUERDA 5   // Bege

// Fins de Curso do Motor Central
#define FIM_CURSO_CENTRO_1 18   // Amarelo
#define FIM_CURSO_CENTRO_2 19   // Branco

#define PIN_CENTRO_OVO 23


void configurarFinsDeCorso() {
  // Torre Direita
  pinMode(FIM_CURSO_DIR_SUPERIOR, INPUT);
  pinMode(FIM_CURSO_DIR_INFERIOR, INPUT);
  
  // Torre Esquerda
  pinMode(FIM_CURSO_ESQ_SUPERIOR, INPUT);
  pinMode(FIM_CURSO_ESQ_INFERIOR, INPUT);
  
  // Mecanismo Central
  pinMode(FIM_CURSO_MECANISMO_MEIO_DIREITA, INPUT);
  pinMode(FIM_CURSO_MECANISMO_MEIO_ESQUERDA, INPUT);
  
  // Motor Central
  pinMode(FIM_CURSO_CENTRO_1, INPUT);
  pinMode(FIM_CURSO_CENTRO_2, INPUT);

  pinMode(PIN_CENTRO_OVO, INPUT);
  
  Serial.println("Fins de curso configurados");
}

void setup() {
  Serial.begin(115200);
  delay(1000); // Aguardar inicialização da serial
  
  Serial.println("Iniciando sistema de controle de elevador...");
  
  configurarFinsDeCorso();
  
  Serial.println("Sistema Pronto!");
}   

void loop(){

  //Verificar estado dos fins de curso
  if (digitalRead(FIM_CURSO_DIR_SUPERIOR) == LOW) {  // OK
    Serial.println("Fim de curso direito superior acionado");
  }
  if (digitalRead(FIM_CURSO_DIR_INFERIOR) == LOW) {  // OK
    Serial.println("Fim de curso direito inferior acionado");
  }
  if (digitalRead(FIM_CURSO_ESQ_SUPERIOR) == LOW) {  // OK
    Serial.println("Fim de curso esquerdo superior acionado");
  }
  if (digitalRead(FIM_CURSO_ESQ_INFERIOR) == LOW) {  //ok
    Serial.println("Fim de curso esquerdo inferior acionado");
  }
  if (digitalRead(FIM_CURSO_MECANISMO_MEIO_DIREITA) == LOW) {  //ok
    Serial.println("Fim de curso mecanismo meio direita acionado");
  }
  if (digitalRead(FIM_CURSO_MECANISMO_MEIO_ESQUERDA) == LOW) { //ok
    Serial.println("Fim de curso mecanismo meio esquerda acionado");
  }
  if (digitalRead(FIM_CURSO_CENTRO_1) == LOW) {
    Serial.println("Fim de curso centro 1 acionado");
  }
  if (digitalRead(FIM_CURSO_CENTRO_2) == LOW) {
    Serial.println("Fim de curso centro 2 acionado");
  }

  if (digitalRead(PIN_CENTRO_OVO) == LOW){
    Serial.println("Identificado OVO");
  }

  delay(50); // Atraso para evitar leituras excessivas
}