// Sistema de Controle de Elevador ESP32
// 3 Motores de Passo com TB6600 + 8 Fins de Curso

// ===== DEFINIÇÃO DOS PINOS =====
// Pinos dos Motores de Passo (TB6600)
// Motor Torre Direita
#define MOTOR_DIR_STEP 25      // Laranja
#define MOTOR_DIR_DIR 26       // Marrom
#define MOTOR_DIR_ENABLE 27    // Verde

// Motor Torre Esquerda
#define MOTOR_ESQ_STEP 32      // Laranja
#define MOTOR_ESQ_DIR 33       // Marrom
#define MOTOR_ESQ_ENABLE 14    // Verde

// Motor Centro
#define MOTOR_CENTRO_STEP 12   // Laranja
#define MOTOR_CENTRO_DIR 13    // Marrom
#define MOTOR_CENTRO_ENABLE 15 // Verde

// Pinos dos Fins de Curso
// Torre Direita
#define FIM_CURSO_DIR_SUPERIOR 34  // Marrom BORNE NRO_1
#define FIM_CURSO_DIR_INFERIOR 35  // Cinza BORNE NRO_2

// Torre Esquerda
#define FIM_CURSO_ESQ_SUPERIOR 36  // Roxo BORNE NRO_3
#define FIM_CURSO_ESQ_INFERIOR 39  // Azul BORNE NRO_4

// Mecanismo Central - Indicadores de Andar
#define FIM_CURSO_MECANISMO_MEIO_DIREITA 4   // Verde BORNE NRO_5
#define FIM_CURSO_MECANISMO_MEIO_ESQUERDA 5  // Bege BORNE NRO_6

// Fins de Curso do Motor Central
#define FIM_CURSO_CENTRO_1 18  // BORNE NRO_7 Amarelo - Posição esquerda
#define FIM_CURSO_CENTRO_2 19  // BORNE NRO_8 Branco - Posição direita

// ===== CONFIGURAÇÕES DO SISTEMA =====
#define VELOCIDADE_MOTOR 1000        // Microsegundos entre pulsos (ajustar conforme necessário)
#define PASSOS_POR_ANDAR 2000      // Número de passos entre andares (ajustar conforme necessário)
#define TEMPO_DEBOUNCE 50          // Tempo de debounce em ms
#define MAX_ANDARES 5              // Número máximo de andares

// ===== VARIÁVEIS GLOBAIS =====
volatile bool fimCursoDirSuperiorAtivado = false;
volatile bool fimCursoDirInferiorAtivado = false;
volatile bool fimCursoEsqSuperiorAtivado = false;
volatile bool fimCursoEsqInferiorAtivado = false;
volatile bool fimCursoMeioDireitaAtivado = false;
volatile bool fimCursoMeioEsquerdaAtivado = false;
volatile bool fimCursoCentro1Ativado = false;
volatile bool fimCursoCentro2Ativado = false;

volatile unsigned long ultimoTempoInterrupcao[8] = {0};
volatile int andarAtual = 0;
volatile int contadorPulsosDireita = 0;
volatile int contadorPulsosEsquerda = 0;

bool sistemaIniciado = false;
bool subindo = true;

// ===== FUNÇÕES DE INTERRUPÇÃO =====
void IRAM_ATTR isrFimCursoDirSuperior() {
    unsigned long tempoAtual = millis();
    if (tempoAtual - ultimoTempoInterrupcao[0] > TEMPO_DEBOUNCE) {
        fimCursoDirSuperiorAtivado = true;
        ultimoTempoInterrupcao[0] = tempoAtual;
    }
}

void IRAM_ATTR isrFimCursoDirInferior() {
    unsigned long tempoAtual = millis();
    if (tempoAtual - ultimoTempoInterrupcao[1] > TEMPO_DEBOUNCE) {
        fimCursoDirInferiorAtivado = true;
        ultimoTempoInterrupcao[1] = tempoAtual;
    }
}

