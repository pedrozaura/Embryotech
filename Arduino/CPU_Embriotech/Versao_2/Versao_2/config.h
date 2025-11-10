/*

  Posição Fios Drivers, Motores.
  Motor Sistema Central de leitura fechamanto1 (Vermelho e Azul) Fechamento2 (Preto e Verde)
  Motor Torre Direita fechamanto1 (Laranja e Azul) Fechamento2 (Marrom e Verde)
  Motor Torre Esquerda fechamanto1 (Laranja e Azul) Fechamento2 (Marrom e Verde)

*/

//Superiores Amarelos
//Inferiores Laranjas


#ifndef CONFIG_H
#define CONFIG_H

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

#define SENSOR_OPTICO_OVO 23
#define pinoLDR 2

// Configurando portas de Saidas para Serial2 utilizado no Display.
#define RXD2 16
#define TXD2 17

#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <Adafruit_BMP280.h>
#include <Adafruit_AHTX0.h>
#include "Wire.h"
#include <UnicViewAD.h>
#include "esp_system.h"
#include <WiFiClientSecure.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <EEPROM.h>
#include <WebServer.h>


const char* ssid = "Outside";
const char* password = "Outside@123456";

// ==================== CONFIGURAÇÕES DA API ====================
const char* api_base_url = "https://embryo.outsideagro.tech/api";

// Você DEVE criar este usuário na sua API primeiro!
const char* username = "processador";     // Nome do usuário para o ESP32
const char* user_password = "Outside@123456";  // Senha do usuário para o ESP32

const char* lote_id = "FagSummit2025"; // Identificador do lote de ovos

const char* dataFinalLote = "2025-12-15T23:59:59"; // Data final do lote de ovos deve manter esse formato que é o do banco de dados. 




#endif