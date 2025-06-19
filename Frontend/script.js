// Configuração da API
const API_BASE_URL = "http:147.79.104.68:5001/"; //URL DA API de Produção
// Elementos do DOM
let loginForm, errorMessage, logoutBtn;

// Verifica se estamos na página de login ou dashboard
if (document.querySelector("#loginForm")) {
  // Elementos da página de login
  loginForm = document.getElementById("loginForm");
  errorMessage = document.getElementById("errorMessage");

  // Evento de submit do formulário de login
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    // Validação básica no cliente
    if (!username || !password) {
      showError("Por favor, preencha todos os campos.", true);
      return;
    }

    const submitBtn = loginForm.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.textContent;

    // Mostra feedback visual
    submitBtn.disabled = true;
    submitBtn.textContent = "Autenticando...";
    submitBtn.style.opacity = "1";

    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("embryotech_token", data.token);
        window.location.href = "dashboard.html";
      } else {
        // Mensagens personalizadas baseadas no status da resposta
        let errorMsg = "Erro ao fazer login";

        if (response.status === 400) {
          errorMsg = "Nome de usuário e senha são obrigatórios";
        } else if (response.status === 401) {
          errorMsg = "Usuário ou senha incorretos";
        } else if (response.status === 500) {
          errorMsg = "Problema no servidor. Tente novamente mais tarde.";
        }

        showError(errorMsg, true);
      }
    } catch (error) {
      showError(
        "Não foi possível conectar ao servidor. Verifique sua conexão.",
        true
      );
    } finally {
      // Restaura o botão
      submitBtn.disabled = false;
      submitBtn.textContent = originalBtnText;
      submitBtn.style.opacity = "1";
    }
  });

  // Verifica se o usuário está autenticado
  const token = localStorage.getItem("embryotech_token");
  if (!token) {
    window.location.href = "index.html";
  } else {
    // Carrega os dados das leituras
    loadReadings();
  }
}

// Função para exibir mensagens de erro
function showError(message, isLoginError = false) {
  errorMessage.textContent = message;
  errorMessage.style.display = "block";

  // Adiciona classe específica para erros de login
  if (isLoginError) {
    errorMessage.classList.add("login-error");
  } else {
    errorMessage.classList.remove("login-error");
  }

  setTimeout(() => {
    errorMessage.style.display = "none";
  }, 5000);
}

// Função para carregar as leituras
async function loadReadings() {
  try {
    const token = localStorage.getItem("embryotech_token");

    // Busca todas as leituras
    const response = await fetch(`${API_BASE_URL}/leituras`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token inválido, faz logout
        localStorage.removeItem("embryotech_token");
        window.location.href = "index.html";
        return;
      }
      throw new Error("Erro ao carregar leituras");
    }

    const readings = await response.json();

    // Ordena as leituras pela data mais recente primeiro
    readings.sort(
      (a, b) => new Date(b.data_inicial) - new Date(a.data_inicial)
    );

    // Exibe a última leitura
    displayLastReading(readings[0]);

    // Exibe a lista de leituras
    displayReadingsList(readings);
  } catch (error) {
    console.error("Erro:", error);
    alert("Erro ao carregar leituras");
  }
}

// Função para exibir a última leitura
function displayLastReading(reading) {
  const container = document.getElementById("lastReadingContainer");

  if (!reading) {
    container.innerHTML = "<p>Nenhuma leitura encontrada</p>";
    return;
  }

  container.innerHTML = `
        <div class="reading-details">
            <div class="reading-row">
                <span>Temperatura:</span>
                <span class="reading-value">${reading.temperatura} °C</span>
            </div>
            <div class="reading-row">
                <span>Umidade:</span>
                <span class="reading-value">${reading.umidade}%</span>
            </div>
            <div class="reading-row">
                <span>Pressão:</span>
                <span class="reading-value">${reading.pressao} atm</span>
            </div>
            <div class="reading-row">
                <span>Lote:</span>
                <span class="reading-lote">${reading.lote}</span>
            </div>
            <div class="reading-row">
                <span>Período:</span>
                <span class="reading-date">
                    ${formatDate(reading.data_inicial)} até ${formatDate(
    reading.data_final
  )}
                </span>
            </div>
        </div>
    `;
}

// Função para exibir a lista de leituras
function displayReadingsList(readings) {
  const container = document.getElementById("readingsListContainer");

  if (!readings || readings.length === 0) {
    container.innerHTML = "<p>Nenhuma leitura encontrada</p>";
    return;
  }

  let html = "";

  readings.forEach((reading) => {
    html += `
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
        `;
  });

  container.innerHTML = html;

  // Adiciona eventos aos botões de detalhes
  document.querySelectorAll(".details-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const readingId = e.target.getAttribute("data-id");
      showReadingDetails(readingId);
    });
  });
}

// Função para formatar data
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

// Função para mostrar detalhes de uma leitura (pode ser implementada posteriormente)
function showReadingDetails(readingId) {
  alert(`Detalhes da leitura ${readingId}`);
  // Aqui você pode implementar uma modal ou outra página com mais detalhes
}
