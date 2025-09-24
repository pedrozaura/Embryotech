#!/usr/bin/env python3
"""
Script de teste da API Embryotech com Swagger
Testa todos os endpoints principais e valida as respostas
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configurações
BASE_URL = "http://localhost:5001"
API_BASE = f"{BASE_URL}/api"

class EmbryotechAPITester:
    def __init__(self):
        self.base_url = API_BASE
        self.token = None
        self.session = requests.Session()
        self.test_user = {
            "username": "test_user_api",
            "email": "test@embryotech.com",
            "password": "testpass123"
        }
        self.admin_user = {
            "username": "admin",
            "password": "admin123"
        }
        
    def log(self, message, level="INFO"):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def make_request(self, method, endpoint, data=None, params=None, headers=None):
        """Fazer requisição HTTP com tratamento de erro"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
            
        if self.token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {self.token}'
            
        headers['Content-Type'] = 'application/json'
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
                
            return response
        except Exception as e:
            self.log(f"Erro na requisição: {str(e)}", "ERROR")
            return None
    
    def test_api_status(self):
        """Testar endpoint de status da API"""
        self.log("🔍 Testando status da API...")
        
        response = self.make_request('GET', '/')
        
        if response and response.status_code == 200:
            data = response.json()
            self.log(f"✅ API Status OK - Porta: {data.get('PORTA', 'N/A')}")
            self.log(f"   Swagger UI: {data.get('swagger_ui', 'N/A')}")
            return True
        else:
            self.log(f"❌ Falha no status da API - Status: {response.status_code if response else 'N/A'}", "ERROR")
            return False
    
    def test_user_registration(self):
        """Testar registro de usuário"""
        self.log("👤 Testando registro de usuário...")
        
        response = self.make_request('POST', '/register', data=self.test_user)
        
        if response and response.status_code in [201, 400]:  # 400 se usuário já existe
            if response.status_code == 201:
                self.log("✅ Usuário registrado com sucesso")
                return True
            else:
                data = response.json()
                if "already exists" in data.get('message', ''):
                    self.log("ℹ️  Usuário já existe (OK para testes)")
                    return True
                else:
                    self.log(f"❌ Erro no registro: {data.get('message', 'N/A')}", "ERROR")
                    return False
        else:
            self.log(f"❌ Falha no registro - Status: {response.status_code if response else 'N/A'}", "ERROR")
            return False
    
    def test_user_login(self):
        """Testar login e obter token"""
        self.log("🔐 Testando login...")
        
        # Tentar login com usuário de teste primeiro
        response = self.make_request('POST', '/login', data={
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        })
        
        # Se falhar, tentar com admin
        if not response or response.status_code != 200:
            self.log("ℹ️  Tentando login com admin...")
            response = self.make_request('POST', '/login', data=self.admin_user)
        
        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            if self.token:
                self.log("✅ Login realizado com sucesso")
                self.log(f"   Token: {self.token[:20]}...")
                return True
            else:
                self.log("❌ Token não retornado", "ERROR")
                return False
        else:
            self.log(f"❌ Falha no login - Status: {response.status_code if response else 'N/A'}", "ERROR")
            return False
    
    def test_create_leitura(self):
        """Testar criação de leitura"""
        self.log("📊 Testando criação de leitura...")
        
        leitura_data = {
            "temperatura": 37.8,
            "umidade": 65.5,
            "pressao": 1013.2,
            "lote": "LOTE_TEST_API",
            "data_inicial": datetime.now().isoformat(),
            "data_final": datetime.now().isoformat()
        }
        
        response = self.make_request('POST', '/leituras', data=leitura_data)
        
        if response and response.status_code == 201:
            data = response.json()
            self.log(f"✅ Leitura criada: {data.get('message', 'N/A')}")
            return True
        else:
            self.log(f"❌ Falha na criação - Status: {response.status_code if response else 'N/A'}", "ERROR")
            if response:
                self.log(f"   Erro: {response.json().get('message', 'N/A')}", "ERROR")
            return False
    
    def test_list_leituras(self):
        """Testar listagem de leituras"""
        self.log("📋 Testando listagem de leituras...")
        
        response = self.make_request('GET', '/leituras')
        
        if response and response.status_code == 200:
            data = response.json()
            self.log(f"✅ Leituras encontradas: {len(data)}")
            return True
        else:
            self.log(f"❌ Falha na listagem - Status: {response.status_code if response else 'N/A'}", "ERROR")
            return False
    
    def test_create_parametro(self):
        """Testar criação de parâmetro (requer admin)"""
        self.log("⚙️  Testando criação de parâmetro...")
        
        parametro_data = {
            "empresa": "Embryotech Test Inc.",
            "lote": "LOTE_TEST_API",
            "temp_ideal": 37.8,
            "umid_ideal": 65.0,
            "pressao_ideal": 1013.2,
            "lumens": 1200,
            "id_sala": "SALA_TEST",
            "estagio_ovo": "teste_api"
        }
        
        response = self.make_request('POST', '/parametros', data=parametro_data)
        
        if response and response.status_code in [201, 403]:  # 403 se não for admin
            if response.status_code == 201:
                self.log("✅ Parâmetro criado com sucesso")
                return True
            else:
                self.log("ℹ️  Acesso negado - usuário não é admin (esperado para usuário comum)")
                return True
        else:
            self.log(f"❌ Falha na criação do parâmetro - Status: {response.status_code if response else 'N/A'}", "ERROR")
            return False
    
    def test_list_empresas(self):
        """Testar listagem de empresas"""
        self.log("🏢 Testando listagem de empresas...")
        
        response = self.make_request('GET', '/empresas')
        
        if response and response.status_code in [200, 403]:  # 403 se não for admin
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Empresas encontradas: {len(data)}")
                return True
            else:
                self.log("ℹ️  Acesso negado - usuário não é admin (esperado para usuário comum)")
                return True
        else:
            self.log(f"❌ Falha na listagem - Status: {response.status_code if response else 'N/A'}", "ERROR")
            return False
    
    def test_list_lotes(self):
        """Testar listagem de lotes"""
        self.log("📦 Testando listagem de lotes...")
        
        response = self.make_request('GET', '/lotes')
        
        if response and response.status_code == 200:
            data = response.json()
            self.log(f"✅ Lotes encontrados: {len(data)}")
            return True
        else:
            self.log(f"❌ Falha na listagem - Status: {response.status_code if response else 'N/A'}", "ERROR")
            return False
    
    def test_get_logs(self):
        """Testar consulta de logs"""
        self.log("📝 Testando consulta de logs...")
        
        response = self.make_request('GET', '/logs', params={'limite': 10})
        
        if response and response.status_code in [200, 403]:  # 403 se não for admin
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Logs encontrados: {len(data)}")
                return True
            else:
                self.log("ℹ️  Acesso negado - usuário não é admin (esperado para usuário comum)")
                return True
        else:
            self.log(f"❌ Falha na consulta - Status: {response.status_code if response else 'N/A'}", "ERROR")
            return False
    
    def test_logout(self):
        """Testar logout"""
        self.log("🚪 Testando logout...")
        
        response = self.make_request('POST', '/logout')
        
        if response and response.status_code == 200:
            self.log("✅ Logout realizado com sucesso")
            self.token = None
            return True
        else:
            self.log(f"❌ Falha no logout - Status: {response.status_code if response else 'N/A'}", "ERROR")
            return False
    
    def test_swagger_ui(self):
        """Testar se a interface do Swagger está acessível"""
        self.log("📚 Testando interface do Swagger...")
        
        try:
            swagger_response = requests.get(f"{BASE_URL}/swagger/")
            if swagger_response.status_code == 200:
                self.log("✅ Interface Swagger acessível")
                self.log(f"   URL: {BASE_URL}/swagger/")
                return True
            else:
                self.log(f"❌ Interface Swagger não acessível - Status: {swagger_response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Erro ao acessar Swagger: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Executar todos os testes"""
        self.log("🚀 Iniciando testes da API Embryotech...")
        self.log("="*60)
        
        tests = [
            ("API Status", self.test_api_status),
            ("Swagger UI", self.test_swagger_ui),
            ("Registro de Usuário", self.test_user_registration),
            ("Login", self.test_user_login),
            ("Criar Leitura", self.test_create_leitura),
            ("Listar Leituras", self.test_list_leituras),
            ("Criar Parâmetro", self.test_create_parametro),
            ("Listar Empresas", self.test_list_empresas),
            ("Listar Lotes", self.test_list_lotes),
            ("Consultar Logs", self.test_get_logs),
            ("Logout", self.test_logout),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n📋 Executando: {test_name}")
            try:
                result = test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
                time.sleep(0.5)  # Pequena pausa entre testes
            except Exception as e:
                self.log(f"❌ Erro inesperado em {test_name}: {str(e)}", "ERROR")
                failed += 1
        
        self.log("\n" + "="*60)
        self.log(f"🎯 RESULTADOS FINAIS:")
        self.log(f"   ✅ Testes passou: {passed}")
        self.log(f"   ❌ Testes falhou: {failed}")
        self.log(f"   📊 Total: {passed + failed}")
        
        if failed == 0:
            self.log("🎉 Todos os testes passaram! API funcionando corretamente.")
            return True
        else:
            self.log("⚠️  Alguns testes falharam. Verifique os logs acima.")
            return False

def main():
    """Função principal"""
    print("🔬 Embryotech API Tester v2.0")
    print("Testando API com documentação Swagger integrada")
    print("="*60)
    
    tester = EmbryotechAPITester()
    
    try:
        # Verificar se a API está rodando
        print(f"🔗 Testando conectividade com {BASE_URL}")
        test_response = requests.get(f"{BASE_URL}/api/", timeout=5)
        if test_response.status_code != 200:
            print(f"❌ API não está respondendo. Verifique se está rodando na porta 5001")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar à API.")
        print("   Verifique se a aplicação está rodando com: python app.py")
        sys.exit(1)
    
    # Executar todos os testes
    success = tester.run_all_tests()
    
    print(f"\n📚 Para ver a documentação completa, acesse:")
    print(f"   {BASE_URL}/swagger/")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()