// script.js completo com adição da funcionalidade de parâmetros (admin)

const API_BASE_URL = "http://147.79.104.68:5001";

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

function setupDashboardPage() {
  const token = localStorage.getItem("embryotech_token");
  if (!token) {
    handleLogout();
    return;
  }

  const logoutBtn = document.getElementById("logoutBtn");
  const showHistoryBtn = document.getElementById("showHistoryBtn");
  const lastReadingContainer = document.getElementById("lastReadingContainer");
  const readingsListContainer = document.getElementById(
    "readingsListContainer"
  );
  const loteLabel = document.getElementById("loteLabel");

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

  if (logoutBtn) logoutBtn.addEventListener("click", handleLogout);
  if (showHistoryBtn)
    showHistoryBtn.addEventListener("click", showHistoryModal);

  const payload = parseJwt(token);
  if (payload && payload.is_admin) {
    const adminMenu = document.getElementById("adminMenu");
    if (adminMenu) adminMenu.style.display = "block";

    const btnParametros = document.getElementById("btnParametros");
    const parametroModal = document.getElementById("parametroModal");
    const parametroForm = document.getElementById("parametroForm");
    const closeBtn = parametroModal.querySelector(".custom-close-btn");

    btnParametros.addEventListener("click", () => {
      parametroModal.style.display = "flex";
    });

    closeBtn.addEventListener("click", () => {
      parametroModal.style.display = "none";
    });

    parametroForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(parametroForm).entries());

      try {
        const res = await fetch(`${API_BASE_URL}/parametros`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(data),
        });

        if (res.ok) {
          alert("Parâmetro salvo com sucesso!");
          parametroForm.reset();
          parametroModal.style.display = "none";
        } else {
          const err = await res.json();
          alert("Erro: " + err.message);
        }
      } catch (error) {
        alert("Erro ao salvar parâmetro.");
      }
    });
  }

  fetchReadings();

  async function fetchReadings() {
    try {
      const response = await fetch(`${API_BASE_URL}/leituras`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Erro ao carregar leituras");

      let readings = await response.json();
      readings.sort(
        (a, b) => new Date(b.data_inicial) - new Date(a.data_inicial)
      );

      if (readings.length > 0) {
        updateLastReading(readings[0]);
        const readingsForCharts = [...readings].reverse();
        updateReadingsList(readings);
        updateCharts(readingsForCharts);
        loteLabel.textContent = `Lote: ${readings[0].lote || "N/A"}`;
        updateReadingsCount(readings.length);
      }
    } catch (error) {
      console.error("Erro:", error);
      showError("Erro ao carregar leituras");
    }
  }

  function updateLastReading(reading) {
    if (!lastReadingContainer) return;

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

  function updateReadingsList(readings) {
    if (!readingsListContainer) return;

    let html = '<div class="readings-grid">';
    readings.forEach((reading) => {
      html += `
        <div class="reading-item">
          <p><strong>Data:</strong> ${formatDate(reading.data_inicial)}</p>
          <p><strong>Temperatura:</strong> ${reading.temperatura} °C</p>
          <p><strong>Umidade:</strong> ${reading.umidade} %</p>
          <p><strong>Pressão:</strong> ${reading.pressao} hPa</p>
        </div>
      `;
    });
    html += "</div>";
    readingsListContainer.innerHTML = html;
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
      "rgba(75, 192, 192, 0.8)"
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
    const closeBtn = document.querySelector(".custom-close-btn");

    modal.style.display = "flex";
    closeBtn.addEventListener("click", () => {
      modal.style.display = "none";
    });

    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.style.display = "none";
      }
    });
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
