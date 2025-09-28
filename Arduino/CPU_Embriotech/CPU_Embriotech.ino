// Código para ESP32 - Sistema de Elevador com 3 Motores de Passo
// Compatível com Arduino IDE

// ========== DEFINIÇÃO DE PINOS ==========

// Pinos dos Motores de Passo (TB6600)
// Motor Torre Direita
#define MOTOR_DIR_STEP 25   // Laranja
#define MOTOR_DIR_DIR 26    // Marrom
#define MOTOR_DIR_ENABLE 27 // Verde

// Motor Torre Esquerda
#define MOTOR_ESQ_STEP 32   // Laranja
#define MOTOR_ESQ_DIR 33    // Marrom
#define MOTOR_ESQ_ENABLE 14 // Verde

// Motor Centro
#define MOTOR_CENTRO_STEP 12    // Laranja
#define MOTOR_CENTRO_DIR 13     // Marrom
#define MOTOR_CENTRO_ENABLE 15  // Verde

// Pinos dos Fins de Curso
// Torre Direita
#define FIM_CURSO_DIR_SUPERIOR 34 // Marrom  BORNE NRO_1
#define FIM_CURSO_DIR_INFERIOR 35 // Cinza   BORNE NRO_2

// Torre Esquerda
#define FIM_CURSO_ESQ_SUPERIOR 36 // Roxo BORNE NRO_3
#define FIM_CURSO_ESQ_INFERIOR 39 // Azul BORNE NRO_4

// Mecanismo Central - Indicadores de Andar
#define FIM_CURSO_MECANISMO_MEIO_DIREITA 4    // Verde BORNE NRO_5
#define FIM_CURSO_MECANISMO_MEIO_ESQUERDA 5   // Bege BORNE NRO_6

// Fins de Curso do Motor Central
#define FIM_CURSO_CENTRO_1 18   // BORNE NRO_7 Amarelo Controle motor centro Posição esquerda
#define FIM_CURSO_CENTRO_2 19   // BORNE NRO_8 Branco Controle motor centro Posição direita

// GPIOs 16 e 17 agora estão livres para comunicação serial
// Exemplo de uso: Serial2.begin(115200, SERIAL_8N1, 16, 17); // RX=16, TX=17

#define pinoSensorParada 23
#define pinoLDR 2



// ========== CONFIGURAÇÕES DO SISTEMA ==========

// Velocidades dos motores (microsegundos entre passos)
#define VELOCIDADE_NORMAL 1000
#define VELOCIDADE_AJUSTE 2000
#define VELOCIDADE_LENTA 3000

// Configurações de passos
#define PASSOS_POR_ANDAR 2000  // Ajuste conforme necessário
#define PASSOS_AJUSTE_FINO 50   // Para correções de equilíbrio

// ========== VARIÁVEIS GLOBAIS ==========

// Estados do sistema
enum EstadoSistema {
  PARADO,
  SUBINDO,
  DESCENDO,
  AJUSTANDO_EQUILIBRIO,
  EXECUTANDO_MOTOR_CENTRO
};

EstadoSistema estadoAtual = PARADO;

// Contadores e flags
int andarAtual = 0;
int totalAndares = 0;
bool direcaoMovimento = true; // true = subindo, false = descendo
unsigned long contadorPassosDireita = 0;
unsigned long contadorPassosEsquerda = 0;
bool equilibrioOK = true;

// Variáveis de controle dos fins de curso
bool ultimoEstadoMeioDireita = false;
bool ultimoEstadoMeioEsquerda = false;

// ========== FUNÇÕES DE CONFIGURAÇÃO ==========

void setup() {
  Serial.begin(115200);
  Serial.println("Iniciando Sistema de Controle do Elevador");
  
  // Configurar Serial2 nas GPIOs liberadas (se necessário)
  // Serial2.begin(115200, SERIAL_8N1, 16, 17); // RX=GPIO16, TX=GPIO17
  
  // Configurar pinos dos motores como saída
  configurarMotores();
  
  // Configurar pinos dos fins de curso como entrada com pullup
  configurarFinsDeCorso();
  
  // Desabilitar todos os motores inicialmente
  desabilitarTodosMotores();
  
  // Realizar homing (ir para posição inicial)
  realizarHoming();
  
  Serial.println("Sistema Pronto!");
}

