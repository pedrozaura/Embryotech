// Código para ESP32 - Sistema de Elevador com 3 Motores de Passo
// Compatível com Arduino IDE



// ========== CONFIGURAÇÕES DO SISTEMA ==========

// Velocidades dos motores (microsegundos entre passos)
#define VELOCIDADE_NORMAL 1000
#define VELOCIDADE_AJUSTE 2000
#define VELOCIDADE_LENTA 3000

// Configurações de passos
#define PASSOS_POR_ANDAR 2000  // Ajuste conforme necessário
#define PASSOS_AJUSTE_FINO 50   // Para correções de equilíbrio


// ========== BIBLIOTECAS ==========
// Bibliotecas Sensores e Atuadores 

#include "config.h"

// ========== OBJETOS DOS SENSORES ==========
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
Adafruit_BMP280 bmp; // I2C
Adafruit_AHTX0 aht;

// Criando o Objeto para o display
LCM Lcm(Serial2); // RX=16, TX=17

// ========== VARIÁVEIS GLOBAIS ==========

// Estados do sistema
enum EstadoSistema {
  PARADO,
  SUBINDO,
  DESCENDO,
  AJUSTANDO_EQUILIBRIO,
  EXECUTANDO_MOTOR_CENTRO
};

// Status de conexão
enum ConnectionStatus {
  DISCONNECTED,
  CONNECTING_WIFI,
  CONNECTING_WEBSOCKET,
  CONNECTED,
  ERROR_STATE
};
ConnectionStatus currentStatus = DISCONNECTED;

// Configurações Wi-Fi e WebServer
struct Config {
  char ssid[32];
  char password[64];
};
Config config;

// ==================== ESTRUTURA DE DADOS ====================
struct SensorData {
  float temperatura;
  float umidade;
  float pressao;
  bool valida;
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

char loteOvos[20] = "";
char dataInicialLote[20] = "";
char dataFinalLote[20] = "";

const int picIdIntro(0); // Coloca o numero da tela Inicial, função para qual quando reiniciar o display essa vai enviar para tela inicial da apresentação do display.
const int picIdMain(153); // leva o numero da tela Principal.

String statusBMP = "";
String statusMLX = "";
String statusSR2 = "";

float temperaturaMLX = 0.0;
float temperaturaBMP = 0.0;
float pressaoBMP = 0.0;
float altitudeBMP = 0.0;
int luminosidadeLDR = 0;

String jwt_token = "";
unsigned long last_token_time = 0;
const unsigned long token_lifetime = 3300000; // 55 minutos (token expira em 1h)
const unsigned long reading_interval = 30000; // 30 segundos entre leituras
unsigned long last_reading_time = 0;

// ==================== CONFIGURAÇÕES NTP ====================
const char* ntp_server = "pool.ntp.org";
const long gmt_offset_sec = -3 * 3600; // GMT-3 (Brasil)
const int daylight_offset_sec = 0;

unsigned long last_ntp_attempt = 0;
const unsigned long ntp_retry_interval = 300000; // Tentar NTP novamente a cada 5 minutos
bool ntp_synchronized = false;

// Inicializando a biblioteca HTTPClient
HTTPClient http;

// Criar instância do servidor na porta 80
WebServer server(80);

// ========== FUNÇÕES DE CONFIGURAÇÃO ==========
// ==================== COLETA DE DADOS DOS SENSORES ====================
SensorData coletar_dados_sensores() {
  SensorData dados;
  dados.valida = false;
  
  sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);  // Read temperature and humidity

  Serial.println("Coletando dados dos sensores...");
  
  // Ler DHT22 (temperatura e umidade)
  dados.temperatura = mlx.readObjectTempC();  //Carrega temperatura do Ovo, sensor MLX90614
  dados.umidade = humidity.relative_humidity; //Carrega a umidade do AHT10. umidade ambiente
  
