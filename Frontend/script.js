// Configuração da API
const API_BASE_URL = "http://147.79.104.68:5001"; // URL corrigida

// Elementos do DOM
let loginForm, errorMessage, logoutBtn;

// Verifica parâmetros de URL para mensagem de logout
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has("logout")) {
  const logoutMessage = document.getElementById("logoutMessage");
  if (logoutMessage) {
    logoutMessage.textContent = "Você saiu do sistema com sucesso.";
    logoutMessage.style.display = "block";
    window.history.replaceState({}, document.title, window.location.pathname);
  }
}

// Função para exibir mensagens de erro
function showError(message, isLoginError = false) {
  if (!errorMessage) errorMessage = document.getElementById("errorMessage");
  if (!errorMessage) return;

  errorMessage.textContent = message;
  errorMessage.style.display = "block";
  errorMessage.className = isLoginError
    ? "error-message login-error"
    : "error-message";

  setTimeout(() => {
    errorMessage.style.display = "none";
  }, 5000);
}

// Função para fazer logout
async function handleLogout() {
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.textContent = "Saindo...";
    logoutBtn.disabled = true;
  }

  // Limpa o token após um pequeno delay para feedback visual
  await new Promise((resolve) => setTimeout(resolve, 300));
  localStorage.removeItem("embryotech_token");

  // Redireciona apenas uma vez
  window.location.href = "index.html?logout=success";
}

// Função principal de inicialização
function init() {
  // Verifica se estamos na página de login
  if (
    window.location.pathname.endsWith("index.html") ||
    window.location.pathname === "/"
  ) {
    setupLoginPage();
  }
  // Verifica se estamos na página de dashboard
  else if (window.location.pathname.endsWith("dashboard.html")) {
    setupDashboardPage();
  }
}

// Configura a página de login
function setupLoginPage() {
  loginForm = document.getElementById("loginForm");
  if (!loginForm) return;

  // Verifica se já está logado (redireciona se positivo)
  const token = localStorage.getItem("embryotech_token");
  if (token) {
    window.location.href = "dashboard.html";
    return;
  }

  // Configura o evento de login
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const submitBtn = loginForm.querySelector('button[type="submit"]');

    // Validação básica no cliente
    if (!username || !password) {
      showError("Por favor, preencha todos os campos.", true);
      return;
    }

    // Feedback visual
    const originalBtnText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = "Autenticando...";

    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("embryotech_token", data.token);
        window.location.href = "dashboard.html";
      } else {
        handleLoginError(response.status);
      }
    } catch (error) {
      showError(
        "Não foi possível conectar ao servidor. Verifique sua conexão.",
        true
      );
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalBtnText;
    }
  });
}

// Trata erros de login
function handleLoginError(status) {
  switch (status) {
    case 400:
      showError("Nome de usuário e senha são obrigatórios", true);
      break;
    case 401:
      showError("Usuário ou senha incorretos", true);
      break;
    case 500:
      showError("Problema no servidor. Tente novamente mais tarde.", true);
      break;
    default:
      showError("Erro ao fazer login", true);
  }
}

// Configura a página de dashboard
function setupDashboardPage() {
  // Verifica autenticação
  const token = localStorage.getItem("embryotech_token");
  if (!token) {
    handleLogout();
    return;
  }

  // Configura o botão de logout
  logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      handleLogout();
    });
  }

  // Carrega as leituras
  loadReadings();
}

// Função para carregar as leituras (mantida como no original)
async function loadReadings() {
  try {
    const token = localStorage.getItem("embryotech_token");
    const response = await fetch(`${API_BASE_URL}/leituras`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      if (response.status === 401) handleLogout();
      throw new Error("Erro ao carregar leituras");
    }

    const readings = await response.json();
    readings.sort(
      (a, b) => new Date(b.data_inicial) - new Date(a.data_inicial)
    );

    displayLastReading(readings[0]);
    displayReadingsList(readings);
  } catch (error) {
    console.error("Erro:", error);
    showError("Erro ao carregar leituras");
  }
}

// Funções de exibição (mantidas como no original)
function displayLastReading(reading) {
  const container = document.getElementById("lastReadingContainer");
  if (!container) return;

  container.innerHTML = reading
    ? `
        <div class="reading-details">
            <div class="reading-row"><span>Temperatura:</span><span class="reading-value">${
              reading.temperatura
            } °C</span></div>
            <div class="reading-row"><span>Umidade:</span><span class="reading-value">${
              reading.umidade
            }%</span></div>
            <div class="reading-row"><span>Pressão:</span><span class="reading-value">${
              reading.pressao
            } atm</span></div>
            <div class="reading-row"><span>Lote:</span><span class="reading-lote">${
              reading.lote
            }</span></div>
            <div class="reading-row"><span>Período:</span><span class="reading-date">${formatDate(
              reading.data_inicial
            )} até ${formatDate(reading.data_final)}</span></div>
        </div>
    `
    : "<p>Nenhuma leitura encontrada</p>";
}

function displayReadingsList(readings) {
  const container = document.getElementById("readingsListContainer");
  if (!container) return;

  container.innerHTML = readings?.length
    ? readings
        .map(
          (reading) => `
        <div class="reading-item">
            <div>
                <div class="reading-row">
                    <span>${formatDate(reading.data_inicial)}</span>
                    <span class="reading-lote">${reading.lote}</span>
                </div>
                <div class="reading-row">
                    <span>${reading.temperatura} °C</span>
                    <span>${reading.umidade}%</span>
                    <span>${reading.pressao} atm</span>
                </div>
            </div>
            <button class="details-btn" data-id="${
              reading.id
            }">Detalhes</button>
        </div>
    `
        )
        .join("")
    : "<p>Nenhuma leitura encontrada</p>";

  document.querySelectorAll(".details-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      showReadingDetails(e.target.getAttribute("data-id"));
    });
  });
}

function formatDate(dateString) {
  const options = {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  };
  return new Date(dateString).toLocaleDateString("pt-BR", options);
}

function showReadingDetails(readingId) {
  alert(`Detalhes da leitura ${readingId}`);
}

// Inicializa a aplicação quando o DOM estiver pronto
document.addEventListener("DOMContentLoaded", init);
