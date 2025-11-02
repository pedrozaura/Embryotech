"""
Script de Validação da Estrutura de Testes
===========================================

Execute este script no diretório Backend para verificar se tudo está configurado corretamente.

Uso: python validar_estrutura.py
"""

import os
import sys
from pathlib import Path

# Cores para output (funciona no Windows 10+)
try:
    os.system('color')
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
except:
    GREEN = YELLOW = RED = BLUE = RESET = ''

def check_file(filepath, required=True):
    """Verifica se um arquivo existe"""
    exists = os.path.exists(filepath)
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    req_text = "(obrigatório)" if required else "(opcional)"
    print(f"  {status} {filepath} {req_text}")
    return exists

def check_directory(dirpath, required=True):
    """Verifica se um diretório existe"""
    exists = os.path.isdir(dirpath)
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    req_text = "(obrigatório)" if required else "(opcional)"
    print(f"  {status} {dirpath}/ {req_text}")
    return exists

def check_import(module_name):
    """Verifica se um módulo pode ser importado"""
    try:
        __import__(module_name)
        print(f"  {GREEN}✓{RESET} {module_name}")
        return True
    except ImportError as e:
        print(f"  {RED}✗{RESET} {module_name} - {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print(f"{BLUE}VALIDAÇÃO DA ESTRUTURA DE TESTES - EMBRYOTECH{RESET}")
    print("="*60 + "\n")

    errors = []
    warnings = []

    # 1. Verificar diretório atual
    print(f"{YELLOW}1. Verificando diretório atual...{RESET}")
    current_dir = os.getcwd()
    print(f"   Diretório: {current_dir}")
    
    if not os.path.exists('app.py'):
        errors.append("Você não está no diretório Backend (app.py não encontrado)")
        print(f"   {RED}✗ Você deve estar no diretório Backend (onde está app.py){RESET}")
    else:
        print(f"   {GREEN}✓ Diretório correto!{RESET}")
    print()

    # 2. Verificar arquivos principais
    print(f"{YELLOW}2. Verificando arquivos principais...{RESET}")
    main_files = ['app.py', 'models.py', 'config.py', 'extensions.py', 'logging_utils.py']
    for file in main_files:
        if not check_file(file, required=True):
            errors.append(f"Arquivo principal faltando: {file}")
    print()

    # 3. Verificar arquivos de configuração de teste
    print(f"{YELLOW}3. Verificando arquivos de configuração de teste...{RESET}")
    test_config_files = ['test_config.py', 'pytest.ini', 'requirements-test.txt']
    for file in test_config_files:
        if not check_file(file, required=True):
            errors.append(f"Arquivo de config de teste faltando: {file}")
    print()

    # 4. Verificar diretório de testes
    print(f"{YELLOW}4. Verificando diretório de testes...{RESET}")
    if not check_directory('tests', required=True):
        errors.append("Diretório tests/ não encontrado")
    else:
        test_files = [
            'tests/__init__.py',
            'tests/conftest.py',
            'tests/test_models.py',
            'tests/test_auth.py',
            'tests/test_parametros_api.py',
            'tests/test_leituras_api.py',
            'tests/test_logging.py'
        ]
        for file in test_files:
            if not check_file(file, required=True):
                errors.append(f"Arquivo de teste faltando: {file}")
    print()

    # 5. Verificar dependências
    print(f"{YELLOW}5. Verificando dependências instaladas...{RESET}")
    dependencies = ['pytest', 'flask', 'sqlalchemy']
    for dep in dependencies:
        if not check_import(dep):
            errors.append(f"Dependência faltando: {dep}")
    print()

    # 6. Verificar se pode importar módulos do projeto
    print(f"{YELLOW}6. Verificando imports do projeto...{RESET}")
    sys.path.insert(0, current_dir)
    project_modules = ['models', 'config', 'extensions', 'logging_utils']
    for module in project_modules:
        if not check_import(module):
            errors.append(f"Não foi possível importar: {module}")
    print()

    # 7. Verificar estrutura de banco de dados
    print(f"{YELLOW}7. Verificando modelos de banco de dados...{RESET}")
    try:
        from models import User, Parametro, Leitura, Log
        print(f"  {GREEN}✓{RESET} User")
        print(f"  {GREEN}✓{RESET} Parametro")
        print(f"  {GREEN}✓{RESET} Leitura")
        print(f"  {GREEN}✓{RESET} Log")
    except ImportError as e:
        errors.append(f"Erro ao importar modelos: {str(e)}")
        print(f"  {RED}✗{RESET} Erro ao importar modelos")
    print()

    # 8. Verificar variáveis de ambiente (opcional)
    print(f"{YELLOW}8. Verificando variáveis de ambiente (opcional)...{RESET}")
    env_file = check_file('.env', required=False) or check_file('_env', required=False)
    if not env_file:
        warnings.append("Arquivo .env ou _env não encontrado (opcional para testes)")
    print()

    # Resumo
    print("="*60)
    print(f"{BLUE}RESUMO DA VALIDAÇÃO{RESET}")
    print("="*60)
    print()

    if not errors and not warnings:
        print(f"{GREEN}✓ PERFEITO! Tudo está configurado corretamente!{RESET}")
        print()
        print(f"{BLUE}Próximos passos:{RESET}")
        print("  1. Execute os testes: pytest tests/ -v")
        print("  2. Veja a cobertura: pytest tests/ --cov=. --cov-report=html")
        print("  3. Abra o relatório: start htmlcov\\index.html")
        print()
        return 0
    
    if warnings:
        print(f"{YELLOW}⚠ AVISOS ({len(warnings)}):{RESET}")
        for warning in warnings:
            print(f"  - {warning}")
        print()

    if errors:
        print(f"{RED}✗ ERROS ENCONTRADOS ({len(errors)}):{RESET}")
        for error in errors:
            print(f"  - {error}")
        print()
        print(f"{BLUE}Correções necessárias:{RESET}")
        print("  1. Certifique-se de estar no diretório Backend")
        print("  2. Execute: pip install -r requirements-test.txt")
        print("  3. Verifique se os arquivos de teste estão em Backend/tests/")
        print("  4. Consulte GUIA_INSTALACAO.md para instruções detalhadas")
        print()
        return 1

    return 0

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Validação cancelada pelo usuário{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Erro inesperado: {str(e)}{RESET}")
        sys.exit(1)
