const state = {
  summary: null,
  route: [],
  sections: [],
  reclosers: [],
  transformers: [],
  mvCustomers: [],
  substations: [],
};

const endpoints = {
  runLossAgent: "/synthetic-loss-agent/run",
  runFeederOperational: "/synthetic-feeder-operational/run",
  summary: "/synthetic-feeder-operational/summary",
  route: "/synthetic-feeder-operational/route",
  sections: "/synthetic-feeder-operational/sections",
  reclosers: "/synthetic-feeder-operational/reclosers",
  transformers: "/synthetic-feeder-operational/transformers?limit=100",
  mvCustomers: "/synthetic-feeder-operational/mv-customers",
  substations: "/synthetic-feeder-operational/substations",
};

document.addEventListener("DOMContentLoaded", () => {
  bindActions();
  loadDashboard();
});

function bindActions() {
  const runButton = document.getElementById("run-agent-button");

  if (!runButton) {
    return;
  }

  runButton.addEventListener("click", async () => {
    await runAgent();
  });
}

async function runAgent() {
  setStatus("Executando agente sintético e atualizando painel...", "success");

  try {
    await postJson(endpoints.runLossAgent);
    await postJson(endpoints.runFeederOperational);
    await loadDashboard();
    setStatus("Agente executado e painel atualizado com sucesso.", "success");
  } catch (error) {
    setStatus(`Erro ao executar agente: ${error.message}`, "error");
  }
}

async function loadDashboard() {
  try {
    setStatus("Carregando dados sintéticos do alimentador...", "");

    const [
      summary,
      routeResponse,
      sectionsResponse,
      reclosersResponse,
      transformersResponse,
      mvCustomersResponse,
      substationsResponse,
    ] = await Promise.all([
      fetchJson(endpoints.summary),
      fetchJson(endpoints.route),
      fetchJson(endpoints.sections),
      fetchJson(endpoints.reclosers),
      fetchJson(endpoints.transformers),
      fetchJson(endpoints.mvCustomers),
      fetchJson(endpoints.substations),
    ]);

    state.summary = summary;
    state.route = routeResponse.items || [];
    state.sections = sectionsResponse.items || [];
    state.reclosers = reclosersResponse.items || [];
    state.transformers = transformersResponse.items || [];
    state.mvCustomers = mvCustomersResponse.items || [];
    state.substations = substationsResponse.items || [];

    renderMetrics();
    renderSectionsTable();
    renderReclosers();
    renderTransformersTable();
    renderMap();

    setStatus("Painel carregado com dados sintéticos operacionais.", "success");
  } catch (error) {
    setStatus(`Erro ao carregar painel: ${error.message}`, "error");
  }
}

function renderMetrics() {
  const summary = state.summary || {};
  const substation = state.substations[0] || {};

  setText("feeder-code", summary.codigo_alimentador || "--");
  setText("substation-code", summary.codigo_subestacao || "--");
  setText("substation-name", substation.nome_subestacao || "Origem do alimentador");

  setText("total-uc-bt", formatInteger(summary.total_uc_bt));
  setText("total-uc-mt", formatInteger(summary.total_uc_mt));
  setText("total-gd", formatInteger(summary.total_gd));
  setText("total-transformers", formatInteger(summary.total_transformadores));
  setText("total-reclosers", formatInteger(summary.total_religadores));
  setText("network-distance", formatNumber(summary.extensao_rede_km, 2));
  setText("estimated-loss", formatNumber(summary.perda_estimada_gwh, 3));
  setText("loss-percent", formatPercent(summary.perda_percentual));
}