  // Ler BMP280 (pressão)
  dados.pressao = bmp.readPressure() / 100.0F; // Converter para hPa carrega os dados de pressao ambiente. 
  
  // Verificar se as leituras são válidas
  if (isnan(dados.temperatura) || isnan(dados.umidade)) {
    Serial.println("Erro: Falha na leitura do sensor Temperatura/Umidade");
    return dados;
  }
  
  if (isnan(dados.pressao) || dados.pressao == 0) {
    Serial.println("Erro: Falha na leitura do sensor BMP280");
    // Continuar mesmo sem pressão válida
    dados.pressao = 0;
  }
  
  // Mostrar dados coletados
  Serial.println("=== DADOS COLETADOS ===");
  Serial.println("Temperatura: " + String(dados.temperatura, 2) + "°C");
  Serial.println("Umidade: " + String(dados.umidade, 2) + "%");
  Serial.println("Pressão: " + String(dados.pressao, 2) + " hPa");
  Serial.println("=====================");
  
  dados.valida = true;
  return dados;
}

void saveConfig() {
  EEPROM.put(0, config);
  EEPROM.commit();
}

void loadConfig() {
  EEPROM.get(0, config);
  if (config.ssid[0] == 0xFF || strlen(config.ssid) == 0) {
    strcpy(config.ssid, "");
    strcpy(config.password, "");
    saveConfig();
  }
}

void startAPMode() {
  WiFi.softAP("ESP32_Config", "");
  IPAddress IP = WiFi.softAPIP();
  Serial.print("Modo AP. Conecte-se ao IP: ");
  Serial.println(IP);

  server.on("/", []() {
    server.send(200, "text/html", 
      "<form action='/save' method='POST'>"
      "SSID: <input type='text' name='ssid'><br>"
      "Senha: <input type='password' name='pass'><br>"
      "<input type='submit' value='Salvar'>"
      "</form>");
  });

  server.on("/save", HTTP_POST, []() {
    strcpy(config.ssid, server.arg("ssid").c_str());
    strcpy(config.password, server.arg("pass").c_str());
    saveConfig();
    server.send(200, "text/plain", "Credenciais salvas. Reiniciando...");
    delay(2000);
    ESP.restart();
  });

  server.begin();
  while (WiFi.status() != WL_CONNECTED) {
    server.handleClient();
    delay(100);
  }
}

void configurar_ntp() {
  Serial.println("Configurando NTP...");
  configTime(gmt_offset_sec, daylight_offset_sec, ntp_server);
  
  Serial.print("Aguardando sincronização NTP");
  int tentativas = 0;
  time_t now = 0;
  
  // Aguardar até 30 segundos para sincronização NTP
  while (tentativas < 30) {
    now = time(nullptr);
    if (now > 1000000000) { // Se timestamp válido (após ano 2001)
      break;
    }
    Serial.print(".");
    delay(1000);
    tentativas++;
  }
  
  Serial.println();
  
  if (now > 1000000000) {
    ntp_synchronized = true;
    Serial.println("✓ NTP sincronizado com sucesso!");
    
    // Mostrar hora atual
    struct tm timeinfo;
    localtime_r(&now, &timeinfo);
    char buffer[50];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &timeinfo);
    Serial.println("Hora atual: " + String(buffer));
  } else {
    ntp_synchronized = false;
    Serial.println("✗ Falha na sincronização NTP - usando estimativa baseada em uptime");
    last_ntp_attempt = millis(); // Marcar para tentar novamente
  }
}

// Função para forçar nova sincronização NTP

