const form = document.getElementById("generator-form");
const requestText = document.getElementById("request-text");
const profileDescription = document.getElementById("profile-description");
const statusNode = document.getElementById("status");
const progressNode = document.querySelector(".progress");
const generateButton = document.getElementById("generate-button");
const analyzeButton = document.getElementById("analyze-button");
const aiStatusTitle = document.getElementById("ai-status-title");
const aiStatusCopy = document.getElementById("ai-status-copy");
const analysisVariant = document.getElementById("analysis-variant");
const analysisSource = document.getElementById("analysis-source");
const analysisProfile = document.getElementById("analysis-profile");
const analysisStyle = document.getElementById("analysis-style");
const analysisStages = document.getElementById("analysis-stages");
const analysisThrust = document.getElementById("analysis-thrust");
const analysisFuel = document.getElementById("analysis-fuel");
const analysisTheme = document.getElementById("analysis-theme");

let analyzeTimer = null;

function detectProfile(text) {
  const normalized = text.toLowerCase();
  if (normalized.includes("баліст") && (normalized.includes("ракет") || normalized.includes("missile")) && !["thaad", "перехоп", "протиракет", "patriot", "pac-3", "pac3"].some((word) => normalized.includes(word))) {
    return {
      title: "Ballistic Missile",
      description: "Звичайна балістична ракета без ПРО-наведення і без профілю THAAD.",
    };
  }
  if (["thaad", "протиракет", "перехоп"].some((word) => normalized.includes(word))) {
    return {
      title: "THAAD / ПРО-профіль",
      description: "Профіль перехоплювача. Для звичайної балістичної ракети пиши саме про ракету, без слів про перехоплення.",
    };
  }
  if (["patriot", "pac-3", "pac3"].some((word) => normalized.includes(word))) {
    return {
      title: "Patriot PAC-3",
      description: "Компактний маневровий перехоплювач ближчої дії.",
    };
  }
  if (["ракет", "launcher", "launch", "злет", "старт"].some((word) => normalized.includes(word)) && !["баліст", "thaad", "перехоп", "протиракет", "patriot", "pac-3", "pac3"].some((word) => normalized.includes(word))) {
    return {
      title: "Orbital Launcher",
      description: "Базова ракета-носій зі значно сильнішим двигуном і простішою стартовою схемою.",
    };
  }
  if (["орбі", "супутник", "launcher", "носі"].some((word) => normalized.includes(word))) {
    return {
      title: "Orbital Launcher",
      description: "Ракета-носій для орбітального запуску без ручного вводу технічних параметрів.",
    };
  }
  if (["буксир", "tug", "стику", "маневр"].some((word) => normalized.includes(word))) {
    return {
      title: "Orbital Tug",
      description: "Орбітальний апарат для маневрів, стикування та переміщення вантажів.",
    };
  }
  if (["дослід", "тест", "навч", "sounding"].some((word) => normalized.includes(word))) {
    return {
      title: "Sounding Rocket",
      description: "Легка суборбітальна ракета для тестів і простих місій.",
    };
  }

  return {
    title: "Автовибір профілю",
    description: "Напиши вільним текстом, що саме треба. Сервер сам підбере тип крафту і параметри.",
  };
}

function updateProfileCard() {
  const profile = detectProfile(requestText.value);
  profileDescription.innerHTML = `
    <span>Що буде використано</span>
    <strong>${profile.title}</strong>
    <p>${profile.description}</p>
  `;
}

function formatNumber(value) {
  return new Intl.NumberFormat("uk-UA").format(value);
}

function renderAiStatus(capabilities, parserSource) {
  const aiEnabled = Boolean(capabilities?.ai_enabled);
  if (aiEnabled) {
    aiStatusTitle.textContent = `OpenAI активний · ${capabilities.model}`;
    aiStatusCopy.textContent = parserSource === "openai"
      ? "Поточний запит був розібраний через AI-модель і потім злитий з локальними правилами генератора."
      : "AI-режим доступний. Для цього запиту зараз спрацювали локальні правила або fallback після AI.";
    return;
  }

  aiStatusTitle.textContent = "Локальний fallback";
  aiStatusCopy.textContent = "Сервер працює на локальному парсері правил. Додай OPENAI_API_KEY, щоб увімкнути глибший AI-розбір.";
}