void IRAM_ATTR isrFimCursoEsqSuperior() {
    unsigned long tempoAtual = millis();
    if (tempoAtual - ultimoTempoInterrupcao[2] > TEMPO_DEBOUNCE) {
        fimCursoEsqSuperiorAtivado = true;
        ultimoTempoInterrupcao[2] = tempoAtual;
    }
}

void IRAM_ATTR isrFimCursoEsqInferior() {
    unsigned long tempoAtual = millis();
    if (tempoAtual - ultimoTempoInterrupcao[3] > TEMPO_DEBOUNCE) {
        fimCursoEsqInferiorAtivado = true;
        ultimoTempoInterrupcao[3] = tempoAtual;
    }
}

void IRAM_ATTR isrFimCursoMeioDireita() {
    unsigned long tempoAtual = millis();
    if (tempoAtual - ultimoTempoInterrupcao[4] > TEMPO_DEBOUNCE) {
        fimCursoMeioDireitaAtivado = true;
        contadorPulsosDireita++;
        ultimoTempoInterrupcao[4] = tempoAtual;
    }
}

void IRAM_ATTR isrFimCursoMeioEsquerda() {
    unsigned long tempoAtual = millis();
    if (tempoAtual - ultimoTempoInterrupcao[5] > TEMPO_DEBOUNCE) {
        fimCursoMeioEsquerdaAtivado = true;
        contadorPulsosEsquerda++;
        ultimoTempoInterrupcao[5] = tempoAtual;
    }
}

void IRAM_ATTR isrFimCursoCentro1() {
    unsigned long tempoAtual = millis();
    if (tempoAtual - ultimoTempoInterrupcao[6] > TEMPO_DEBOUNCE) {
        fimCursoCentro1Ativado = true;
        ultimoTempoInterrupcao[6] = tempoAtual;
    }
}

void IRAM_ATTR isrFimCursoCentro2() {
    unsigned long tempoAtual = millis();
    if (tempoAtual - ultimoTempoInterrupcao[7] > TEMPO_DEBOUNCE) {
        fimCursoCentro2Ativado = true;
        ultimoTempoInterrupcao[7] = tempoAtual;
    }
}