void configurarMotores() {
  // Torre Direita
  pinMode(MOTOR_DIR_STEP, OUTPUT);
  pinMode(MOTOR_DIR_DIR, OUTPUT);
  pinMode(MOTOR_DIR_ENABLE, OUTPUT);
  
  // Torre Esquerda
  pinMode(MOTOR_ESQ_STEP, OUTPUT);
  pinMode(MOTOR_ESQ_DIR, OUTPUT);
  pinMode(MOTOR_ESQ_ENABLE, OUTPUT);
  
  // Motor Centro
  pinMode(MOTOR_CENTRO_STEP, OUTPUT);
  pinMode(MOTOR_CENTRO_DIR, OUTPUT);
  pinMode(MOTOR_CENTRO_ENABLE, OUTPUT);
  
  Serial.println("Motores configurados");
}

void configurarFinsDeCorso() {
  // Torre Direita
  pinMode(FIM_CURSO_DIR_SUPERIOR, INPUT_PULLUP);
  pinMode(FIM_CURSO_DIR_INFERIOR, INPUT_PULLUP);
  
  // Torre Esquerda
  pinMode(FIM_CURSO_ESQ_SUPERIOR, INPUT_PULLUP);
  pinMode(FIM_CURSO_ESQ_INFERIOR, INPUT_PULLUP);
  
  // Mecanismo Central
  pinMode(FIM_CURSO_MECANISMO_MEIO_DIREITA, INPUT_PULLUP);
  pinMode(FIM_CURSO_MECANISMO_MEIO_ESQUERDA, INPUT_PULLUP);
  
  // Motor Central
  pinMode(FIM_CURSO_CENTRO_1, INPUT_PULLUP);
  pinMode(FIM_CURSO_CENTRO_2, INPUT_PULLUP);
  
  Serial.println("Fins de curso configurados");
}

// ========== FUNÇÕES DE CONTROLE DOS MOTORES ==========

void habilitarMotor(int pinoEnable) {
  digitalWrite(pinoEnable, LOW); // TB6600 habilita com LOW
}

void desabilitarMotor(int pinoEnable) {
  digitalWrite(pinoEnable, HIGH); // TB6600 desabilita com HIGH
}

void desabilitarTodosMotores() {
  desabilitarMotor(MOTOR_DIR_ENABLE);
  desabilitarMotor(MOTOR_ESQ_ENABLE);
  desabilitarMotor(MOTOR_CENTRO_ENABLE);
}

void darPasso(int pinoStep, int velocidade) {
  digitalWrite(pinoStep, HIGH);
  delayMicroseconds(velocidade / 2);
  digitalWrite(pinoStep, LOW);
  delayMicroseconds(velocidade / 2);
}

void setDirecaoMotor(int pinoDir, bool direcao) {
  digitalWrite(pinoDir, direcao ? HIGH : LOW);
}

// ========== FUNÇÕES DE MOVIMENTO SINCRONIZADO ==========