function renderAnalysis(data) {
  renderAiStatus(data.capabilities, data.parser_source);
  analysisVariant.textContent = data.variant_name || data.craft_name || "Без варіанта";
  const baseSourceText = data.parser_source === "openai"
    ? "Запит розібраний AI-моделлю й підготовлений до генерації XML."
    : "Запит розібраний локальним parser fallback і готовий до генерації XML.";
  const templateNote = data.prefer_template && !data.template_available
    ? " Шаблон не знайдено, увімкнено auto-procedural режим з розширеною деталізацією."
    : "";
  analysisSource.textContent = data.fidelity_note
    ? `${baseSourceText} ${data.fidelity_note}${templateNote}`
    : `${baseSourceText}${templateNote}`;
  analysisProfile.textContent = data.profile_label || data.profile_id || "-";
  analysisStyle.textContent = data.replica_mode ? "replica" : (data.style_preset || "default");
  analysisStages.textContent = `${data.stages || "-"}`;
  analysisThrust.textContent = data.thrust ? `${formatNumber(data.thrust)} N` : "-";
  analysisFuel.textContent = data.fuel_capacity ? `${formatNumber(data.fuel_capacity)} u` : "-";

  const theme = data.theme || {};
  const themeTokens = [theme.base, theme.detail, theme.accent].filter(Boolean);
  const themeText = themeTokens.length ? themeTokens.join(" / ") : "Авто";
  if (data.prefer_template && data.template_id) {
    analysisTheme.textContent = data.template_available
      ? `${themeText} · template:${data.template_id}`
      : `${themeText} · auto:${data.template_id} (missing template)`;
  } else {
    analysisTheme.textContent = themeText;
  }
}

async function analyzeRequest(showStatus = false) {
  const payload = Object.fromEntries(new FormData(form).entries());

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Не вдалося проаналізувати запит.");
    }

    renderAnalysis(data);
    if (showStatus) {
      statusNode.textContent = "AI-аналіз оновлено. Можна одразу генерувати XML.";
    }
    return data;
  } catch (error) {
    if (showStatus) {
      statusNode.textContent = error.message;
    }
    throw error;
  }
}

function scheduleAnalysis() {
  clearTimeout(analyzeTimer);
  analyzeTimer = setTimeout(() => {
    analyzeRequest(false).catch(() => {
      analysisSource.textContent = "Автоаналіз не вдався. Перевір заповнення полів або запусти аналіз вручну.";
    });
  }, 320);
}

async function generateCraft(event) {
  event.preventDefault();

  statusNode.textContent = "";
  progressNode.hidden = false;
  generateButton.disabled = true;
  analyzeButton.disabled = true;

  const payload = Object.fromEntries(new FormData(form).entries());

  try {
    await analyzeRequest(false);

    const response = await fetch("/api/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || "Не вдалося згенерувати XML.");
    }

    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "craft.xml";
    const match = disposition.match(/filename="?([^\"]+)"?/i);
    const fileName = match ? match[1] : "craft.xml";
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    statusNode.textContent = "XML-файл згенеровано. Завантаження має початися автоматично.";
  } catch (error) {
    statusNode.textContent = error.message;
  } finally {
    progressNode.hidden = true;
    generateButton.disabled = false;
    analyzeButton.disabled = false;
  }
}

requestText.addEventListener("input", () => {
  updateProfileCard();
  scheduleAnalysis();
});
form.craftName.addEventListener("input", scheduleAnalysis);
analyzeButton.addEventListener("click", () => {
  statusNode.textContent = "";
  analyzeRequest(true).catch(() => {});
});
form.addEventListener("submit", generateCraft);
updateProfileCard();
analyzeRequest(false).catch(() => {});
