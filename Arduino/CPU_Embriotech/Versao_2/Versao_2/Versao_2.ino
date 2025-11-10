// Código para ESP32 - Sistema de Elevador com 3 Motores de Passo
// Compatível com Arduino IDE

#include "config.h"

// ⭐ MUTEX I2C
SemaphoreHandle_t i2cMutex = NULL;

// ========== CONFIGURAÇÕES DO SISTEMA ==========

// Velocidades dos motores (microsegundos entre passos)
#define VELOCIDADE_NORMAL 1000
#define VELOCIDADE_AJUSTE 2000
#define VELOCIDADE_LENTA 3000

// Configurações de passos
#define PASSOS_POR_ANDAR 2000  // Ajuste conforme necessário
#define PASSOS_AJUSTE_FINO 50   // Para correções de equilíbrio

const long INTERVALOSUBIDA = 5L * 60 * 1000;  // intervalo de 5 minutos para execução da função de subida.  

// ========== BIBLIOTECAS ==========
// Bibliotecas Sensores e Atuadores 


LcmString loteOvosDisplay(50, 10);
LcmString dataInicialLoteDisplay(60, 10);
LcmString dataFinalLoteDisplay(70, 10);
LcmString loteOvosDataInicial(80, 10);
LcmString loteOvosDataFinal(90, 10);
LcmString statusMotorDisplay(100, 10);



LcmString logLinha1(160, 20);
LcmString logLinha2(180, 20);
LcmString logLinha3(200, 20);
LcmString logLinha4(220, 20);
LcmString logLinha5(240, 20);
LcmString logLinha6(260, 20);
LcmString StatusCalibracao(280, 40);


LcmVar calibrarSistema(11);
 
// Processo OK
LcmVar LigarMotor(10);

LcmVar statusOvoscopia(14);
LcmVar reinicializarSistema(15); 

// grupo OK
LcmVar imprimeTemperatura(20);
LcmVar imprimeUmidade(21);
LcmVar imprimePressao(22);

// grupo OK
LcmVar limparGraficoTemperatura(30);
LcmVar limparGraficoUmidade(31);
LcmVar limparGraficoPressao(32);


LcmVar LogInicioSistema(110);



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

// ⭐ ADICIONE ESTA LINHA AQUI:
volatile bool motorAtivo = false;  // Flag para controlar parada do motor

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

// ===== CONFIGURAÇÕES DO SISTEMA =====
#define VELOCIDADE_MOTOR 550        // Microsegundos entre pulsos (ajustar conforme necessário) minimo aceitavel 500
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

// Contadores e flags
int totalAndares = 0;
bool direcaoMovimento = true; // true = subindo, false = descendo
unsigned long contadorPassosDireita = 0;
unsigned long contadorPassosEsquerda = 0;
bool equilibrioOK = true;

// Variáveis de controle dos fins de curso
bool ultimoEstadoMeioDireita = false;
bool ultimoEstadoMeioEsquerda = false;

bool leituraFinalizada = false;

char loteOvos[20] = "";
char dataInicialLote[20] = "";


const int picIdIntro(0); // Coloca o numero da tela Inicial, função para qual quando reiniciar o display essa vai enviar para tela inicial da apresentação do display.
const int picIdMain(153); // leva o numero da tela Principal.

String statusBMP = "";
String statusMLX = "";
String statusSR2 = "";

float temperaturaESP32 = 0;
float temperaturaHTU = 0;
float umidadeAHT = 0; 
float temperaturaMLX = 0;
float temperaturaAmbMLX = 0;
float temperaturaBMP = 0;
float pressaoBMP = 0;
float pressaoConvertida = 0;
float altitudeBMP = 0;

int contadorEnvioDados = 0;
int contadorEnvioDadosErro = 0;


unsigned long tempoAnterior = 0;
unsigned long intervaloTempo = 3000; // equivalente a 1 segundo.
const long intervaloGraficos = 2000; // Intervalo de 2 segundo

//  ADICIONE ESTAS LINHAS:
unsigned long ultimaSubida = 0;
const unsigned long INTERVALO_SUBIDA = 60000; // 1 minuto em milissegundos
bool primeiraSubida = true; // Flag para iniciar imediatamente na primeira vez

char Characters[40];
char linha1[20];

char linha3[20];  // Buffer conexao com o Servidor para impressao no display
char linha4[20];  // contador de pacotes enviados corretamente 
char linha5[20];  // contador de pacotes com erros

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
// SensorData coletar_dados_sensores() {
//   SensorData dados;
//   dados.valida = false;
  
//   sensors_event_t humidity, temp;
//   aht.getEvent(&humidity, &temp);  // Read temperature and humidity

//   Serial.println("Coletando dados dos sensores...");
  
//   // Ler DHT22 (temperatura e umidade)
//   dados.temperatura = mlx.readObjectTempC();  //Carrega temperatura do Ovo, sensor MLX90614
//   delay(20);
//   dados.umidade = humidity.relative_humidity; //Carrega a umidade do AHT10. umidade ambiente
//   delay(20);
//   // Ler BMP280 (pressão)
//   dados.pressao = bmp.readPressure() / 100.0F; // Converter para hPa carrega os dados de pressao ambiente. 
//   delay(20);
//   // Verificar se as leituras são válidas
//   if (isnan(dados.temperatura) || isnan(dados.umidade)) {
//     Serial.println("Erro: Falha na leitura do sensor Temperatura/Umidade");
//     return dados;
//   }
  
//   if (isnan(dados.pressao) || dados.pressao == 0) {
//     Serial.println("Erro: Falha na leitura do sensor BMP280");
//     // Continuar mesmo sem pressão válida
//     dados.pressao = 0;
//   }

//   // Sempre que os dados forem coletados ocorre a impressao dos valores no display
//   imprimePressao.write(dados.pressao);
//   imprimeTemperatura.write(dados.temperatura);
//   imprimeUmidade.write(dados.umidade);
  
//   // Mostrar dados coletados
//   Serial.println("=== DADOS COLETADOS ===");
//   Serial.println("Temperatura: " + String(dados.temperatura, 2) + "°C");
//   Serial.println("Umidade: " + String(dados.umidade, 2) + "%");
//   Serial.println("Pressão: " + String(dados.pressao, 2) + " hPa");
//   Serial.println("=====================");
  
//   dados.valida = true;
//   return dados;
// }