void moverTorresSincronizadas(bool direcao, int passos) {
  Serial.print("Movendo torres - Direção: ");
  Serial.println(direcao ? "SUBINDO" : "DESCENDO");
  
  // Habilitar motores das torres
  habilitarMotor(MOTOR_DIR_ENABLE);
  habilitarMotor(MOTOR_ESQ_ENABLE);
  
  // Definir direção
  setDirecaoMotor(MOTOR_DIR_DIR, direcao);
  setDirecaoMotor(MOTOR_ESQ_DIR, direcao);
  
  // Mover ambos os motores sincronizadamente
  for (int i = 0; i < passos; i++) {
    // Verificar fins de curso de segurança
    if (verificarLimitesSeguranca(direcao)) {
      Serial.println("Limite de segurança atingido!");
      break;
    }
    
    // Dar passo em ambos os motores
    darPasso(MOTOR_DIR_STEP, VELOCIDADE_NORMAL);
    darPasso(MOTOR_ESQ_STEP, VELOCIDADE_NORMAL);
    
    // Atualizar contadores
    if (direcao) {
      contadorPassosDireita++;
      contadorPassosEsquerda++;
    } else {
      contadorPassosDireita--;
      contadorPassosEsquerda--;
    }
    
    // Verificar se passou por um andar
    verificarPassagemAndar();
    
    // Verificar e corrigir equilíbrio a cada X passos
    if (i % 100 == 0) {
      verificarEquilibrio();
    }
  }
  
  // Desabilitar motores
  desabilitarMotor(MOTOR_DIR_ENABLE);
  desabilitarMotor(MOTOR_ESQ_ENABLE);
}

bool verificarLimitesSeguranca(bool direcao) {
  if (direcao) { // Subindo
    if (digitalRead(FIM_CURSO_DIR_SUPERIOR) == LOW || 
        digitalRead(FIM_CURSO_ESQ_SUPERIOR) == LOW) {
      return true;
    }
  } else { // Descendo
    if (digitalRead(FIM_CURSO_DIR_INFERIOR) == LOW || 
        digitalRead(FIM_CURSO_ESQ_INFERIOR) == LOW) {
      return true;
    }
  }
  return false;
}

void verificarPassagemAndar() {
  bool estadoAtualDireita = digitalRead(FIM_CURSO_MECANISMO_MEIO_DIREITA) == LOW;
  bool estadoAtualEsquerda = digitalRead(FIM_CURSO_MECANISMO_MEIO_ESQUERDA) == LOW;
  
  // Detectar mudança de estado (borda)
  if (estadoAtualDireita && !ultimoEstadoMeioDireita) {
    Serial.println("Passou por andar - Sensor Direita");
    if (direcaoMovimento) andarAtual++;
    else andarAtual--;
    pararEmAndar();
  }
  
  if (estadoAtualEsquerda && !ultimoEstadoMeioEsquerda) {
    Serial.println("Passou por andar - Sensor Esquerda");
    // Usar para verificação de equilíbrio
  }
  
  ultimoEstadoMeioDireita = estadoAtualDireita;
  ultimoEstadoMeioEsquerda = estadoAtualEsquerda;
}

void pararEmAndar() {
  Serial.print("Parando no andar: ");
  Serial.println(andarAtual);
  
  // Desabilitar motores das torres
  desabilitarTodosMotores();
  
  // Aguardar estabilização
  delay(500);
  
  // Executar função do motor central
  executarMotorCentro();
  
  // Aguardar antes de continuar
  delay(1000);
}

// ========== FUNÇÃO DO MOTOR CENTRAL ==========

void executarMotorCentro() {
  estadoAtual = EXECUTANDO_MOTOR_CENTRO;
  
  Serial.println("=====================================");
  Serial.println("EXECUTANDO MOTOR CENTRAL");
  Serial.print("Andar atual: ");
  Serial.println(andarAtual);
  Serial.println("Aqui será executado o movimento do motor central");
  Serial.println("E a leitura dos sensores será feita");
  Serial.println("=====================================");
  
  // TODO: Implementar movimento real do motor central
  // Por enquanto, apenas imprime mensagem conforme solicitado
  
  // Simulação de tempo de execução
  delay(2000);
  
  estadoAtual = direcaoMovimento ? SUBINDO : DESCENDO;
}

// ========== FUNÇÕES DE EQUILÍBRIO ==========

void verificarEquilibrio() {
  // Comparar os contadores de passos
  long diferenca = abs((long)contadorPassosDireita - (long)contadorPassosEsquerda);
  
  if (diferenca > PASSOS_AJUSTE_FINO) {
    Serial.print("Desequilíbrio detectado! Diferença: ");
    Serial.println(diferenca);
    ajustarEquilibrio();
  }
}