function renderSectionsTable() {
  const tableBody = document.getElementById("sections-table-body");

  if (!tableBody) {
    return;
  }

  tableBody.innerHTML = "";

  state.sections.forEach((section) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${escapeHtml(section.codigo_secao)}</td>
      <td>${escapeHtml(section.religador_origem)}</td>
      <td>${escapeHtml(section.religador_destino)}</td>
      <td>${formatInteger(section.transformadores)}</td>
      <td>${formatInteger(section.uc_bt)}</td>
      <td>${formatInteger(section.uc_mt)}</td>
      <td>${formatInteger(section.gd)}</td>
      <td>${formatNumber(section.perda_estimada_gwh, 3)}</td>
      <td>${formatPercent(section.perda_percentual)}</td>
      <td>${heatBadge(section.nivel_calor)}</td>
    `;

    tableBody.appendChild(row);
  });
}

function renderReclosers() {
  const list = document.getElementById("recloser-list");

  if (!list) {
    return;
  }

  list.innerHTML = "";

  state.reclosers.forEach((recloser) => {
    const item = document.createElement("article");
    item.className = "stack-item";

    item.innerHTML = `
      <div class="stack-item-header">
        <strong>${escapeHtml(recloser.codigo_religador)}</strong>
        ${heatBadge(recloser.nivel_calor)}
      </div>
      <p>
        Trecho ${escapeHtml(recloser.trecho)} |
        ${formatInteger(recloser.transformadores_jusante)} trafos a jusante |
        ${formatInteger(recloser.uc_bt_jusante)} UC BT |
        ${formatInteger(recloser.uc_mt_jusante)} UC MT |
        ${formatInteger(recloser.gd_jusante)} GD
      </p>
      <p>
        Consumo a jusante:
        ${formatNumber(recloser.consumo_jusante_gwh, 3)} GWh |
        Injetada:
        ${formatNumber(recloser.energia_injetada_jusante_gwh, 3)} GWh |
        Perda:
        ${formatNumber(recloser.perda_jusante_gwh, 3)} GWh
        (${formatPercent(recloser.perda_percentual_jusante)})
      </p>
    `;

    list.appendChild(item);
  });
}

function renderTransformersTable() {
  const tableBody = document.getElementById("transformers-table-body");

  if (!tableBody) {
    return;
  }

  const rankedTransformers = [...state.transformers]
    .sort((left, right) => {
      return toNumber(right.perda_estimada_mwh) - toNumber(left.perda_estimada_mwh);
    })
    .slice(0, 10);

  tableBody.innerHTML = "";

  rankedTransformers.forEach((transformer) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${escapeHtml(transformer.codigo_transformador)}</td>
      <td>${escapeHtml(transformer.trecho)}</td>
      <td>${formatInteger(transformer.uc_bt)}</td>
      <td>${formatInteger(transformer.gd)}</td>
      <td>${formatNumber(transformer.energia_injetada_mwh, 2)}</td>
      <td>${formatNumber(transformer.perda_estimada_mwh, 2)}</td>
      <td>${heatBadge(transformer.nivel_calor)}</td>
    `;

    tableBody.appendChild(row);
  });
}

function renderMap() {
  const map = document.getElementById("feeder-map");

  if (!map) {
    return;
  }

  map.innerHTML = `
    <div class="map-line" id="map-line"></div>
    <div class="energy-flow">Fluxo de energia</div>
  `;

  const allGeoPoints = [
    ...state.route,
    ...state.reclosers,
    ...state.mvCustomers,
    ...state.transformers,
    ...state.substations,
  ].filter((point) => hasCoordinates(point));

  if (allGeoPoints.length === 0) {
    return;
  }

  const bounds = buildBounds(allGeoPoints);

  renderRouteLine(bounds);
  renderRoutePoints(map, bounds);
  renderTransformers(map, bounds);
  renderReclosers(map, bounds);
  renderMvCustomers(map, bounds);
  renderSubstations(map, bounds);
}

function renderRouteLine(bounds) {
  const route = state.route.filter((point) => hasCoordinates(point));
  const lineContainer = document.getElementById("map-line");

  if (!lineContainer || !bounds || route.length < 2) {
    return;
  }

  const polyline = route
    .map((point) => {
      const position = projectPoint(point, bounds);
      return `${position.x},${position.y}`;
    })
    .join(" ");

  lineContainer.innerHTML = `
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <polyline
        points="${polyline}"
        fill="none"
        stroke="#0284c7"
        stroke-width="0.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <polyline
        points="${polyline}"
        fill="none"
        stroke="rgba(255,255,255,0.85)"
        stroke-width="0.25"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  `;
}

function renderRoutePoints(map, bounds) {
  state.route
    .filter((point) => hasCoordinates(point))
    .forEach((point) => {
      if (point.tipo_ponto === "subestacao") {
        return;
      }

      if (point.tipo_ponto === "religador") {
        return;
      }

      if (point.tipo_ponto === "cliente_mt") {
        return;
      }

      const tooltip = [
        `Percurso: ${point.descricao}`,
        `Sequência: ${point.sequencia}`,
        `Alimentador: ${point.codigo_alimentador}`,
      ].join("\n");

      addMapPoint(map, bounds, point, "transformer low", tooltip);
    });
}

function renderTransformers(map, bounds) {
  state.transformers
    .filter((point) => hasCoordinates(point))
    .forEach((transformer) => {
      const heatClass = heatClassName(transformer.nivel_calor);
      const tooltip = [
        `Trafo: ${transformer.codigo_transformador}`,
        `Trecho: ${transformer.trecho}`,
        `UC BT: ${formatInteger(transformer.uc_bt)}`,
        `UC MT: ${formatInteger(transformer.uc_mt)}`,
        `GD: ${formatInteger(transformer.gd)}`,
        `Consumo: ${formatNumber(transformer.consumo_mensal_mwh, 2)} MWh`,
        `Injetada: ${formatNumber(transformer.energia_injetada_mwh, 2)} MWh`,
        `Perda: ${formatNumber(transformer.perda_estimada_mwh, 2)} MWh`,
        `Perda %: ${formatPercent(transformer.perda_percentual)}`,
        `Calor: ${transformer.nivel_calor}`,
      ].join("\n");

      addMapPoint(map, bounds, transformer, `transformer ${heatClass}`, tooltip);
    });
}