void tentar_resincronizar_ntp() {
  Serial.println("Ressincronizando NTP...");
  configTime(gmt_offset_sec, daylight_offset_sec, ntp_server);
  
  // Aguardar 10 segundos
  for (int i = 0; i < 10; i++) {
    delay(1000);
    time_t now = time(nullptr);
    if (now > 1000000000) {
      ntp_synchronized = true;
      Serial.println("✓ NTP ressincronizado com sucesso!");
      
      // Mostrar nova hora
      struct tm timeinfo;
      localtime_r(&now, &timeinfo);
      char buffer[50];
      strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &timeinfo);
      Serial.println("Nova hora: " + String(buffer));
      return;
    }
  }
  ntp_synchronized = false;
  Serial.println("✗ Ressincronização falhou - tentará novamente em 5 minutos");
}

void conectar_wifi() {
  loadConfig();
  WiFi.begin(config.ssid, config.password);
  
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 15) {
    delay(1000);
    Serial.print(".");
    tentativas++;
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nFalha ao conectar ao WiFi");
    Serial.println("\nFalha! Modo AP ativado.");
    currentStatus = ERROR_STATE;
    startAPMode();
  } else {
    Serial.println("\nWiFi Conectado com sucesso!");
    Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("Intensidade Sinal: %d dBm\n", WiFi.RSSI());
  }
}

bool fazer_login() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi não conectado. Não é possível fazer login.");
    return false;
  }
  
  // Configurar cliente HTTPS
  WiFiClientSecure client;
  client.setInsecure(); // Para desenvolvimento - aceita qualquer certificado SSL
  
  HTTPClient http;
  http.begin(client, String(api_base_url) + "/login");
  http.addHeader("Content-Type", "application/json");
  
  // Configurar timeout para HTTPS
  http.setTimeout(15000); // 15 segundos
  
  // Criar JSON de login
  DynamicJsonDocument doc(1024);
  doc["username"] = username;
  doc["password"] = user_password;
  
  String json_string;
  serializeJson(doc, json_string);
  
  Serial.println("Fazendo login na API via HTTPS...");
  Serial.println("URL: " + String(api_base_url) + "/login");
  
  int httpResponseCode = http.POST(json_string);
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    Serial.println("Login realizado com sucesso!");
    
    // Parse da resposta para extrair o token
    DynamicJsonDocument responseDoc(1024);
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (error) {
      Serial.print("Erro ao fazer parse da resposta: ");
      Serial.println(error.c_str());
      http.end();
      return false;
    }
    
    jwt_token = responseDoc["token"].as<String>();
    last_token_time = millis();
    
    Serial.println("Token JWT obtido com sucesso");
    Serial.println("Token (primeiros 20 caracteres): " + jwt_token.substring(0, 20) + "...");
    http.end();
    return true;
  } else {
    Serial.print("Erro no login. Código HTTP: ");
    Serial.println(httpResponseCode);
    String response = http.getString();
    Serial.println("Resposta: " + response);
    http.end();
    return false;
  }
}

bool enviar_dados_api(SensorData dados) {
  if (jwt_token == "") {
    Serial.println("Token JWT não disponível");
    return false;
  }
  
  // Configurar cliente HTTPS
  WiFiClientSecure client;
  client.setInsecure(); // Para desenvolvimento - aceita qualquer certificado SSL
  
  HTTPClient http;
  http.begin(client, String(api_base_url) + "/leituras");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + jwt_token);
  
  // Configurar timeout para HTTPS
  http.setTimeout(15000); // 15 segundos
  
  // Criar timestamp atual (formato ISO)
  String timestamp = obter_timestamp_iso();
  
  // Formatar valores com 2 casas decimais
  String temperatura_formatada = String(dados.temperatura, 2);
  String umidade_formatada = String(dados.umidade, 2);
  String pressao_formatada = String(dados.pressao, 2);
  
  // Criar JSON com os dados formatados
  DynamicJsonDocument doc(1024);
  doc["temperatura"] = temperatura_formatada.toFloat();
  doc["umidade"] = umidade_formatada.toFloat();
  
  // Só incluir pressão se for um valor válido
  if (dados.pressao > 0) {
    doc["pressao"] = pressao_formatada.toFloat();
  }
  
  doc["lote"] = lote_id;
  doc["data_inicial"] = timestamp;
  doc["data_final"] = timestamp;
  
  String json_string;
  serializeJson(doc, json_string);
  
  Serial.println("Enviando dados para API via HTTPS...");
  Serial.println("Valores formatados:");
  Serial.println("  Temperatura: " + temperatura_formatada + "°C");
  Serial.println("  Umidade: " + umidade_formatada + "%");
  if (dados.pressao > 0) {
    Serial.println("  Pressão: " + pressao_formatada + " hPa");
  }
  Serial.println("JSON: " + json_string);
  
  int httpResponseCode = http.POST(json_string);
  
  if (httpResponseCode == 201) {
    String response = http.getString();
    Serial.println("Dados enviados com sucesso!");
    Serial.println("Resposta: " + response);
    http.end();
    return true;
  } else {
    Serial.print("Erro ao enviar dados. Código HTTP: ");
    Serial.println(httpResponseCode);
    String response = http.getString();
    Serial.println("Resposta: " + response);
    
    // Se token inválido, limpar para forçar novo login
    if (httpResponseCode == 401) {
      Serial.println("Token inválido. Limpando token para novo login.");
      jwt_token = "";
    }
    
    http.end();
    return false;
  }
}