void ajustarEquilibrio() {
  estadoAtual = AJUSTANDO_EQUILIBRIO;
  
  Serial.println("Ajustando equilíbrio...");
  
  if (contadorPassosDireita > contadorPassosEsquerda) {
    // Motor esquerdo precisa compensar
    habilitarMotor(MOTOR_ESQ_ENABLE);
    setDirecaoMotor(MOTOR_ESQ_DIR, direcaoMovimento);
    
    while (contadorPassosEsquerda < contadorPassosDireita) {
      darPasso(MOTOR_ESQ_STEP, VELOCIDADE_AJUSTE);
      contadorPassosEsquerda++;
    }
    
    desabilitarMotor(MOTOR_ESQ_ENABLE);
  } else if (contadorPassosEsquerda > contadorPassosDireita) {
    // Motor direito precisa compensar
    habilitarMotor(MOTOR_DIR_ENABLE);
    setDirecaoMotor(MOTOR_DIR_DIR, direcaoMovimento);
    
    while (contadorPassosDireita < contadorPassosEsquerda) {
      darPasso(MOTOR_DIR_STEP, VELOCIDADE_AJUSTE);
      contadorPassosDireita++;
    }
    
    desabilitarMotor(MOTOR_DIR_ENABLE);
  }
  
  Serial.println("Equilíbrio ajustado!");
  estadoAtual = direcaoMovimento ? SUBINDO : DESCENDO;
}

// ========== FUNÇÃO DE HOMING ==========

void realizarHoming() {
  Serial.println("Iniciando processo de HOMING...");
  
  // Descer até encontrar os fins de curso inferiores
  habilitarMotor(MOTOR_DIR_ENABLE);
  habilitarMotor(MOTOR_ESQ_ENABLE);
  
  setDirecaoMotor(MOTOR_DIR_DIR, false); // Descendo
  setDirecaoMotor(MOTOR_ESQ_DIR, false);
  
  // Mover até ambos os fins de curso serem acionados
  while (digitalRead(FIM_CURSO_DIR_INFERIOR) == HIGH || 
         digitalRead(FIM_CURSO_ESQ_INFERIOR) == HIGH) {
    
    if (digitalRead(FIM_CURSO_DIR_INFERIOR) == HIGH) {
      darPasso(MOTOR_DIR_STEP, VELOCIDADE_LENTA);
    }
    
    if (digitalRead(FIM_CURSO_ESQ_INFERIOR) == HIGH) {
      darPasso(MOTOR_ESQ_STEP, VELOCIDADE_LENTA);
    }
    
    delay(1);
  }
  
  // Resetar contadores
  contadorPassosDireita = 0;
  contadorPassosEsquerda = 0;
  andarAtual = 0;
  
  desabilitarTodosMotores();
  
  Serial.println("HOMING concluído! Sistema na posição inicial.");
  delay(1000);
}

// ========== LOOP PRINCIPAL ==========

void loop() {
  // Verificar se está no limite superior
  if (digitalRead(FIM_CURSO_DIR_SUPERIOR) == LOW || 
      digitalRead(FIM_CURSO_ESQ_SUPERIOR) == LOW) {
    Serial.println("Limite superior atingido - Invertendo direção");
    direcaoMovimento = false; // Mudar para descer
    delay(1000);
  }
  
  // Verificar se está no limite inferior
  if (digitalRead(FIM_CURSO_DIR_INFERIOR) == LOW || 
      digitalRead(FIM_CURSO_ESQ_INFERIOR) == LOW) {
    Serial.println("Limite inferior atingido - Invertendo direção");
    direcaoMovimento = true; // Mudar para subir
    delay(1000);
  }
  
  // Executar movimento contínuo
  if (estadoAtual != EXECUTANDO_MOTOR_CENTRO) {
    estadoAtual = direcaoMovimento ? SUBINDO : DESCENDO;
    moverTorresSincronizadas(direcaoMovimento, 10); // Mover 10 passos por vez
  }
  
  // Pequeno delay para não sobrecarregar o processador
  delay(1);
}