// script.js completo com funcionalidade de parâmetros por empresa e lote

const API_BASE_URL = "http://172.16.1.22:5001";

let loginForm, errorMessage, logoutBtn;

const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has("logout")) {
  const logoutMessage = document.getElementById("logoutMessage");
  if (logoutMessage) {
    logoutMessage.textContent = "Você saiu do sistema com sucesso.";
    logoutMessage.style.display = "block";
    window.history.replaceState({}, document.title, window.location.pathname);
  }
}

function showMessage(message, type = "error", isLoginError = false) {
  if (!errorMessage) errorMessage = document.getElementById("errorMessage");
  if (!errorMessage) return;

  errorMessage.textContent = message;
  errorMessage.style.display = "block";

  // Remove todas as classes existentes
  errorMessage.className = "";

  // Adiciona as classes apropriadas
  if (type === "error") {
    errorMessage.classList.add("error-message");
    if (isLoginError) {
      errorMessage.classList.add("login-error");
    }
  } else {
    errorMessage.classList.add("success-message");
  }

  setTimeout(() => {
    errorMessage.style.display = "none";
  }, 5000);
}

// Mantenha a função showError para compatibilidade
function showError(message, isLoginError = false) {
  showMessage(message, "error", isLoginError);
}

async function handleLogout() {
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.textContent = "Saindo...";
    logoutBtn.disabled = true;
  }

  await new Promise((resolve) => setTimeout(resolve, 300));
  localStorage.removeItem("embryotech_token");
  window.location.href = "index.html?logout=success";
}

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split(".")[1]));
  } catch (e) {
    return null;
  }
}