// ===== CONFIGURAÇÃO INICIAL =====
void setup() {
    Serial.begin(115200);
    Serial.println("=== Sistema de Elevador Iniciando ===");
    
    // Configurar pinos dos motores como saída
    pinMode(MOTOR_DIR_STEP, OUTPUT);
    pinMode(MOTOR_DIR_DIR, OUTPUT);
    pinMode(MOTOR_DIR_ENABLE, OUTPUT);
    
    pinMode(MOTOR_ESQ_STEP, OUTPUT);
    pinMode(MOTOR_ESQ_DIR, OUTPUT);
    pinMode(MOTOR_ESQ_ENABLE, OUTPUT);
    
    pinMode(MOTOR_CENTRO_STEP, OUTPUT);
    pinMode(MOTOR_CENTRO_DIR, OUTPUT);
    pinMode(MOTOR_CENTRO_ENABLE, OUTPUT);
    
    // Configurar pinos dos fins de curso como entrada com pull-up
    pinMode(FIM_CURSO_DIR_SUPERIOR, INPUT);
    pinMode(FIM_CURSO_DIR_INFERIOR, INPUT);
    pinMode(FIM_CURSO_ESQ_SUPERIOR, INPUT);
    pinMode(FIM_CURSO_ESQ_INFERIOR, INPUT);
    pinMode(FIM_CURSO_MECANISMO_MEIO_DIREITA, INPUT);
    pinMode(FIM_CURSO_MECANISMO_MEIO_ESQUERDA, INPUT);
    pinMode(FIM_CURSO_CENTRO_1, INPUT);
    pinMode(FIM_CURSO_CENTRO_2, INPUT);

    // Configurar interrupções para os fins de curso
    attachInterrupt(digitalPinToInterrupt(FIM_CURSO_DIR_SUPERIOR), isrFimCursoDirSuperior, FALLING);
    attachInterrupt(digitalPinToInterrupt(FIM_CURSO_DIR_INFERIOR), isrFimCursoDirInferior, FALLING);
    attachInterrupt(digitalPinToInterrupt(FIM_CURSO_ESQ_SUPERIOR), isrFimCursoEsqSuperior, FALLING);
    attachInterrupt(digitalPinToInterrupt(FIM_CURSO_ESQ_INFERIOR), isrFimCursoEsqInferior, FALLING);
    attachInterrupt(digitalPinToInterrupt(FIM_CURSO_MECANISMO_MEIO_DIREITA), isrFimCursoMeioDireita, FALLING);
    attachInterrupt(digitalPinToInterrupt(FIM_CURSO_MECANISMO_MEIO_ESQUERDA), isrFimCursoMeioEsquerda, FALLING);
    attachInterrupt(digitalPinToInterrupt(FIM_CURSO_CENTRO_1), isrFimCursoCentro1, FALLING);
    attachInterrupt(digitalPinToInterrupt(FIM_CURSO_CENTRO_2), isrFimCursoCentro2, FALLING);
    
    // Habilitar motores
    digitalWrite(MOTOR_DIR_ENABLE, LOW);  // TB6600 - LOW habilita
    digitalWrite(MOTOR_ESQ_ENABLE, LOW);
    digitalWrite(MOTOR_CENTRO_ENABLE, LOW);
    
    // Executar homing inicial
    Serial.println("Executando HOMING...");
    executarHoming();
    
    Serial.println("Sistema pronto! Iniciando ciclo de leituras...");
    delay(2000);
}

// ===== FUNÇÕES DE CONTROLE DOS MOTORES =====
void moverMotoresSincronizados(int passos, bool direcao) {
    // Define direção dos motores (true = subir, false = descer)
    digitalWrite(MOTOR_DIR_DIR, direcao ? HIGH : LOW);
    digitalWrite(MOTOR_ESQ_DIR, direcao ? HIGH : LOW);
    
    // Move os dois motores em sincronia
    for (int i = 0; i < passos; i++) {
        // Verifica fins de curso de segurança
        if (direcao) {  // Subindo
            if (fimCursoDirSuperiorAtivado || fimCursoEsqSuperiorAtivado) {
                Serial.println("Fim de curso superior atingido!");
                break;
            }
        } else {  // Descendo
            if (fimCursoDirInferiorAtivado || fimCursoEsqInferiorAtivado) {
                Serial.println("Fim de curso inferior atingido!");
                break;
            }
        }
        
        // Pulso simultâneo nos dois motores
        digitalWrite(MOTOR_DIR_STEP, HIGH);
        digitalWrite(MOTOR_ESQ_STEP, HIGH);
        delayMicroseconds(VELOCIDADE_MOTOR);
        
        digitalWrite(MOTOR_DIR_STEP, LOW);
        digitalWrite(MOTOR_ESQ_STEP, LOW);
        delayMicroseconds(VELOCIDADE_MOTOR);
        
        // Verificar equilíbrio a cada 100 passos
        if (i % 100 == 0) {
            verificarEquilibrio();
        }
    }
}