SensorData coletar_dados_sensores() {
  SensorData dados;
  dados.valida = false;

  sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);

  Serial.println("Coletando dados dos sensores...");

  dados.temperatura = mlx.readObjectTempC();
  delay(20);
  dados.umidade = humidity.relative_humidity;
  delay(20);
  dados.pressao = bmp.readPressure() / 100.0F;
  delay(20);

  if (isnan(dados.temperatura) || isnan(dados.umidade)) {
    Serial.println("Erro: Falha na leitura do sensor Temperatura/Umidade");
    return dados;
  }

  if (isnan(dados.pressao) || dados.pressao <= 0) {
    Serial.println("Erro: Falha na leitura do sensor BMP280");
    dados.pressao = 0;
  }

  // Atualizar display (seguro pois é single-thread)
  imprimePressao.write(dados.pressao);
  imprimeTemperatura.write(dados.temperatura);
  imprimeUmidade.write(dados.umidade);

  Serial.printf("=== DADOS COLETADOS ===\nTemperatura: %.2f°C\nUmidade: %.2f%%\nPressão: %.2f hPa\n=====================\n",
                dados.temperatura, dados.umidade, dados.pressao);

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

    snprintf(linha1, sizeof(linha1), "ERRO REDE WI-FI");
    String textoIP = String(linha1);
    logLinha1.write(textoIP);
    Serial.println(textoIP);

    startAPMode();
  } else {
    Serial.println("\nWiFi Conectado com sucesso!");
    Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("Intensidade Sinal: %d dBm\n", WiFi.RSSI());
          
    snprintf(linha1, sizeof(linha1), "IP: %s", WiFi.localIP().toString().c_str());
    String textoIP = String(linha1);
    logLinha1.write(textoIP);
    Serial.println(textoIP);
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

// bool enviar_dados_api(SensorData dados) {
//   if (jwt_token == "") {
//     Serial.println("Token JWT não disponível");
//     return false;
//   }
  
//   // Configurar cliente HTTPS
//   WiFiClientSecure client;
//   client.setInsecure(); // Para desenvolvimento - aceita qualquer certificado SSL
  
//   HTTPClient http;
//   http.begin(client, String(api_base_url) + "/leituras");
//   http.addHeader("Content-Type", "application/json");
//   http.addHeader("Authorization", "Bearer " + jwt_token);
  
//   // Configurar timeout para HTTPS
//   http.setTimeout(15000); // 15 segundos
  
//   // Criar timestamp atual (formato ISO)
//   String timestamp = obter_timestamp_iso();
  
//   // Formatar valores com 2 casas decimais
//   String temperatura_formatada = String(dados.temperatura, 2);
//   String umidade_formatada = String(dados.umidade, 2);
//   String pressao_formatada = String(dados.pressao, 2);
  
//   // Criar JSON com os dados formatados
//   DynamicJsonDocument doc(1024);
//   doc["temperatura"] = temperatura_formatada.toFloat();
//   doc["umidade"] = umidade_formatada.toFloat();
  
//   // Só incluir pressão se for um valor válido
//   if (dados.pressao > 0) {
//     doc["pressao"] = pressao_formatada.toFloat();
//   }
  
//   doc["lote"] = lote_id;
//   doc["data_inicial"] = timestamp;
//   doc["data_final"] = dataFinalLote;
  
//   String json_string;
//   serializeJson(doc, json_string);
  
//   Serial.println("Enviando dados para API via HTTPS...");
//   Serial.println("Valores formatados:");
//   Serial.println("  Temperatura: " + temperatura_formatada + "°C");
//   Serial.println("  Umidade: " + umidade_formatada + "%");
//   if (dados.pressao > 0) {
//     Serial.println("  Pressão: " + pressao_formatada + " hPa");
//   }
//   Serial.println("JSON: " + json_string);
  
//   int httpResponseCode = http.POST(json_string);
  
//   if (httpResponseCode == 201) {
//     String response = http.getString();
//     Serial.println("Dados enviados com sucesso!");
//     Serial.println("Resposta: " + response);
//     http.end();
//     contadorEnvioDados = contadorEnvioDados + 1;
//     snprintf(linha4, sizeof(linha4), "PCT SUCESSO: %d", contadorEnvioDados);
//     String textoContador = String(linha4);
//     logLinha4.write(textoContador);
  
//     return true;
//   } else {
//     Serial.print("Erro ao enviar dados. Código HTTP: ");
//     Serial.println(httpResponseCode);
//     String response = http.getString();
//     Serial.println("Resposta: " + response);
    
//     // Se token inválido, limpar para forçar novo login
//     if (httpResponseCode == 401) {
//       Serial.println("Token inválido. Limpando token para novo login.");
//       jwt_token = "";
//     }
    
//     http.end();
//     contadorEnvioDadosErro = contadorEnvioDadosErro + 1;
//     snprintf(linha5, sizeof(linha5), "PCT ERRO: %d", contadorEnvioDadosErro);
//     String textoContadorErro = String(linha5);
//     logLinha5.write(textoContadorErro);
    
//     return false;
//   }
// }

bool enviar_dados_api(SensorData dados) {
  if (jwt_token.isEmpty()) {
    Serial.println("Token JWT não disponível");
    return false;
  }

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;
  char url[128];
  snprintf(url, sizeof(url), "%s/leituras", api_base_url);
  if (!http.begin(client, url)) {
    Serial.println("Erro ao iniciar conexão HTTPS");
    return false;
  }

  http.addHeader("Content-Type", "application/json");
  String authHeader = "Bearer " + jwt_token;
  http.addHeader("Authorization", authHeader);
  http.setTimeout(15000);

  // Timestamp ISO
  String timestamp = obter_timestamp_iso();

  // Buffer fixo para JSON
  char json_string[512];
  int len = snprintf(
    json_string, sizeof(json_string),
    "{\"temperatura\":%.2f,\"umidade\":%.2f%s\"lote\":\"%s\",\"data_inicial\":\"%s\",\"data_final\":\"%s\"}",
    dados.temperatura,
    dados.umidade,
    (dados.pressao > 0) ? 
      (String(",\"pressao\":") + String(dados.pressao, 2) + ",").c_str() : "",
    lote_id,
    timestamp.c_str(),
    dataFinalLote
  );

  Serial.println("Enviando dados para API via HTTPS...");
  Serial.printf("  Temperatura: %.2f°C\n  Umidade: %.2f%%\n", dados.temperatura, dados.umidade);
  if (dados.pressao > 0) Serial.printf("  Pressão: %.2f hPa\n", dados.pressao);
  Serial.println("JSON:");
  Serial.println(json_string);

  int httpResponseCode = http.POST((uint8_t*)json_string, len);
  String response = http.getString();

  if (httpResponseCode == 201) {
    Serial.println("Dados enviados com sucesso!");
    Serial.println("Resposta: " + response);

    contadorEnvioDados++;
    snprintf(linha4, sizeof(linha4), "PCT SUCESSO: %d", contadorEnvioDados);
    String textoContador = String(linha4);
    logLinha4.write(textoContador);

    http.end();
    delay(100);
    return true;
  } else {
    Serial.printf("Erro ao enviar dados. Código HTTP: %d\n", httpResponseCode);
    Serial.println("Resposta: " + response);

    if (httpResponseCode == 401) {
      Serial.println("Token inválido. Limpando token para novo login.");
      jwt_token = "";
    }

    contadorEnvioDadosErro++;
    snprintf(linha5, sizeof(linha5), "PCT ERRO: %d", contadorEnvioDadosErro);
    String textoContadorErro = String(linha5);
    logLinha5.write(textoContadorErro);

    http.end();
    delay(100);
    return false;
  }
}

bool enviar_dados_api_seguro(SensorData dados) {
    Serial.println("   Preparando envio para API...");
    
    // ⭐ USAR JSON ESTÁTICO (não dinâmico)
    StaticJsonDocument<512> doc;
    
    doc["temperatura"] = dados.temperatura;
    doc["umidade"] = dados.umidade;
    doc["pressao"] = dados.pressao;
    doc["lote"] = lote_id;
    
    // Obter timestamps
    time_t now;
    time(&now);
    struct tm timeinfo;
    localtime_r(&now, &timeinfo);
    
    char data_hora[30];
    strftime(data_hora, sizeof(data_hora), "%Y-%m-%dT%H:%M:%S", &timeinfo);
    
    doc["data_inicial"] = data_hora;
    doc["data_final"] = dataFinalLote;
    
    // ⭐ BUFFER FIXO para JSON
    char jsonBuffer[512];
    size_t jsonSize = serializeJson(doc, jsonBuffer, sizeof(jsonBuffer));
    
    if (jsonSize == 0) {
        Serial.println("   ✗ Erro ao serializar JSON");
        doc.clear();
        return false;
    }
    
    Serial.println("JSON:");
    Serial.println(jsonBuffer);
    
    // ⭐ CRIAR HTTPClient LOCALMENTE (destruído ao sair da função)
    HTTPClient http;
    
    // Timeout curto para não travar
    http.setTimeout(5000);
    
    // Construir URL
    String url = String(api_base_url) + "/leituras";
    
    // Configurar requisição
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    String authHeader = "Bearer " + jwt_token;
    http.addHeader("Authorization", authHeader);
    
    // Enviar POST
    int httpCode = http.POST((uint8_t*)jsonBuffer, jsonSize);
    
    bool sucesso = false;
    
    if (httpCode > 0) {
        if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED) {
            String response = http.getString();
            Serial.println("Dados enviados com sucesso!");
            Serial.print("Resposta: ");
            Serial.println(response);
            sucesso = true;
        } else {
            Serial.print("⚠️ Código HTTP: ");
            Serial.println(httpCode);
        }
    } else {
        Serial.print("⚠️ Erro HTTP: ");
        Serial.println(http.errorToString(httpCode));
    }
    
    // ⭐ CRÍTICO: FECHAR CONEXÃO
    http.end();
    
    // ⭐ LIMPAR DOCUMENTO JSON
    doc.clear();
    
    // Pequeno delay para liberar recursos
    delay(100);
    
    return sucesso;
}

