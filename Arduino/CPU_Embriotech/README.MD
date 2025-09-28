📋 Resumo da configuração atual de pinos:
´´´
Componente GPIOFunção Comunicação
Serial 16, 17 LIVRE para Serial2
Indicadores de Andar 4, 5 Fins de curso do
mecanismoTorres 34, 35, 36, 39 Fins de curso superior/inferior
Motor Centro 18, 19 Fins de curso do motor central
Drivers TB6600 25-27, 32-33-14, 12-13-15 STEP, DIR, ENABLE
´´´

O código está pronto para uso! Você pode descomentar a linha da Serial2 no setup() quando quiser ativar a comunicação serial nas GPIOs 16 e 17.