void verificarEquilibrio() {
    // Verifica se os contadores de pulsos estão equilibrados
    int diferenca = abs(contadorPulsosDireita - contadorPulsosEsquerda);
    
    if (diferenca > 1) {
        Serial.print("AVISO: Desbalanceamento detectado! Diferença: ");
        Serial.println(diferenca);
        
        // Corrigir desbalanceamento
        if (contadorPulsosDireita > contadorPulsosEsquerda) {
            // Motor esquerdo precisa compensar
            for (int i = 0; i < diferenca * 50; i++) {  // 50 passos por diferença de pulso
                digitalWrite(MOTOR_ESQ_STEP, HIGH);
                delayMicroseconds(VELOCIDADE_MOTOR);
                digitalWrite(MOTOR_ESQ_STEP, LOW);
                delayMicroseconds(VELOCIDADE_MOTOR);
            }
        } else {
            // Motor direito precisa compensar
            for (int i = 0; i < diferenca * 50; i++) {
                digitalWrite(MOTOR_DIR_STEP, HIGH);
                delayMicroseconds(VELOCIDADE_MOTOR);
                digitalWrite(MOTOR_DIR_STEP, LOW);
                delayMicroseconds(VELOCIDADE_MOTOR);
            }
        }
    }
}

void executarHoming() {
    Serial.println("Iniciando processo de HOMING...");
    
    // Resetar flags
    fimCursoDirInferiorAtivado = false;
    fimCursoEsqInferiorAtivado = false;
    
    // Mover para baixo até atingir os fins de curso inferiores
    digitalWrite(MOTOR_DIR_DIR, LOW);  // Direção para descer
    digitalWrite(MOTOR_ESQ_DIR, LOW);
    
    while (!fimCursoDirInferiorAtivado || !fimCursoEsqInferiorAtivado) {
        // Move motor direito se ainda não chegou ao fim
        if (!fimCursoDirInferiorAtivado) {
            digitalWrite(MOTOR_DIR_STEP, HIGH);
            delayMicroseconds(VELOCIDADE_MOTOR);
            digitalWrite(MOTOR_DIR_STEP, LOW);
        }
        
        // Move motor esquerdo se ainda não chegou ao fim
        if (!fimCursoEsqInferiorAtivado) {
            digitalWrite(MOTOR_ESQ_STEP, HIGH);
            delayMicroseconds(VELOCIDADE_MOTOR);
            digitalWrite(MOTOR_ESQ_STEP, LOW);
        }
        
        delayMicroseconds(VELOCIDADE_MOTOR);
    }
    
    // Resetar contadores
    andarAtual = 0;
    contadorPulsosDireita = 0;
    contadorPulsosEsquerda = 0;
    
    Serial.println("HOMING concluído! Sistema na posição inicial.");
    delay(1000);
}

// ===== FUNÇÃO DO MOTOR CENTRAL =====
void motorCentro() {
    Serial.println("=== Executando função motorCentro() ===");
    Serial.print("Andar atual: ");
    Serial.println(andarAtual);
    
    // Por enquanto, apenas imprime mensagem
    Serial.println("Motor central: Preparando para leitura de sensores...");
    
    // Aqui será adicionado o movimento do motor central posteriormente
    // Por agora, simular uma pausa para leitura
    delay(2000);
    
    Serial.println("Motor central: Operação concluída");
}

void leituraCentral() {
    Serial.println("=== Executando leituraCentral() ===");
    
    // Verificar status dos fins de curso do motor central
    if (fimCursoCentro1Ativado) {
        Serial.println("Fim de curso centro 1 (esquerda) ativado!");
        fimCursoCentro1Ativado = false;  // Resetar flag
    }
    
    if (fimCursoCentro2Ativado) {
        Serial.println("Fim de curso centro 2 (direita) ativado!");
        fimCursoCentro2Ativado = false;  // Resetar flag
    }
    
    // Executar função do motor central
    motorCentro();
}