// Funçoes auxiliares
// ==================== FUNÇÕES AUXILIARES ====================
String obter_timestamp_iso() {
  // Tentar usar NTP primeiro
  time_t now = time(nullptr);
  
  Serial.println("=== DEBUG TIMESTAMP DETALHADO ===");
  Serial.println("NTP time raw: " + String(now));
  Serial.println("Válido? " + String(now > 1000000000 ? "SIM" : "NÃO"));
  
  if (now > 1000000000) { // Se NTP funcionou (timestamp válido após 2001)
    Serial.println("✓ Usando NTP para timestamp");
    
    struct tm timeinfo;
    localtime_r(&now, &timeinfo); // Usar localtime para GMT-3
    
    char buffer[25];
    strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S", &timeinfo);
    
    Serial.println("Timestamp NTP: " + String(buffer));
    return String(buffer);
  } else {
    Serial.println("✗ NTP falhou - usando estimativa baseada em data atual");
    
    // CORREÇÃO: Usar uma data base mais realística (final de 2024)
    // Base: 31/12/2024 23:59:59 (timestamp: 1735689599)
    unsigned long estimated_time = 1735689599 + (millis() / 1000);
    
    struct tm timeinfo;
    time_t estimated = estimated_time;
    gmtime_r(&estimated, &timeinfo);
    
    char buffer[25];
    strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S", &timeinfo);
    
    Serial.println("Timestamp estimado: " + String(buffer));
    return String(buffer);
  }
}

void debug_timestamp() {
  Serial.println("=== DEBUG TIMESTAMP ===");
  time_t now = time(nullptr);
  Serial.println("NTP time atual: " + String(now));
  Serial.println("Millis(): " + String(millis()));
  Serial.println("Timestamp gerado: " + obter_timestamp_iso());
  
  // Mostrar também a hora local se NTP funcionou
  if (now > 1000000000) {
    struct tm timeinfo;
    localtime_r(&now, &timeinfo);
    char readable[50];
    strftime(readable, sizeof(readable), "%d/%m/%Y %H:%M:%S", &timeinfo);
    Serial.println("Hora legível (GMT-3): " + String(readable));
  }
  Serial.println("========================");
}

// ==================== FUNÇÕES DE DEBUG ====================
void debug_wifi_status() {
  Serial.print("Status WiFi: ");
  switch(WiFi.status()) {
    case WL_CONNECTED:
      Serial.println("Conectado");
      break;
    case WL_NO_SSID_AVAIL:
      Serial.println("SSID não disponível");
      break;
    case WL_CONNECT_FAILED:
      Serial.println("Falha na conexão");
      break;
    case WL_CONNECTION_LOST:
      Serial.println("Conexão perdida");
      break;
    case WL_DISCONNECTED:
      Serial.println("Desconectado");
      break;
    default:
      Serial.println("Outro status");
      break;
  }
}

