#!/bin/bash

# Script para executar todos os testes da aplicação Embryotech

echo "=========================================="
echo "  EMBRYOTECH - Execução de Testes"
echo "=========================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se pytest está instalado
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}[ERRO]${NC} pytest não está instalado!"
    echo "Instale as dependências com: pip install -r requirements-test.txt"
    exit 1
fi

echo -e "${YELLOW}[INFO]${NC} Iniciando testes..."
echo ""

# Executar testes com coverage
echo -e "${YELLOW}[INFO]${NC} Executando testes com cobertura de código..."
pytest tests/ \
    --verbose \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=xml \
    --junit-xml=test-results.xml

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}[SUCESSO]${NC} Todos os testes passaram!"
    echo ""
    echo "Relatórios gerados:"
    echo "  - HTML: htmlcov/index.html"
    echo "  - XML: coverage.xml"
    echo "  - JUnit: test-results.xml"
    echo ""
    echo "Para ver o relatório HTML, abra: htmlcov/index.html"
else
    echo ""
    echo -e "${RED}[FALHA]${NC} Alguns testes falharam!"
    exit 1
fi