// ===== FUNÇÃO PRINCIPAL DE LEITURA =====
void iniciarLeituras() {
    Serial.println("\n=== INICIANDO CICLO DE LEITURAS ===");
    
    // Resetar flags de andares
    fimCursoMeioDireitaAtivado = false;
    fimCursoMeioEsquerdaAtivado = false;
    
    // Subir até o topo
    Serial.println("Subindo...");
    subindo = true;
    
    while (!fimCursoDirSuperiorAtivado && !fimCursoEsqSuperiorAtivado) {
        // Mover um pequeno número de passos
        moverMotoresSincronizados(100, true);
        
        // Verificar se passou por um andar
        if (fimCursoMeioDireitaAtivado || fimCursoMeioEsquerdaAtivado) {
            andarAtual++;
            Serial.print("\n>>> Andar ");
            Serial.print(andarAtual);
            Serial.println(" detectado!");
            
            // Parar motores
            delay(500);
            
            // Executar leitura central
            leituraCentral();
            
            // Resetar flags
            fimCursoMeioDireitaAtivado = false;
            fimCursoMeioEsquerdaAtivado = false;
            
            delay(500);
        }
    }
    
    Serial.println("\n>>> TOPO ATINGIDO! <<<");
    delay(2000);
    
    // Resetar flags
    fimCursoDirSuperiorAtivado = false;
    fimCursoEsqSuperiorAtivado = false;
    fimCursoMeioDireitaAtivado = false;
    fimCursoMeioEsquerdaAtivado = false;
    
    // Descer até a base
    Serial.println("\nDescendo para a base...");
    subindo = false;
    
    while (!fimCursoDirInferiorAtivado && !fimCursoEsqInferiorAtivado) {
        // Mover um pequeno número de passos
        moverMotoresSincronizados(100, false);
        
        // Verificar se passou por um andar
        if (fimCursoMeioDireitaAtivado || fimCursoMeioEsquerdaAtivado) {
            andarAtual--;
            Serial.print("\n>>> Andar ");
            Serial.print(andarAtual);
            Serial.println(" detectado (descendo)!");
            
            // Parar motores
            delay(500);
            
            // Executar leitura central
            leituraCentral();
            
            // Resetar flags
            fimCursoMeioDireitaAtivado = false;
            fimCursoMeioEsquerdaAtivado = false;
            
            delay(500);
        }
    }
    
    Serial.println("\n>>> BASE ATINGIDA! <<<");
    andarAtual = 0;
    
    // Resetar contadores para manter equilíbrio
    contadorPulsosDireita = 0;
    contadorPulsosEsquerda = 0;
    
    // Resetar flags
    fimCursoDirInferiorAtivado = false;
    fimCursoEsqInferiorAtivado = false;
    
    delay(2000);
}

// ===== LOOP PRINCIPAL =====
void loop() {
    // Executar ciclo completo de leituras
    iniciarLeituras();
    
    Serial.println("\n=== CICLO COMPLETO! Reiniciando... ===\n");
    delay(3000);
}

// ===== FUNÇÕES AUXILIARES DE DEBUG =====
void imprimirStatusSistema() {
    Serial.println("\n--- Status do Sistema ---");
    Serial.print("Andar atual: ");
    Serial.println(andarAtual);
    Serial.print("Pulsos Direita: ");
    Serial.println(contadorPulsosDireita);
    Serial.print("Pulsos Esquerda: ");
    Serial.println(contadorPulsosEsquerda);
    Serial.print("Direção: ");
    Serial.println(subindo ? "SUBINDO" : "DESCENDO");
    
    // Status dos fins de curso
    Serial.println("Fins de Curso:");
    Serial.print("  Dir Superior: ");
    Serial.println(digitalRead(FIM_CURSO_DIR_SUPERIOR) ? "OFF" : "ON");
    Serial.print("  Dir Inferior: ");
    Serial.println(digitalRead(FIM_CURSO_DIR_INFERIOR) ? "OFF" : "ON");
    Serial.print("  Esq Superior: ");
    Serial.println(digitalRead(FIM_CURSO_ESQ_SUPERIOR) ? "OFF" : "ON");
    Serial.print("  Esq Inferior: ");
    Serial.println(digitalRead(FIM_CURSO_ESQ_INFERIOR) ? "OFF" : "ON");
    Serial.println("-------------------------\n");
}