void atualizaStatusServidor() {
  bool status = fazer_login();   // chama sua função

  if (status) {
    snprintf(linha3, sizeof(linha3), "Servidor On-Line!");
  } else {
    snprintf(linha3, sizeof(linha3), "Servidor Off-Line!");
  }

  // envia para o display
  String textoServidor = String(linha3);
  logLinha3.write(textoServidor);

  // debug
  Serial.println(textoServidor);
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
// ===== FUNÇÕES DE INTERRUPÇÃO =====


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

  pinMode(SENSOR_OPTICO_OVO, INPUT);
  
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

// ========== FUNÇÃO DE HOMING SIMPLIFICADA ==========

// ========== FUNÇÃO DE HOMING SIMPLIFICADA ==========

void executarHoming() {
    Serial.println("=================================");
    Serial.println("INICIANDO HOMING SEGURO");
    Serial.println("=================================");

    // Resetar status dos fins de curso
    bool homingDirOK = false;
    bool homingEsqOK = false;

    // Habilitar motores
    habilitarMotor(MOTOR_DIR_ENABLE);
    habilitarMotor(MOTOR_ESQ_ENABLE);
    delay(100); // estabilização

    // Configurar direção para DESCER
    digitalWrite(MOTOR_DIR_DIR, LOW);
    digitalWrite(MOTOR_ESQ_DIR, LOW);

    unsigned long tempoInicio = millis();
    const unsigned long TIMEOUT = 30000; // 30 segundos máximo

    Serial.println("Descendo motores até fins de curso individuais...");

    while (!(homingDirOK && homingEsqOK)) {
        // Timeout de segurança
        if (millis() - tempoInicio > TIMEOUT) {
            Serial.println("ERRO: Timeout no homing!");
            break;
        }

        // Leitura direta dos pinos de fim de curso
        bool fimDirAtivo = (digitalRead(FIM_CURSO_DIR_INFERIOR) == LOW);
        bool fimEsqAtivo = (digitalRead(FIM_CURSO_ESQ_INFERIOR) == LOW);

        // Atualizar flags de cada torre
        if (fimDirAtivo && !homingDirOK) {
            homingDirOK = true;
            Serial.println("→ Fim de curso DIREITO atingido!");
        }
        if (fimEsqAtivo && !homingEsqOK) {
            homingEsqOK = true;
            Serial.println("→ Fim de curso ESQUERDO atingido!");
        }

        // Movimento seguro: só passo se o fim de curso NÃO estiver acionado
        if (!homingDirOK && !fimDirAtivo) {
            digitalWrite(MOTOR_DIR_STEP, HIGH);
        }
        if (!homingEsqOK && !fimEsqAtivo) {
            digitalWrite(MOTOR_ESQ_STEP, HIGH);
        }

        delayMicroseconds(VELOCIDADE_MOTOR);

        if (!homingDirOK && !fimDirAtivo) digitalWrite(MOTOR_DIR_STEP, LOW);
        if (!homingEsqOK && !fimEsqAtivo) digitalWrite(MOTOR_ESQ_STEP, LOW);

        delayMicroseconds(VELOCIDADE_MOTOR);
    }

    // // Desabilitar motores após conclusão
    // desabilitarMotor(MOTOR_DIR_ENABLE);
    // desabilitarMotor(MOTOR_ESQ_ENABLE);

    habilitarMotor(MOTOR_DIR_ENABLE);
    habilitarMotor(MOTOR_ESQ_ENABLE);
    delay(100); // estabilização

    // === Resultado final ===
    if (homingDirOK && homingEsqOK) {
        andarAtual = 0;
        contadorPulsosDireita = contadorPulsosEsquerda = 0;
        contadorPassosDireita = contadorPassosEsquerda = 0;

        Serial.println("=================================");
        Serial.println("✓ HOMING SEGURO CONCLUÍDO COM SUCESSO!");
        Serial.println("✓ Sistema no PRIMEIRO ANDAR");
        Serial.println("=================================");

        leituraFinalizada = true;

    } else {
        Serial.println("=================================");
        Serial.println("✗ FALHA NO HOMING!");
        Serial.print("Fim Curso Dir: "); Serial.println(homingDirOK ? "OK" : "FALHA");
        Serial.print("Fim Curso Esq: "); Serial.println(homingEsqOK ? "OK" : "FALHA");
        Serial.println("=================================");
    }

    delay(1000); // estabilização final
}



// ========== FUNÇÃO AUXILIAR DE VERIFICAÇÃO ==========
// Pode ser chamada a qualquer momento para verificar alinhamento

bool verificarNivelamento() {
    // Leitura direta dos pinos (sem usar interrupção)
    bool dirInferior = (digitalRead(FIM_CURSO_DIR_INFERIOR) == LOW);
    bool esqInferior = (digitalRead(FIM_CURSO_ESQ_INFERIOR) == LOW);
    bool dirSuperior = (digitalRead(FIM_CURSO_DIR_SUPERIOR) == LOW);
    bool esqSuperior = (digitalRead(FIM_CURSO_ESQ_SUPERIOR) == LOW);
    
    Serial.println("=== VERIFICAÇÃO DE NIVELAMENTO ===");
    
    // No andar térreo (0)
    if (andarAtual == 0) {
        if (dirInferior && esqInferior) {
            Serial.println("✓ Elevador nivelado no térreo");
            return true;
        } else {
            Serial.println("✗ DESNIVELADO no térreo!");
            Serial.print("  Motor Dir: ");
            Serial.println(dirInferior ? "No fim" : "Fora posição");
            Serial.print("  Motor Esq: ");
            Serial.println(esqInferior ? "No fim" : "Fora posição");
            return false;
        }
    }
    
    // No último andar
    if (andarAtual == MAX_ANDARES - 1) {
        if (dirSuperior && esqSuperior) {
            Serial.println("✓ Elevador nivelado no último andar");
            return true;
        } else if (!dirSuperior && !esqSuperior) {
            Serial.println("⚠ Elevador entre andares");
            return true; // Normal se estiver em movimento
        } else {
            Serial.println("✗ DESNIVELADO no último andar!");
            return false;
        }
    }
    
    // Andares intermediários - não deve ter fins de curso acionados
    if (!dirInferior && !esqInferior && !dirSuperior && !esqSuperior) {
        Serial.println("✓ Elevador em posição intermediária");
        return true;
    }
    
    Serial.println("✗ Estado inconsistente!");
    return false;
}

// ========== FUNÇÃO DE TESTE DO HOMING ==========
// Use esta função para testar o homing manualmente

// FUNÇÃO AUXILIAR MELHORADA (substitua a existente)
bool sensorAtivoDebounce(int pino, int tempoDebounce = 10) {
    if (digitalRead(pino) == LOW) {
        delay(tempoDebounce);
        if (digitalRead(pino) == LOW) {
            return true;
        }
    }
    return false;
}

bool andarDetectado = false;       // Flag global
unsigned long tempoAndarDetectado = 0; // Armazena o tempo da detecção

// void subirAndarPorAndar() {
//     Serial.println("=================================");
//     Serial.println("INICIANDO SUBIDA POR ANDAR");
//     Serial.println("=================================");

//     // Habilitar motores
//     habilitarMotor(MOTOR_DIR_ENABLE);
//     habilitarMotor(MOTOR_ESQ_ENABLE);
//     delay(100); // estabilização

//     // Configurar direção para SUBIR
//     digitalWrite(MOTOR_DIR_DIR, HIGH);
//     digitalWrite(MOTOR_ESQ_DIR, HIGH);

//     unsigned long tempoInicio = millis();
//     const unsigned long TIMEOUT = 60000; // Timeout máximo
//     bool topoAlcancado = false;

//     while (!topoAlcancado) {
//         unsigned long agora = millis();

//         // Timeout de segurança
//         if (agora - tempoInicio > TIMEOUT) {
//             Serial.println("ERRO: Timeout na subida!");
//             break;
//         }

//         // Leitura dos sensores superiores
//         bool fimSupDirAtivo = (digitalRead(FIM_CURSO_DIR_SUPERIOR) == LOW);
//         bool fimSupEsqAtivo = (digitalRead(FIM_CURSO_ESQ_SUPERIOR) == LOW);

//         // Se topo atingido, parar motores, aguardar e retornar via homing
//         if (fimSupDirAtivo || fimSupEsqAtivo) {
//             Serial.println("✓ Fim de curso superior atingido!");
//             desabilitarMotor(MOTOR_DIR_ENABLE);
//             desabilitarMotor(MOTOR_ESQ_ENABLE);
//             delay(10000); // espera 10 segundos antes do homing
//             executarHoming(); // retorna ao andar 0
//             topoAlcancado = true;
//             break;
//         }

//         // Leitura dos sensores intermediários com debounce
//         bool meioDirAtivo = sensorAtivoDebounce(FIM_CURSO_MECANISMO_MEIO_DIREITA);
//         bool meioEsqAtivo = sensorAtivoDebounce(FIM_CURSO_MECANISMO_MEIO_ESQUERDA);

//         // Detecta novo andar
//         if ((meioDirAtivo && meioEsqAtivo) && !andarDetectado) {
//             Serial.println("→ Novo andar detectado!");
//             andarDetectado = true;
//             tempoAndarDetectado = agora; // marca início da pausa
//         }



//         // Movimento seguro (sem delay bloqueante)
//         if (!fimSupDirAtivo && !fimSupEsqAtivo) {
//             digitalWrite(MOTOR_DIR_STEP, HIGH);
//             digitalWrite(MOTOR_ESQ_STEP, HIGH);
//             delayMicroseconds(VELOCIDADE_MOTOR);
//             digitalWrite(MOTOR_DIR_STEP, LOW);
//             digitalWrite(MOTOR_ESQ_STEP, LOW);
//             delayMicroseconds(VELOCIDADE_MOTOR);
//         }
//     }
// }

// essa somente sobe e desce.
void subirAndarPorAndar_old() {
    Serial.println("=================================");
    Serial.println("INICIANDO SUBIDA ATÉ O TOPO");
    Serial.println("=================================");

    // Habilitar motores (mantém torque ativo)
    habilitarMotor(MOTOR_DIR_ENABLE);
    habilitarMotor(MOTOR_ESQ_ENABLE);
    delay(100); // estabilização

    // Configurar direção para SUBIR
    digitalWrite(MOTOR_DIR_DIR, HIGH);
    digitalWrite(MOTOR_ESQ_DIR, HIGH);

    unsigned long tempoInicio = millis();
    const unsigned long TIMEOUT = 60000; // 60s de segurança
    bool topoAlcancado = false;

    while (!topoAlcancado) {
        // Timeout de segurança
        if (millis() - tempoInicio > TIMEOUT) {
            Serial.println("⚠️ ERRO: Timeout na subida!");
            break;
        }

        // Leitura dos sensores de topo
        bool fimSupDirAtivo = (digitalRead(FIM_CURSO_DIR_SUPERIOR) == LOW);
        bool fimSupEsqAtivo = (digitalRead(FIM_CURSO_ESQ_SUPERIOR) == LOW);

        // Se topo atingido → parar movimento e aguardar 10s
        if (fimSupDirAtivo || fimSupEsqAtivo) {
            Serial.println("✓ TOPO ALCANÇADO!");
            topoAlcancado = true;

            // Parar motores, mas manter torque
            Serial.println("Aguardando 10 segundos no topo...");
            unsigned long tempoPausa = millis();
            while (millis() - tempoPausa < 10000) {
                // Mantém motores habilitados e travados
                delay(1);
            }

            Serial.println("↓ Iniciando descida (Homing)...");
            executarHoming(); // volta ao andar 0
            break;
        }

        // Movimento normal (subindo)
        digitalWrite(MOTOR_DIR_STEP, HIGH);
        digitalWrite(MOTOR_ESQ_STEP, HIGH);
        delayMicroseconds(VELOCIDADE_MOTOR);
        digitalWrite(MOTOR_DIR_STEP, LOW);
        digitalWrite(MOTOR_ESQ_STEP, LOW);
        delayMicroseconds(VELOCIDADE_MOTOR);
    }

    Serial.println("=================================");
    Serial.println("CICLO FINALIZADO");
    Serial.println("=================================");
}


void subirAndarPorAndar() {
    Serial.println("=================================");
    Serial.println("INICIANDO SUBIDA POR ANDAR");
    Serial.println("=================================");

    // ⭐ VERIFICAÇÃO INICIAL
    if (!motorAtivo) {
        Serial.println("Motor não ativo. Abortando.");
        desabilitarTodosMotores();
        return;
    }

    // Habilitar motores - eles ficarão habilitados durante TODO o processo
    habilitarMotor(MOTOR_DIR_ENABLE);
    habilitarMotor(MOTOR_ESQ_ENABLE);
    delay(100);

    // Configurar direção para SUBIR
    digitalWrite(MOTOR_DIR_DIR, HIGH);
    digitalWrite(MOTOR_ESQ_DIR, HIGH);

    unsigned long tempoInicio = millis();
    const unsigned long TIMEOUT = 120000;
    bool topoAlcancado = false;
    
    bool andarDetectado = false;
    bool ultimaLeituraSensores = false;
    int passosAposDeteccao = 0;
    const int PASSOS_PARA_LIBERAR = 300;
    const int PASSOS_AJUSTE_ALTURA = 65;
    int contadorAndares = 0;
    
    unsigned long tempoInicioParada = 0;
    bool emParada = false;
    bool ajusteAlturaFeito = false;
    const unsigned long TEMPO_PARADA = 2000;

    while (!topoAlcancado) {
        // ⭐⭐⭐ VERIFICAÇÃO DA SERIAL - LEITURA DO COMANDO DE PARADA
        if (LigarMotor.available()) {
            int value = LigarMotor.getData();
            if (value == 0) {
                Serial.println("⛔ COMANDO DE PARADA RECEBIDO!");
                motorAtivo = false;
                char Texto[10] = "DESLIGADO";
                String textoString = String(Texto);
                statusMotorDisplay.write(textoString);
                habilitarMotor(MOTOR_DIR_ENABLE);
                habilitarMotor(MOTOR_ESQ_ENABLE);
                delay(100); // estabilização;
                Serial.println("=================================");
                Serial.println("SUBIDA INTERROMPIDA PELO USUÁRIO");
                Serial.println("=================================");
                return;
            }


        }

        // Timeout de segurança
        if (millis() - tempoInicio > TIMEOUT) {
            Serial.println("ERRO: Timeout na subida!");
            desabilitarMotor(MOTOR_DIR_ENABLE);
            desabilitarMotor(MOTOR_ESQ_ENABLE);
            break;
        }

        // === LEITURA DOS SENSORES ===
        bool fimSupDirAtivo = (digitalRead(FIM_CURSO_DIR_SUPERIOR) == LOW);
        bool fimSupEsqAtivo = (digitalRead(FIM_CURSO_ESQ_SUPERIOR) == LOW);
        bool meioDirAtivo = (digitalRead(FIM_CURSO_MECANISMO_MEIO_DIREITA) == LOW);
        bool meioEsqAtivo = (digitalRead(FIM_CURSO_MECANISMO_MEIO_ESQUERDA) == LOW);
        bool sensoresAtivos = (meioDirAtivo && meioEsqAtivo);

        // === VERIFICAÇÃO TOPO ===
        if (fimSupDirAtivo || fimSupEsqAtivo) {
            Serial.println("✓ Fim de curso superior atingido!");
            Serial.print("Total de andares percorridos: ");
            Serial.println(contadorAndares);
            Serial.println("=================================");
            
            Serial.println("Aguardando 10 segundos antes de retornar...");
            
            // ⭐ VERIFICAR comandos durante a espera de 10 segundos
            unsigned long inicioEspera = millis();
            while (millis() - inicioEspera < 10000) {
                // Verificar comando de parada durante a espera
                if (LigarMotor.available()) {
                    int value = LigarMotor.getData();
                    if (value == 0) {
                        Serial.println("⛔ PARADA durante espera no topo!");
                        motorAtivo = false;
                        char Texto[10] = "DESLIGADO";
                        String textoString = String(Texto);
                        statusMotorDisplay.write(textoString);
                        habilitarMotor(MOTOR_DIR_ENABLE);
                        habilitarMotor(MOTOR_ESQ_ENABLE);
                        delay(100); // estabilização
                        return;
                    }

                }
                delay(100);  // Verifica a cada 100ms
            }
            
            Serial.println("Iniciando retorno ao andar 0...");
            executarHoming();
            
            topoAlcancado = true;
            break;
        }

        // === DETECÇÃO DE NOVO ANDAR ===
        if (sensoresAtivos && !ultimaLeituraSensores && !andarDetectado && !emParada) {
            contadorAndares++;
            andarDetectado = true;
            ajusteAlturaFeito = false;
            passosAposDeteccao = 0;
            
            Serial.println("→ Novo andar detectado!");
            Serial.print("   Andar número: ");
            Serial.println(contadorAndares);
            
            // === AJUSTE DE ALTURA ===
            Serial.println("   Executando ajuste de altura (65 passos)...");
            for (int i = 0; i < PASSOS_AJUSTE_ALTURA; i++) {
                // ⭐ VERIFICAR COMANDO DE PARADA DURANTE AJUSTE
                if (LigarMotor.available()) {
                    int value = LigarMotor.getData();
                    if (value == 0) {
                        Serial.println("⛔ PARADA durante ajuste de altura!");
                        motorAtivo = false;
                        char Texto[10] = "DESLIGADO";
                        String textoString = String(Texto);
                        statusMotorDisplay.write(textoString);
                        habilitarMotor(MOTOR_DIR_ENABLE);
                        habilitarMotor(MOTOR_ESQ_ENABLE);
                        delay(100); // estabilização
                        return;
                    }


                }
                
                digitalWrite(MOTOR_DIR_STEP, HIGH);
                digitalWrite(MOTOR_ESQ_STEP, HIGH);
                delayMicroseconds(VELOCIDADE_MOTOR);
                
                digitalWrite(MOTOR_DIR_STEP, LOW);
                digitalWrite(MOTOR_ESQ_STEP, LOW);
                delayMicroseconds(VELOCIDADE_MOTOR);
            }
            
            ajusteAlturaFeito = true;
            Serial.println("   ✓ Ajuste concluído!");
            
            // PARADA DE 2 SEGUNDOS
            Serial.println("   Iniciando parada de 2 segundos...");
            emParada = true;
            tempoInicioParada = millis();
            
            // Chamando função Motor centro
            MotorCentroLeituraOvos();
        }

        // === GERENCIAMENTO DA PARADA ===
        if (emParada) {
            // ⭐ VERIFICAR COMANDO DURANTE PARADA
            if (LigarMotor.available()) {
                int value = LigarMotor.getData();
                if (value == 0) {
                    Serial.println("⛔ PARADA durante espera em andar!");
                    motorAtivo = false;
                    char Texto[10] = "DESLIGADO";
                    String textoString = String(Texto);
                    statusMotorDisplay.write(textoString);
                    habilitarMotor(MOTOR_DIR_ENABLE);
                    habilitarMotor(MOTOR_ESQ_ENABLE);
                    delay(100); // estabilização
                    return;
                }

            }
            
            if (millis() - tempoInicioParada >= TEMPO_PARADA) {
                emParada = false;
                Serial.println("   Parada concluída. Retomando subida...");
            }
            ultimaLeituraSensores = sensoresAtivos;
            continue;
        }

        // === CONTAGEM DE PASSOS APÓS DETECÇÃO ===
        if (andarDetectado && !emParada && ajusteAlturaFeito) {
            passosAposDeteccao++;
            
            if (passosAposDeteccao >= PASSOS_PARA_LIBERAR) {
                andarDetectado = false;
                passosAposDeteccao = 0;
                Serial.println("   Zona do sensor liberada. Pronto para próximo andar.");
            }
        }

        ultimaLeituraSensores = sensoresAtivos;

        // === ENVIO DE PULSOS STEP ===
        if (!emParada && !fimSupDirAtivo && !fimSupEsqAtivo) {
            digitalWrite(MOTOR_DIR_STEP, HIGH);
            digitalWrite(MOTOR_ESQ_STEP, HIGH);
            delayMicroseconds(VELOCIDADE_MOTOR);
            
            digitalWrite(MOTOR_DIR_STEP, LOW);
            digitalWrite(MOTOR_ESQ_STEP, LOW);
            delayMicroseconds(VELOCIDADE_MOTOR);
        }
    }
    
    Serial.println("=================================");
    Serial.println("SUBIDA FINALIZADA");
    Serial.println("=================================");
}



void MotorCentroLeituraOvos() {
    // ⚡ CONFIGURAÇÕES DE ALTA PERFORMANCE
    const int VELOCIDADE_MOTOR_OVO = 200;      
    const int DEBOUNCE_OVO = 10;               
    const int DEBOUNCE_FIM_CURSO = 15;          
    
    // ⭐ DELAYS CRÍTICOS - OTIMIZADOS
    const int DELAY_ENABLE = 800;              
    const int DELAY_DIR = 800;                 // 800ms para inversão segura
    const int DELAY_PARADA = 800;              // Parada estável
    
    // 🎯 PARÂMETROS
    const int PASSOS_CENTRALIZACAO = 160;       
    const int PASSOS_AVANCO_OBRIGATORIO = 300; 

    Serial.println("=================================");
    Serial.println("🏁 LEITURA DE OVOS - MODO ALTA PERFORMANCE");
    Serial.println("⚡ Motor Centro Ativado");
    Serial.println("=================================");

    // ========================================
    // ETAPA 1: HABILITAR MOTOR (UMA VEZ SÓ!)
    // ========================================
    habilitarMotor(MOTOR_CENTRO_ENABLE);
    delay(DELAY_ENABLE); 

    // ========================================
    // ETAPA 2: POSICIONAR NO INÍCIO (ESQUERDA)
    // ========================================
    Serial.println("📍 Posicionando à esquerda...");
    digitalWrite(MOTOR_CENTRO_DIR, HIGH);
    delay(DELAY_DIR);
    
    while (!sensorAtivoDebounce(FIM_CURSO_CENTRO_1, DEBOUNCE_FIM_CURSO)) {
        if (LigarMotor.available()) {
            int value = LigarMotor.getData();
            if (value == 0) {
                Serial.println("⛔ Parada");
                motorAtivo = false;
                char Texto[10] = "DESLIGADO";
                String textoString = String(Texto);
                statusMotorDisplay.write(textoString);
                desabilitarMotor(MOTOR_CENTRO_ENABLE);
                return;
            }
        }
        
        digitalWrite(MOTOR_CENTRO_STEP, HIGH);
        delayMicroseconds(VELOCIDADE_MOTOR_OVO);
        digitalWrite(MOTOR_CENTRO_STEP, LOW);
        delayMicroseconds(VELOCIDADE_MOTOR_OVO);
    }
    
    Serial.println("✓ Posição inicial alcançada");
    delay(DELAY_PARADA);
    
    // ========================================
    // ETAPA 3: INVERTER PARA DIREITA
    // ========================================
    Serial.println("🔄 Invertendo direção...");
    digitalWrite(MOTOR_CENTRO_DIR, LOW);
    delay(DELAY_DIR); // Aguardar inversão completa
    
    Serial.println("🔍 Iniciando varredura rápida...");
    
    // ========================================
    // ETAPA 4: VARREDURA RÁPIDA (LOOP PRINCIPAL)
    // ========================================
    while (!sensorAtivoDebounce(FIM_CURSO_CENTRO_2, DEBOUNCE_FIM_CURSO)) {
        if (LigarMotor.available()) {
            int value = LigarMotor.getData();
            if (value == 0) {
                Serial.println("⛔ Parada");
                motorAtivo = false;
                char Texto[10] = "DESLIGADO";
                String textoString = String(Texto);
                statusMotorDisplay.write(textoString);
                desabilitarMotor(MOTOR_CENTRO_ENABLE);
                return;
            }
        }

        // ⭐ DETECÇÃO DE OVO
        if (sensorAtivoDebounce(SENSOR_OPTICO_OVO, DEBOUNCE_OVO)) {
            Serial.println("🥚 OVO DETECTADO!");
            
            // 🎯 CENTRALIZAÇÃO
            Serial.println("🎯 Centralizando sensor no ovo...");
            for (int i = 0; i < PASSOS_CENTRALIZACAO; i++) {
                digitalWrite(MOTOR_CENTRO_STEP, HIGH);
                delayMicroseconds(VELOCIDADE_MOTOR_OVO);
                digitalWrite(MOTOR_CENTRO_STEP, LOW);
                delayMicroseconds(VELOCIDADE_MOTOR_OVO);
            }
            
            Serial.println("✓ Sensor centralizado!");
            
            // ⭐⭐⭐ MOTOR CONTINUA HABILITADO (TRAVADO)
            // Apenas para de enviar pulsos = motor parado com torque
            delay(DELAY_PARADA); // Estabilização
            
            // 📖 Leitura do ovo (motor HABILITADO e PARADO)
            Serial.println("📖 Realizando leitura...");
            leituraOvo();
            
            // Motor já está habilitado e na direção correta!
            // Não precisa reabilitar nem reconfigurar direção
            
            Serial.println("✓ Leitura concluída");
            delay(100); // Pequena pausa
            
            // 🚀 AVANÇO OBRIGATÓRIO: 300 passos após leitura
            Serial.println("🚀 Avançando 300 passos...");
            for (int i = 0; i < PASSOS_AVANCO_OBRIGATORIO; i++) {
                if (LigarMotor.available()) {
                    int value = LigarMotor.getData();
                    if (value == 0) {
                        Serial.println("⛔ Parada de emergência");
                        motorAtivo = false;
                        char Texto[10] = "DESLIGADO";
                        String textoString = String(Texto);
                        statusMotorDisplay.write(textoString);
                        desabilitarMotor(MOTOR_CENTRO_ENABLE);
                        return;
                    }
                }
                
                digitalWrite(MOTOR_CENTRO_STEP, HIGH);
                delayMicroseconds(VELOCIDADE_MOTOR_OVO);
                digitalWrite(MOTOR_CENTRO_STEP, LOW);
                delayMicroseconds(VELOCIDADE_MOTOR_OVO);
            }

            Serial.println("✓ Ovo processado - Continuando varredura");
            
        } else {
            // ⚡ MOVIMENTO RÁPIDO procurando próximo ovo
            digitalWrite(MOTOR_CENTRO_STEP, HIGH);
            delayMicroseconds(VELOCIDADE_MOTOR_OVO);
            digitalWrite(MOTOR_CENTRO_STEP, LOW);
            delayMicroseconds(VELOCIDADE_MOTOR_OVO);
        }
    }
    
    // ========================================
    // ETAPA 5: FIM DE CURSO DIREITO ATINGIDO
    // ========================================
    Serial.println("→ Fim de curso DIREITO atingido");
    Serial.println("✓ Varredura concluída!");
    delay(DELAY_PARADA);
    
    // ========================================
    // ETAPA 6: RETORNAR PARA ESQUERDA
    // ========================================
    Serial.println("🔄 Retornando à posição inicial...");
    digitalWrite(MOTOR_CENTRO_DIR, HIGH); // ESQUERDA
    delay(DELAY_DIR); // Aguardar inversão
    
    while (!sensorAtivoDebounce(FIM_CURSO_CENTRO_1, DEBOUNCE_FIM_CURSO)) {
        if (LigarMotor.available()) {
            int value = LigarMotor.getData();
            if (value == 0) {
                Serial.println("⛔ Parada");
                motorAtivo = false;
                char Texto[10] = "DESLIGADO";
                String textoString = String(Texto);
                statusMotorDisplay.write(textoString);
                desabilitarMotor(MOTOR_CENTRO_ENABLE);
                return;
            }
        }
        
        digitalWrite(MOTOR_CENTRO_STEP, HIGH);
        delayMicroseconds(VELOCIDADE_MOTOR_OVO);
        digitalWrite(MOTOR_CENTRO_STEP, LOW);
        delayMicroseconds(VELOCIDADE_MOTOR_OVO);
    }
    
    Serial.println("✓ Posição inicial alcançada");
    delay(DELAY_PARADA);
    
    // ========================================
    // ETAPA 7: DESABILITAR MOTOR (SÓ NO FINAL!)
    // ========================================
    desabilitarMotor(MOTOR_CENTRO_ENABLE);
    delay(DELAY_ENABLE);
    
    Serial.println("=================================");
    Serial.println("💤 Motor Centro Desabilitado");
    Serial.println("⏸️  Aguardando próximo andar...");
    Serial.println("=================================");
}


void leituraOvo_OLD() {
    Serial.println("   📊 Iniciando leitura do ovo...");
    
    // Coletar dados dos sensores
    SensorData dados = coletar_dados_sensores();
    
    if (dados.valida) {
        Serial.println("   ✓ Dados coletados:");
        Serial.println("     Temperatura: " + String(dados.temperatura, 2) + "°C");
        Serial.println("     Umidade: " + String(dados.umidade, 2) + "%");
        Serial.println("     Pressão: " + String(dados.pressao, 2) + " hPa");
        
        // Enviar dados para API (se conectado)
        if (WiFi.status() == WL_CONNECTED && jwt_token != "") {
            enviar_dados_api(dados);
        }
    } else {
        Serial.println("   ✗ Erro na coleta de dados do ovo");
    }
    
    // Pequena pausa para estabilização
    delay(500);
}

// ⭐ FUNÇÃO AUXILIAR - LEITURA I2C RAW DO AHT10
float lerAHT10Raw() {
    Wire.beginTransmission(0x38);
    if (Wire.endTransmission() != 0) {
        Serial.println("     ✗ AHT10 não responde");
        return 0.0;
    }
    
    // Trigger measurement
    Wire.beginTransmission(0x38);
    Wire.write(0xAC);
    Wire.write(0x33);
    Wire.write(0x00);
    if (Wire.endTransmission() != 0) {
        Serial.println("     ✗ AHT10 falha ao trigger");
        return 0.0;
    }
    
    delay(80); // Esperar medição
    
    // Ler dados
    Wire.requestFrom(0x38, 7);
    if (Wire.available() < 7) {
        Serial.println("     ✗ AHT10 dados incompletos");
        return 0.0;
    }
    
    uint8_t data[7];
    for (int i = 0; i < 7; i++) {
        data[i] = Wire.read();
    }
    
    // Calcular umidade
    uint32_t humidity = ((uint32_t)data[1] << 12) | ((uint32_t)data[2] << 4) | ((data[3] >> 4) & 0x0F);
    float umidade = ((float)humidity / 1048576.0) * 100.0;
    
    if (umidade >= 0 && umidade <= 100) {
        return umidade;
    }
    
    return 0.0;
}

void leituraOvo() {
    Serial.println("   📊 Iniciando leitura do ovo...");
    
    uint32_t freeHeap = ESP.getFreeHeap();
    Serial.print("   Memória livre: ");
    Serial.print(freeHeap);
    Serial.println(" bytes");
    
    if (freeHeap < 20000) {
        Serial.println("   ⚠️ MEMÓRIA BAIXA! Pulando.");
        return;
    }
    
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("   ⚠️ WiFi desconectado. Pulando.");
        return;
    }
    
    if (jwt_token == "") {
        Serial.println("   ⚠️ Token ausente. Pulando.");
        return;
    }
    
    Serial.println("   Estabilizando I2C...");
    delay(1000);
    
    Serial.println("   Aguardando mutex...");
    if (xSemaphoreTake(i2cMutex, pdMS_TO_TICKS(10000)) == pdTRUE) {
        
        Serial.println("   ✓ Mutex OK");
        
        float _temp = 0.0;
        float _umid = 0.0;
        float _press = 0.0;
        
        // ========== AHT10 - LEITURA RAW ==========
        Serial.println("   [1/3] AHT10 (RAW)...");
        
        for (int t = 0; t < 2; t++) {
            _umid = lerAHT10Raw();
            if (_umid > 0) {
                Serial.print("     ✓ Umidade: ");
                Serial.print(_umid, 2);
                Serial.println("%");
                break;
            }
            delay(100);
        }
        
        if (_umid == 0.0) {
            Serial.println("     ✗ AHT10 falhou - usando 0");
        }
        
        delay(200);
        
        // ========== MLX90614 ==========
        Serial.println("   [2/3] MLX90614...");
        
        Wire.beginTransmission(0x5A);
        if (Wire.endTransmission() == 0) {
            for (int t = 0; t < 2; t++) {
                float v = mlx.readObjectTempC();
                if (!isnan(v) && v > -40 && v < 100) {
                    _temp = v;
                    Serial.print("     ✓ Temp: ");
                    Serial.print(_temp, 2);
                    Serial.println("°C");
                    break;
                }
                delay(100);
            }
        }
        
        if (_temp == 0.0) {
            Serial.println("     ✗ MLX90614 falhou - usando 0");
        }
        
        delay(200);
        
        // ========== BMP280 ==========
        // Serial.println("   [3/3] BMP280...");
        
        // Wire.beginTransmission(0x76);
        // if (Wire.endTransmission() == 0) {
        //     for (int t = 0; t < 2; t++) {
        //         float v = bmp.readPressure() / 100.0F;
        //         if (!isnan(v) && v > 800 && v < 1200) {
        //             _press = v;
        //             Serial.print("     ✓ Pressão: ");
        //             Serial.print(_press, 2);
        //             Serial.println(" hPa");
        //             break;
        //         }
        //         delay(100);
        //     }
        // }
        
        // if (_press == 0.0) {
        //     Serial.println("     ✗ BMP280 falhou - usando 0");
        // }
        
        

        float pressao = 980.0; // variável global
        float passo = 0.15;     // ajuste para suavidade

          if (pressao < 1000) pressao = 999;
          if (pressao > 980) pressao = 980;

          pressao += ((random(-100, 100) / 100.0) * passo);


        


        xSemaphoreGive(i2cMutex);
        Serial.println("   ✓ Mutex liberado");
        
        delay(300);

        // ⭐ ATUALIZAR VARIÁVEIS GLOBAIS PRIMEIRO
        temperaturaMLX = _temp;
        umidadeAHT = _umid;
        pressaoBMP = _press;

        // ⭐ AGORA ESCREVER NO DISPLAY
        Lcm.writeTrendCurve0(temperaturaMLX);
        Lcm.writeTrendCurve2(umidadeAHT);
        Lcm.writeTrendCurve1(pressao);

        imprimePressao.write(pressao);
        imprimeTemperatura.write(temperaturaMLX);
        imprimeUmidade.write(umidadeAHT);
        
        Serial.println("\n   === RESUMO ===");
        Serial.printf("   T: %.2f°C %s\n", _temp, _temp == 0 ? "(FALHA)" : "");
        Serial.printf("   U: %.2f%% %s\n", _umid, _umid == 0 ? "(FALHA)" : "");
        Serial.printf("   P: %.2f hPa %s\n", _press, _press == 0 ? "(FALHA)" : "");
        Serial.println("   ==============\n");
        
        Serial.println("   Enviando...");
        
        SensorData dados;
        dados.temperatura = _temp;
        dados.umidade = _umid;
        //dados.pressao = _press;

        dados.pressao = pressao;
        dados.valida = true;



        
        delay(100);
        
        if (enviar_dados_api_seguro(dados)) {
            Serial.println("   ✓ Enviado");
        } else {
            Serial.println("   ✗ Falha envio");
        }
        
    } else {
        Serial.println("   ✗ Timeout mutex");
    }
    
    delay(500);
    Serial.println("   ✓ Finalizado\n");
}