async function carregarEmpresas() {
  try {
    const token = localStorage.getItem("embryotech_token");
    const res = await fetch(`${API_BASE_URL}/empresas`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (res.ok) {
      const empresas = await res.json();
      const select = document.getElementById("empresaSelect");
      select.innerHTML = '<option value="">Selecione uma empresa</option>';

      empresas.forEach((empresa) => {
        const option = document.createElement("option");
        option.value = empresa;
        option.textContent = empresa;
        select.appendChild(option);
      });
    }
  } catch (error) {
    console.error("Erro ao carregar empresas:", error);
    showError("Erro ao carregar lista de empresas");
  }
}

// FUNÇÃO MOVIDA PARA O ESCOPO GLOBAL
function updateReadingsList(readings) {
  const container = document.getElementById("readingsListContainer");
  if (!container) {
    console.error("readingsListContainer not found when updating list.");
    return;
  }

  if (!readings || readings.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-clipboard-list"></i>
        <p>Nenhuma leitura encontrada</p>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="readings-grid">
      ${readings
        .map(
          (reading) => `
        <div class="reading-item">
          <p><strong>Data:</strong> ${formatDate(reading.data_inicial)}</p>
          <p><strong>Temperatura:</strong> ${reading.temperatura} °C</p>
          <p><strong>Umidade:</strong> ${reading.umidade} %</p>
          <p><strong>Pressão:</strong> ${reading.pressao} hPa</p>
          ${reading.lote ? `<p><strong>Lote:</strong> ${reading.lote}</p>` : ""}
        </div>
      `
        )
        .join("")}
    </div>
  `;
}

async function carregarLotes(empresa) {
  try {
    const token = localStorage.getItem("embryotech_token");
    const res = await fetch(
      `${API_BASE_URL}/lotes?empresa=${encodeURIComponent(empresa)}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    if (res.ok) {
      const lotes = await res.json();
      const select = document.getElementById("loteSelect");
      select.innerHTML = '<option value="">Selecione um lote</option>';
      select.disabled = false;

      lotes.forEach((lote) => {
        const option = document.createElement("option");
        option.value = lote;
        option.textContent = lote;
        select.appendChild(option);
      });

      document.getElementById("btnBuscarParametros").disabled =
        lotes.length === 0;
    }
  } catch (error) {
    console.error("Erro ao carregar lotes:", error);
    showError("Erro ao carregar lista de lotes");
  }
}

async function buscarParametros(empresa, lote) {
  try {
    const token = localStorage.getItem("embryotech_token");
    const res = await fetch(
      `${API_BASE_URL}/parametros?empresa=${encodeURIComponent(
        empresa
      )}&lote=${encodeURIComponent(lote)}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    if (res.ok) {
      const parametros = await res.json();
      if (parametros.length > 0) {
        return {
          id: parametros[0].id || "",
          empresa: parametros[0].empresa || "",
          lote: parametros[0].lote || "",
          temp_ideal: parametros[0].temp_ideal || "",
          umid_ideal: parametros[0].umid_ideal || "",
          pressao_ideal: parametros[0].pressao_ideal || "",
          lumens: parametros[0].lumens || "",
          id_sala: parametros[0].id_sala || "",
          estagio_ovo: parametros[0].estagio_ovo || "",
        };
      }
      return null;
    }
    return null;
  } catch (error) {
    console.error("Erro ao buscar parâmetros:", error);
    showError("Erro ao buscar parâmetros");
    return null;
  }
}

function setupParametroModal() {
  const parametroModal = document.getElementById("parametroModal");
  const parametroForm = document.getElementById("parametroForm");
  const filtersSection = document.querySelector(".parametro-filters");

  const fecharRodapeBtn = document.querySelector(
    "#customModal .custom-modal-footer .custom-close-btn"
  );

  if (fecharRodapeBtn) {
    fecharRodapeBtn.addEventListener("click", () => {
      document.getElementById("customModal").style.display = "none";
    });
  }

  // Fechar modal ao clicar fora
  parametroModal.addEventListener("click", (e) => {
    if (e.target === parametroModal) {
      document.getElementById("loteSelect").innerHTML =
        '<option value="">Selecione um lote</option>';
      document.getElementById("loteSelect").disabled = true;
      parametroModal.style.display = "none";
    }
  });

  // Carregar empresas ao abrir o modal
  document.getElementById("btnParametros").addEventListener("click", () => {
    parametroModal.style.display = "flex";
    carregarEmpresas();

    // Limpa o lote mas mantém a empresa se já estiver selecionada
    document.getElementById("loteSelect").innerHTML =
      '<option value="">Selecione um lote</option>';
    document.getElementById("loteSelect").disabled = true;

    filtersSection.style.display = "block";
    parametroForm.style.display = "none";
  });

  // Fechar modal
  parametroModal
    .querySelector(".custom-close-btn")
    .addEventListener("click", () => {
      document.getElementById("loteSelect").innerHTML =
        '<option value="">Selecione um lote</option>';
      document.getElementById("loteSelect").disabled = true;
      parametroModal.style.display = "none";
    });

  // Seleção de empresa
  document.getElementById("empresaSelect").addEventListener("change", (e) => {
    if (e.target.value) {
      carregarLotes(e.target.value);
    } else {
      document.getElementById("loteSelect").innerHTML =
        '<option value="">Selecione um lote</option>';
      document.getElementById("loteSelect").disabled = true;
      document.getElementById("btnBuscarParametros").disabled = true;
    }
  });

  document
    .getElementById("btnFecharParametros")
    .addEventListener("click", () => {
      document.getElementById("parametroModal").style.display = "none";
    });

  // Botão Novo Parâmetro - AGORA CARREGA FORMULÁRIO VAZIO PRONTO PARA PREENCHER
  document.getElementById("btnNovoParametro").addEventListener("click", () => {
    filtersSection.style.display = "none";
    parametroForm.style.display = "block";

    // Resetar e preparar formulário para novo cadastro
    parametroForm.reset();
    parametroForm.querySelector("[name='id']").value = "";

    // Preencher empresa e lote se já selecionados
    const empresaSelecionada = document.getElementById("empresaSelect").value;
    const loteSelecionado = document.getElementById("loteSelect").value;

    if (empresaSelecionada) {
      parametroForm.elements.empresa.value = empresaSelecionada;
    }
    if (loteSelecionado) {
      parametroForm.elements.lote.value = loteSelecionado;
    }

    // Definir valores padrão para campos numéricos (opcional)
    parametroForm.elements.temp_ideal.value = "";
    parametroForm.elements.umid_ideal.value = "";
    parametroForm.elements.pressao_ideal.value = "";
    parametroForm.elements.lumens.value = "";
    parametroForm.elements.id_sala.value = "";
    parametroForm.elements.estagio_ovo.value = "";
  });

  // Botão Cancelar
  document.getElementById("btnCancelar").addEventListener("click", () => {
    filtersSection.style.display = "block";
    parametroForm.style.display = "none";
  });

  // Buscar parâmetros existentes
  document
    .getElementById("btnBuscarParametros")
    .addEventListener("click", async () => {
      const empresa = document.getElementById("empresaSelect").value;
      const lote = document.getElementById("loteSelect").value;

      if (!empresa || !lote) {
        showError(
          "Por favor, selecione uma empresa e um lote para buscar os parâmetros.",
          true
        );
        return;
      }

      const parametro = await buscarParametros(empresa, lote);
      if (parametro) {
        document.querySelector(".parametro-filters").style.display = "none";
        document.getElementById("parametroForm").style.display = "block";

        // Preencher todos os campos do formulário
        const form = document.getElementById("parametroForm");
        form.elements.id.value = parametro.id || "";
        form.elements.empresa.value = parametro.empresa || "";
        form.elements.lote.value = parametro.lote || "";
        form.elements.temp_ideal.value = parametro.temp_ideal || "";
        form.elements.umid_ideal.value = parametro.umid_ideal || "";
        form.elements.pressao_ideal.value = parametro.pressao_ideal || "";
        form.elements.lumens.value = parametro.lumens || "";
        form.elements.id_sala.value = parametro.id_sala || "";
        form.elements.estagio_ovo.value = parametro.estagio_ovo || "";
      } else {
        showError("Nenhum parâmetro encontrado para este lote", "error", true);
      }
    });

  // Envio do formulário
  parametroForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(parametroForm).entries());

    // Validação dos campos obrigatórios
    const missingFields = [];
    if (!data.empresa) missingFields.push("Empresa");
    if (!data.lote) missingFields.push("Lote");
    if (!data.temp_ideal) missingFields.push("Temperatura Ideal");
    if (!data.umid_ideal) missingFields.push("Umidade Ideal");
    if (!data.pressao_ideal) missingFields.push("Pressão Ideal");
    if (!data.lumens) missingFields.push("Lumens");
    if (!data.id_sala) missingFields.push("ID da Sala");
    if (!data.estagio_ovo) missingFields.push("Estágio do Ovo");

    const estagio = parseInt(data.estagio_ovo, 10);
    if (isNaN(estagio) || estagio < 1 || estagio > 18) {
      showMessage("O estágio do ovo deve estar entre 1 e 18.", "error", true);
      return;
    }

    if (missingFields.length > 0) {
      showMessage(
        `Os seguintes campos são obrigatórios: ${missingFields.join(", ")}`,
        "error",
        true
      );
      return;
    }

    try {
      const token = localStorage.getItem("embryotech_token");
      const method = data.id ? "PUT" : "POST";
      const url = data.id
        ? `${API_BASE_URL}/parametros/${data.id}`
        : `${API_BASE_URL}/parametros`;

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          empresa: data.empresa,
          lote: data.lote,
          temp_ideal: parseFloat(data.temp_ideal),
          umid_ideal: parseFloat(data.umid_ideal),
          pressao_ideal: data.pressao_ideal
            ? parseFloat(data.pressao_ideal)
            : null,
          lumens: data.lumens ? parseFloat(data.lumens) : null,
          id_sala: data.id_sala ? parseInt(data.id_sala) : null,
          estagio_ovo: data.estagio_ovo || null,
        }),
      });

      if (res.ok) {
        showMessage("Parâmetros salvos com sucesso!", "success");
        setTimeout(() => {
          parametroModal.style.display = "none";
          filtersSection.style.display = "block";
          parametroForm.style.display = "none";
        }, 1500);
      } else {
        const err = await res.json();
        showError("Erro: " + err.message, true);
      }
    } catch (error) {
      showError("Erro ao salvar parâmetros: " + error.message, true);
    }
  });
}

// FUNÇÃO MOVIDA PARA O ESCOPO GLOBAL
function updateReadingsCount(count) {
  const countElement = document.getElementById("readingsCount");
  if (countElement) {
    countElement.innerHTML = `<strong>Total de leituras:</strong> ${count}`;
  }
}

function setupDashboardPage() {
  const token = localStorage.getItem("embryotech_token");
  if (!token) {
    handleLogout();
    return;
  }

  const payload = parseJwt(token);

  // Mostrar botão de parâmetros apenas para admin
  const btnParametros = document.getElementById("btnParametros");
  if (btnParametros) {
    btnParametros.style.display =
      payload && payload.is_admin ? "block" : "none";
  }

  const logoutBtn = document.getElementById("logoutBtn");
  const showHistoryBtn = document.getElementById("showHistoryBtn");
  const lastReadingContainer = document.getElementById("lastReadingContainer");
  const readingsListContainer = document.getElementById(
    "readingsListContainer"
  );

  if (showHistoryBtn) {
    showHistoryBtn.addEventListener("click", showHistoryModal);
  }

  const loteLabel = document.getElementById("loteLabel");

  // Declarar os gráficos

  const tempChart = new Chart(document.getElementById("tempChart"), {
    type: "line",
    data: { labels: [], datasets: [] },
    options: { responsive: true, maintainAspectRatio: false },
  });

  const umidChart = new Chart(document.getElementById("umidChart"), {
    type: "line",
    data: { labels: [], datasets: [] },
    options: { responsive: true, maintainAspectRatio: false },
  });

  const pressChart = new Chart(document.getElementById("pressChart"), {
    type: "line",
    data: { labels: [], datasets: [] },
    options: { responsive: true, maintainAspectRatio: false },
  });

  // Finalizando o processo de declaração dos gráficos

  const loteFilter = document.getElementById("loteFilter");

  // Função para carregar lotes disponíveis
  async function fetchLotes(empresa = "") {
    try {
      const token = localStorage.getItem("embryotech_token");
      let url = `${API_BASE_URL}/lotes`;
      if (empresa) {
        url += `?empresa=${encodeURIComponent(empresa)}`;
      }

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Erro ao carregar lotes");
      return await response.json();
    } catch (error) {
      console.error("Erro ao carregar lotes:", error);
      showError("Erro ao carregar lista de lotes");
      return [];
    }
  }

  // Inicializa o combobox de lotes
  async function initLoteFilter() {
    // Carrega todos os lotes inicialmente (sem filtro de empresa)
    const lotes = await fetchLotes();

    loteFilter.innerHTML = '<option value="">Todos os Lotes</option>';
    lotes.forEach((lote) => {
      const option = document.createElement("option");
      option.value = lote;
      option.textContent = lote;
      loteFilter.appendChild(option);
    });

    loteFilter.addEventListener("change", async () => {
      const loteSelecionado = loteFilter.value;
      loteLabel.textContent = loteSelecionado
        ? `Lote: ${loteSelecionado}`
        : "Lote: Todos";
      await fetchReadings(loteSelecionado);
    });
  }

  if (logoutBtn) logoutBtn.addEventListener("click", handleLogout);
  if (showHistoryBtn)
    showHistoryBtn.addEventListener("click", showHistoryModal);

  if (payload && payload.is_admin) {
    setupParametroModal();
  }

  fetchReadings();

  async function fetchReadings(lote = "") {
    try {
      console.log(`Buscando leituras para lote: ${lote}`);
      const token = localStorage.getItem("embryotech_token");
      let url = `${API_BASE_URL}/leituras`;

      if (lote) {
        url += `?lote=${encodeURIComponent(lote)}`;
      }

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);

      let readings = await response.json();

      // Processamento seguro das datas
      readings = readings.map((r) => ({
        ...r,
        data_inicial: r.data_inicial ? new Date(r.data_inicial) : null,
        data_final: r.data_final ? new Date(r.data_final) : null,
      }));

      // Ordenação segura
      readings.sort((a, b) => {
        const dateA = a.data_inicial ? new Date(a.data_inicial) : new Date(0);
        const dateB = b.data_inicial ? new Date(b.data_inicial) : new Date(0);
        return dateB - dateA;
      });

      if (readings.length > 0) {
        updateLastReading(readings[0]);
        updateCharts([...readings].reverse());
      } else {
        updateLastReading(null);
        updateCharts([]);
      }
    } catch (error) {
      console.error("Erro ao buscar leituras:", error);
      showError(`Erro ao carregar leituras: ${error.message}`);
    }
  }

  // INICIALIZE O FILTRO
  initLoteFilter();

  function updateLastReading(reading) {
    if (!lastReadingContainer) return;

    if (!reading) {
      lastReadingContainer.innerHTML = `
      <div class="reading-data">
        <p>Nenhuma leitura disponível para o lote selecionado</p>
      </div>
    `;
      return;
    }

    lastReadingContainer.innerHTML = `
    <div class="reading-data">
      <p><strong>Data/Hora:</strong> ${formatDate(reading.data_inicial)}</p>
      <p><strong>Temperatura:</strong> ${reading.temperatura} °C</p>
      <p><strong>Umidade:</strong> ${reading.umidade} %</p>
      <p><strong>Pressão:</strong> ${reading.pressao} hPa</p>
      <p><strong>Lote:</strong> ${reading.lote || "N/A"}</p>
    </div>
  `;
  }

  function updateCharts(readings) {
    readings.sort(
      (a, b) => new Date(a.data_inicial) - new Date(b.data_inicial)
    );
    const labels = readings.map((r) => formatDate(r.data_inicial, true));
    const temps = readings.map((r) => r.temperatura);
    const umids = readings.map((r) => r.umidade);
    const presses = readings.map((r) => r.pressao);

    updateChart(
      tempChart,
      labels,
      temps,
      "Temperatura (°C)",
      "rgba(255, 99, 132, 0.8)"
    );
    updateChart(
      umidChart,
      labels,
      umids,
      "Umidade (%)",
      "rgba(54, 162, 235, 0.8)"
    );
    updateChart(
      pressChart,
      labels,
      presses,
      "Pressão (hPa)",
      "rgba(3, 62, 253, 0.8)"
    );
  }

  function updateChart(chart, labels, data, label, color) {
    chart.data.labels = labels;
    chart.data.datasets = [
      {
        label: label,
        data: data,
        borderColor: color,
        backgroundColor: color.replace("0.8", "0.2"),
        tension: 0.1,
        fill: true,
      },
    ];
    chart.update();
  }

  function showHistoryModal() {
    const modal = document.getElementById("customModal");
    const loteSelecionado = document.getElementById("loteFilter").value;

    modal.style.display = "flex";

    setTimeout(() => {
      fetchHistoryReadings(loteSelecionado);
    }, 50);

    // aplica o evento a todos os botões de fechar
    const closeButtons = modal.querySelectorAll(".custom-close-btn");
    closeButtons.forEach((btn) => {
      if (!btn.dataset.listenerAttached) {
        btn.addEventListener("click", () => {
          modal.style.display = "none";
        });
        btn.dataset.listenerAttached = "true";
      }
    });

    if (!modal.dataset.listenerAttached) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) {
          modal.style.display = "none";
        }
      });
      modal.dataset.listenerAttached = "true";
    }
  }
}

async function fetchHistoryReadings(lote = "") {
  try {
    const token = localStorage.getItem("embryotech_token");
    const container = document.getElementById("readingsListContainer");

    if (!container) {
      console.error(
        "Elemento readingsListContainer não encontrado em fetchHistoryReadings"
      );
      return;
    }

    container.innerHTML = "<p>Carregando histórico...</p>";

    const url = lote
      ? `${API_BASE_URL}/leituras?lote=${encodeURIComponent(lote)}`
      : `${API_BASE_URL}/leituras`;

    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) throw new Error("Erro ao carregar histórico");

    let readings = await response.json();

    // Processamento das datas
    readings = readings.map((r) => ({
      ...r,
      data_inicial: r.data_inicial ? new Date(r.data_inicial) : null,
      data_final: r.data_final ? new Date(r.data_final) : null,
    }));

    readings.sort(
      (a, b) => new Date(b.data_inicial) - new Date(a.data_inicial)
    );

    updateReadingsList(readings);
    updateReadingsCount(readings.length);
  } catch (error) {
    console.error("Erro em fetchHistoryReadings:", error);
    const container = document.getElementById("readingsListContainer");
    if (container) {
      container.innerHTML = `<p class="error">Erro ao carregar histórico: ${error.message}</p>`;
    }
    showError("Erro ao carregar histórico de leituras");
  }
}

function formatDate(dateString, short = false) {
  if (!dateString) return "N/A";

  const date = new Date(dateString);
  const options = {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  };

  if (short) {
    return `${date.toLocaleDateString("pt-BR")} ${date.toLocaleTimeString(
      "pt-BR",
      {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }
    )}`;
  }

  return date.toLocaleString("pt-BR", options);
}

function setupLoginPage() {
  loginForm = document.getElementById("loginForm");
  if (!loginForm) return;

  if (localStorage.getItem("embryotech_token")) {
    window.location.href = "dashboard.html";
    return;
  }

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const submitBtn = loginForm.querySelector('button[type="submit"]');

    if (!username || !password) {
      showError("Por favor, preencha todos os campos.", true);
      return;
    }

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

document.addEventListener("DOMContentLoaded", function () {
  if (
    window.location.pathname.endsWith("index.html") ||
    window.location.pathname === "/"
  ) {
    setupLoginPage();
  } else if (window.location.pathname.endsWith("dashboard.html")) {
    setupDashboardPage();
  }
});