void debug_memoria() {
  Serial.print("Memória livre: ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");
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

void setup() {
  Serial.begin(115200);
  Serial.println("Iniciando Sistema de Controle do Elevador");

  Wire.begin();

    // Porta Serial 2 - Responsavel para comunicação do display
  Serial2.begin(115200, SERIAL_8N1, RXD2, TXD2);
   
  if(!Serial2){
    Serial.println("Erro ao Inicializar a porta Serial 2 -- Verifique!!!");
    statusSR2 = "DISPLAY - ERROR";
  }
  else{
    Serial.println("Serial 2 Inicializada com sucesso!!!");
    statusSR2 = "DISPLAY - OK";
  }
  
  Lcm.begin();
  mlx.begin();
  aht.begin();
  if (!aht.begin()) {
    Serial.println("Falha ao localizar o sensor AHT10 !");
  }
  Serial.println("AHT10 encontrado e inicializado.");

  temperaturaMLX = mlx.readAmbientTempC();

  if(isnan(temperaturaMLX)){ // verificando se o retorno not a number, ou seja, sem retorno numerico. 
    Serial.println("Verifique o Sensor MLX!");
    Serial.println(" ");
    statusMLX = "MLX - ERROR";
  }
  else{
    Serial.println("MLX Inicializado com sucesso");
    Serial.println(" ");
    statusMLX = "MLX - OK";
  }

  // Inicializando o sensor BMP280
 
  if(!bmp.begin(0x76)){
    Serial.println("Verifique o Sensor BMP!");
    Serial.println(" ");
    statusBMP = "BMP - ERROR";
  }
  else{
    Serial.println("BMP Inicializado com sucesso!");
    Serial.println(" ");
    statusBMP = "BMP - OK";
  }

    // Inicializar EEPROM e WiFi
  EEPROM.begin(sizeof(Config));

  Lcm.changePicId(picIdIntro);


  // Conectar ao WiFi
  conectar_wifi();
  
  // Fazer login inicial
  fazer_login();
  
  // Configurar NTP para timestamps reais
  configurar_ntp();
  
  // Configurar pinos dos motores como saída
  configurarMotores();
  
  // Configurar pinos dos fins de curso como entrada com pullup
  configurarFinsDeCorso();
  
  // Desabilitar todos os motores inicialmente
  desabilitarTodosMotores();
  
  // Realizar homing (ir para posição inicial)
 // realizarHoming();
  
  Serial.println("Sistema Pronto!");
}

void loop() {
  /*
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
  */
  // Pequeno delay para não sobrecarregar o processador
  delay(1);


 if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi desconectado. Tentando reconectar...");
    conectar_wifi();
    return;
  }
  
  // Verificar se precisa tentar ressincronizar NTP
  if (!ntp_synchronized && (millis() - last_ntp_attempt >= ntp_retry_interval)) {
    Serial.println("Tentando ressincronizar NTP...");
    tentar_resincronizar_ntp();
    last_ntp_attempt = millis();
  }
  
  // Verificar se é hora de coletar dados
  if (millis() - last_reading_time >= reading_interval) {
    // Debug do timestamp
    debug_timestamp();
    
    // Coletar dados dos sensores
    SensorData dados = coletar_dados_sensores();
    
    if (dados.valida) {
      // Verificar se o token ainda é válido
      if (millis() - last_token_time >= token_lifetime || jwt_token == "") {
        Serial.println("Token expirado ou inexistente. Fazendo novo login...");
        fazer_login();
      }
      
      // Enviar dados para a API
      if (jwt_token != "") {
        enviar_dados_api(dados);
      }
    }
    
    last_reading_time = millis();
  }
  
  delay(1000); // Pequeno delo sobrecarregar o loop





}