function renderReclosers(map, bounds) {
  state.reclosers
    .filter((point) => hasCoordinates(point))
    .forEach((recloser) => {
      const tooltip = [
        `Religador: ${recloser.codigo_religador}`,
        `Trecho: ${recloser.trecho}`,
        `Trafos a jusante: ${formatInteger(recloser.transformadores_jusante)}`,
        `UC BT a jusante: ${formatInteger(recloser.uc_bt_jusante)}`,
        `UC MT a jusante: ${formatInteger(recloser.uc_mt_jusante)}`,
        `GD a jusante: ${formatInteger(recloser.gd_jusante)}`,
        `Perda: ${formatNumber(recloser.perda_jusante_gwh, 3)} GWh`,
        `Perda %: ${formatPercent(recloser.perda_percentual_jusante)}`,
      ].join("\n");

      addMapPoint(map, bounds, recloser, "recloser", tooltip);
    });
}

function renderMvCustomers(map, bounds) {
  state.mvCustomers
    .filter((point) => hasCoordinates(point))
    .forEach((customer) => {
      const tooltip = [
        `Cliente MT: ${customer.codigo_cliente_mt}`,
        `Setor: ${customer.setor}`,
        `Demanda: ${formatNumber(customer.demanda_kw, 1)} kW`,
        `Consumo: ${formatNumber(customer.consumo_mensal_mwh, 2)} MWh`,
      ].join("\n");

      addMapPoint(map, bounds, customer, "mt", tooltip);
    });
}

function renderSubstations(map, bounds) {
  state.substations
    .filter((point) => hasCoordinates(point))
    .forEach((substation) => {
      const tooltip = [
        `Subestação: ${substation.codigo_subestacao}`,
        `${substation.nome_subestacao}`,
        `Tensão: ${formatNumber(substation.tensao_kv, 1)} kV`,
      ].join("\n");

      addMapPoint(map, bounds, substation, "substation", tooltip);
    });
}

function addMapPoint(map, bounds, point, className, tooltip) {
  if (!map || !bounds || !point || !hasCoordinates(point)) {
    return;
  }

  const position = projectPoint(point, bounds);
  const element = document.createElement("button");

  element.type = "button";
  element.className = `map-point ${className}`;
  element.style.left = `${position.x}%`;
  element.style.top = `${position.y}%`;
  element.dataset.tooltip = tooltip;

  map.appendChild(element);
}

function buildBounds(points) {
  const validPoints = points.filter((point) => hasCoordinates(point));

  if (validPoints.length === 0) {
    return null;
  }

  const latitudes = validPoints.map((point) => toNumber(point.latitude));
  const longitudes = validPoints.map((point) => toNumber(point.longitude));

  return {
    minLatitude: Math.min(...latitudes),
    maxLatitude: Math.max(...latitudes),
    minLongitude: Math.min(...longitudes),
    maxLongitude: Math.max(...longitudes),
  };
}

function projectPoint(point, bounds) {
  if (!bounds) {
    return {
      x: 50,
      y: 50,
    };
  }

  const latitude = toNumber(point.latitude);
  const longitude = toNumber(point.longitude);

  return {
    x: normalize(longitude, bounds.minLongitude, bounds.maxLongitude),
    y: 100 - normalize(latitude, bounds.minLatitude, bounds.maxLatitude),
  };
}

function normalize(value, min, max) {
  if (max === min) {
    return 50;
  }

  return ((value - min) / (max - min)) * 82 + 9;
}

async function fetchJson(url) {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`${url} retornou HTTP ${response.status}`);
  }

  return response.json();
}

async function postJson(url) {
  const response = await fetch(url, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`${url} retornou HTTP ${response.status}`);
  }

  return response.json();
}

function setStatus(message, type) {
  const element = document.getElementById("status-message");

  if (!element) {
    return;
  }

  element.className = "status-bar";

  if (type) {
    element.classList.add(type);
  }

  element.textContent = message;
}

function setText(id, value) {
  const element = document.getElementById(id);

  if (!element) {
    return;
  }

  element.textContent = value;
}

function heatBadge(level) {
  const normalizedLevel = String(level || "BAIXO").toUpperCase();
  const className = heatClassName(normalizedLevel);

  return `<span class="badge ${className}">${escapeHtml(normalizedLevel)}</span>`;
}

function heatClassName(level) {
  const normalizedLevel = String(level || "BAIXO").toUpperCase();

  if (normalizedLevel === "ALTO") {
    return "alto";
  }

  if (normalizedLevel === "MEDIO") {
    return "medio";
  }

  return "baixo";
}

function hasCoordinates(point) {
  if (!point) {
    return false;
  }

  return point.latitude !== undefined && point.longitude !== undefined;
}

function toNumber(value) {
  const numberValue = Number(value);

  if (Number.isNaN(numberValue)) {
    return 0;
  }

  return numberValue;
}

function formatInteger(value) {
  return toNumber(value).toLocaleString("pt-BR", {
    maximumFractionDigits: 0,
  });
}

function formatNumber(value, digits) {
  return toNumber(value).toLocaleString("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatPercent(value) {
  return `${(toNumber(value) * 100).toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}