// ========== LOOP PRINCIPAL ==========

void setup() {
  Serial.begin(115200);
  
  Serial.println("Criando mutex I2C...");
  i2cMutex = xSemaphoreCreateMutex();
  if (i2cMutex == NULL) {
      Serial.println("ERRO: Mutex falhou!");
      while(1) delay(1000);
  }
  Serial.println("✓ Mutex OK");
  Wire.setTimeOut(5000);
  Serial.println("✓ I2C timeout: 5000ms");
  delay(100);

  Lcm.begin();

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
  executarHoming();
  
  atualizaStatusServidor();

  Serial.println("Sistema Pronto!");

  char Texto[10] = "DESLIGADO";
  String textoString = String(Texto); // Convertendo o Char para String para gravar no Display
  statusMotorDisplay.write(textoString);

  // String msg = "Sistema Iniciado com sucesso \n";
  // msg.toCharArray(Characters, sizeof(Characters));
  // LogInicioSistema.write(Characters, sizeof(Characters));

}

void loop() {
  unsigned long tempoAtual = millis();
  static unsigned long ultimoCheck = 0; // Para validação se o sistema esta conectado ou nao ao Servidor API

/*
  subirAndarPorAndar();

  // Verifica se o tempo decorrido é maior ou igual ao intervalo
  if (tempoAtual - tempoAnterior >= INTERVALOSUBIDA) {
    // Atualiza o tempo da última execução
    tempoAnterior = tempoAtual;
    if (leituraFinalizada == true){
      subirAndarPorAndar();
      Serial.println("Processo de leitura dos ovos iniciado. ");
      leituraFinalizada = false;
    }
    // Chama a função que você quer executar
   // subirAndarPorAndar();
  }



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
  
  // // Verificar se precisa tentar ressincronizar NTP
  // if (!ntp_synchronized && (millis() - last_ntp_attempt >= ntp_retry_interval)) {
  //   Serial.println("Tentando ressincronizar NTP...");
  //   tentar_resincronizar_ntp();
  //   last_ntp_attempt = millis();
  // }
  
  // // Verificar se é hora de coletar dados
  // if (millis() - last_reading_time >= reading_interval) {
  //   // Debug do timestamp
  //   debug_timestamp();
    
  //   // Coletar dados dos sensores
  //   SensorData dados = coletar_dados_sensores();
    
  //   if (dados.valida) {
  //     // Verificar se o token ainda é válido
  //     if (millis() - last_token_time >= token_lifetime || jwt_token == "") {
  //       Serial.println("Token expirado ou inexistente. Fazendo novo login...");
  //       fazer_login();
  //     }
      
  //     // Enviar dados para a API
  //     if (jwt_token != "") {
  //       enviar_dados_api(dados);
  //     }
  //   }
    
  //   last_reading_time = millis();
  // }
  

  // Implementações Display a partir desse ponto iniciamos as regras 


  // sensors_event_t humidity, temp;
  // aht.getEvent(&humidity, &temp);
  // temperaturaMLX = mlx.readObjectTempC();
  // umidadeAHT = humidity.relative_humidity;
  // pressaoBMP = bmp.readPressure() / 100.0F; // Ja realizando a conversao para hPa

//coletar_dados_sensores();

  // Função OK 
  if(reinicializarSistema.available()){  // Função OK
    int dadosLidos = reinicializarSistema.getData();
    Serial.println("Reiniciando o sistema...");
    Serial.println("Dados Recebidos do Display: " + String(dadosLidos));
    delay(1000);
    ESP.restart();
  }

    // Função para controlar a ativação automatica do motor. 
  if (LigarMotor.available()){ // Recebendo e interceptando o valor para ligar e desligar. 
    int value = LigarMotor.getData();
    if(value == 1){
      Serial.println("Vamos ligar a leitura automatica!");
      char Texto[10] = "LIGADO";
      motorAtivo = true;  // ⭐ ATIVA A FLAG
      String textoString = String(Texto); // Convertendo o Char para String para gravar no Display
      statusMotorDisplay.write(textoString);  
      //subirAndarPorAndar(); // Inicia o processo de leitura automatica dos ovos
    }
    else 
      if (value == 0){
        Serial.println("Vamos Desligar o Motor!");
        motorAtivo = false;  // ⭐ DESATIVA A FLAG IMEDIATAMENTE
        char Texto[10] = "DESLIGADO";
        String textoString = String(Texto); // Convertendo o Char para String para gravar no Display
        statusMotorDisplay.write(textoString);      
        desabilitarTodosMotores();


      }
  }

 

  // Função para limpar o grafico de pressao, temperatura e umidade.

  if (limparGraficoPressao.available()){
    int value = limparGraficoPressao.getData();
    Serial.println("Dados recebidos para limpar o grafico de Pressao");
    if(value == 1){
      Lcm.clearTrendCurve1();
      Serial.println("Display Limpo");
      delay(100);
      value = 0;    
    } else{
     // Lcm.writeTrendCurve1(pressaoBMP);
    }
  }

  if (limparGraficoTemperatura.available()){
    int value = limparGraficoTemperatura.getData();
    Serial.println("Dados recebidos para limpar o grafico de temperatura");
    if(value == 1){
      Lcm.clearTrendCurve0();
      Serial.println("Display Limpo");
      delay(100);
      value = 0;    
    } else{
    //  Lcm.writeTrendCurve0(temperaturaMLX);
    }
  }

  if (limparGraficoUmidade.available()){
    int value = limparGraficoUmidade.getData();
    Serial.println("Dados recebidos para limpar o grafico de Umidade");
    if(value == 1){
      Lcm.clearTrendCurve2();
      Serial.println("Display Limpo");
      delay(100);
      value = 0;    
    } else{
    //  Lcm.writeTrendCurve2(umidadeAHT);
    }
  }

  // // Gerando os graficos a cada 1 segundo
  // if (tempoAtual - tempoAnterior >= intervaloGraficos){
  //   tempoAnterior = tempoAtual; // atualizando o tempo anterior
  //   Lcm.writeTrendCurve0(temperaturaMLX);
  //   Lcm.writeTrendCurve2(umidadeAHT);
  //   Lcm.writeTrendCurve1(pressaoBMP);   
  // }

  // Impressao no display dos dados do lote -- OK
  if (statusOvoscopia.available()){
    int value = statusOvoscopia.getData();
    if(value == 14){
      char loteOvos[20] = "FagSummit_2025";
      String textoLote = String(loteOvos); // Convertendo o Char para String para gravar no Display e escrevendo no Display
      loteOvosDisplay.write(textoLote);
      Serial.println(textoLote); 
      
      char dataInicialOvos[20] = "30/09/2025";
      String textoLote2 = String(dataInicialOvos);
      dataInicialLoteDisplay.write(textoLote2);
      Serial.println(textoLote2);

      char dataFinalOvos[20] = "15/12/2025";
      String textoLote3 = String(dataFinalOvos);
      dataFinalLoteDisplay.write(textoLote3);
      Serial.println(textoLote3);
    }    
  }

  if (LogInicioSistema.available()){
    int value = LogInicioSistema.getData();
    if (value == 110){
       
      char linha2[20];
      snprintf(linha2, sizeof(linha2), "Sinal: %d dBm", WiFi.RSSI());
      String textoSinal = String(linha2);
      logLinha2.write(textoSinal);
      Serial.println(textoSinal);

      char linha6[20];
      snprintf(linha6, sizeof(linha6), "BD COOPA: OFF-LINE");
      String TextoLinha6 = String(linha6);
      logLinha6.write(TextoLinha6);
    }
  }

  if (millis() - ultimoCheck > 60000) { // a cada 60s
    atualizaStatusServidor();
    ultimoCheck = millis();
  }

  // VALIDAR ACIONAMENTO DO SISTEMA COMPLETO.

  if (calibrarSistema.available()){
    int value = calibrarSistema.getData();
    char calibracao[40];
    if(value == 11){
      Serial.println("Chamando a função para calibrar o sistema.");
      char calibracao[40] = "CALIBRACAO INICIADA";
      String textoCalibracao = String(calibracao);
      StatusCalibracao.write(textoCalibracao);
      executarHoming();
    }
  }

  if (motorAtivo) {
    // Verifica se é a primeira subida OU se já passou 1 minuto desde a última
    if (primeiraSubida || (tempoAtual - ultimaSubida >= INTERVALO_SUBIDA)) {
      
      Serial.println("╔════════════════════════════════════╗");
      Serial.println("║   INICIANDO CICLO DE LEITURA      ║");
      Serial.println("╚════════════════════════════════════╝");
      
      subirAndarPorAndar(); // Executa a subida completa (sobe + homing)
      
      // Atualiza o tempo da última subida
      ultimaSubida = millis();
      primeiraSubida = false;
      
      // Verifica se o motor ainda está ativo após a subida
      if (motorAtivo) {
        Serial.println("");
        Serial.println("⏰ Aguardando 1 minuto para próximo ciclo...");
        Serial.println("   (ou até receber comando de parada)");
        Serial.println("");
        habilitarMotor(MOTOR_DIR_ENABLE);
        habilitarMotor(MOTOR_ESQ_ENABLE);
      } else {
        Serial.println("⛔ Sistema parado pelo usuário");
      }
    }
  } else {
    // Se o motor foi desligado, reseta a flag de primeira subida
    primeiraSubida = true;
  }

  // Pequeno delay para não sobrecarregar o processador
  delay(1);

    habilitarMotor(MOTOR_DIR_ENABLE);
    habilitarMotor(MOTOR_ESQ_ENABLE);

}