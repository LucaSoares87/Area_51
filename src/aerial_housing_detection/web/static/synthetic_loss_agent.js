const state = {
  summary: null,
  route: [],
  sections: [],
  reclosers: [],
  transformers: [],
  mvCustomers: [],
  substations: [],
  currentHeatFilter: "TODOS",
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
  bindFilters();
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

function bindFilters() {
  const filterButtons = document.querySelectorAll("[data-heat-filter]");

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const filter = button.dataset.heatFilter || "TODOS";
      state.currentHeatFilter = filter;

      filterButtons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");

      renderTransformersTable();
      renderSuspiciousInstallationsTable();
      renderMap();
      updateFilterPill();
    });
  });
}

async function runAgent() {
  setStatus("Executando agente sintético e atualizando painel...", "success");
  setText("context-agent-status", "Executando");

  try {
    await postJson(endpoints.runLossAgent);
    await postJson(endpoints.runFeederOperational);
    await loadDashboard();

    setStatus("Agente executado e painel atualizado com sucesso.", "success");
    setText("context-agent-status", "Atualizado");
    setText("context-updated-at", formatDateTime(new Date()));
  } catch (error) {
    setStatus(`Erro ao executar agente: ${error.message}`, "error");
    setText("context-agent-status", "Erro");
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
    renderExecutiveMetrics();
    renderCommercialMetrics();
    renderSectionsTable();
    renderReclosers();
    renderTransformersTable();
    renderSuspiciousInstallationsTable();
    renderMap();
    updateFilterPill();

    setStatus("Painel carregado com dados sintéticos operacionais.", "success");
    setText("context-agent-status", "Carregado");
    setText("context-updated-at", formatDateTime(new Date()));
  } catch (error) {
    setStatus(`Erro ao carregar painel: ${error.message}`, "error");
    setText("context-agent-status", "Erro");
  }
}

function renderMetrics() {
  const summary = state.summary || {};
  const substation = state.substations[0] || {};

  setText("feeder-code", summary.codigo_alimentador || "--");
  setText("context-feeder", summary.codigo_alimentador || "--");
  setText("context-substation", summary.codigo_subestacao || "--");

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

function renderExecutiveMetrics() {
  const criticalSection = getCriticalSection();
  const criticalRecloser = getCriticalRecloser();
  const criticalTransformer = getCriticalTransformer();
  const highHeatCount = state.transformers.filter((item) => normalizeHeat(item.nivel_calor) === "ALTO").length;

  setText("critical-section", criticalSection?.codigo_secao || "--");
  setText(
    "critical-section-detail",
    criticalSection
      ? `${formatNumber(criticalSection.perda_estimada_gwh, 3)} GWh | ${formatPercent(criticalSection.perda_percentual)}%`
      : "Maior concentração de perdas",
  );

  setText("critical-recloser", criticalRecloser?.codigo_religador || "--");
  setText(
    "critical-recloser-detail",
    criticalRecloser
      ? `${formatNumber(criticalRecloser.perda_jusante_gwh, 3)} GWh a jusante`
      : "Maior perda a jusante",
  );

  setText("critical-transformer", criticalTransformer?.codigo_transformador || "--");
  setText(
    "critical-transformer-detail",
    criticalTransformer
      ? `${formatNumber(criticalTransformer.perda_estimada_mwh, 2)} MWh estimados`
      : "Maior perda estimada",
  );

  setText("high-heat-count", formatInteger(highHeatCount));
  setText("legend-high-count", formatInteger(highHeatCount));
  setText("legend-medium-count", formatInteger(countByHeat("MEDIO")));
  setText("legend-low-count", formatInteger(countByHeat("BAIXO")));
}

function renderCommercialMetrics() {
  const suspiciousInstallations = buildSyntheticSuspiciousInstallations();

  const totals = suspiciousInstallations.reduce(
    (accumulator, item) => {
      accumulator.realNotes += toNumber(item.ntReal);
      accumulator.unproductiveNotes += toNumber(item.ntImprod);
      accumulator.fraudProcedures += toNumber(item.procFraud);
      accumulator.recoveredKwh += toNumber(item.kwhRecovered);
      return accumulator;
    },
    {
      realNotes: 0,
      unproductiveNotes: 0,
      fraudProcedures: 0,
      recoveredKwh: 0,
    },
  );

  setText("real-notes-count", formatInteger(totals.realNotes));
  setText("unproductive-notes-count", formatInteger(totals.unproductiveNotes));
  setText("fraud-procedure-count", formatInteger(totals.fraudProcedures));
  setText("recovered-kwh", formatInteger(totals.recoveredKwh));
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

  setText("recloser-count-pill", `${formatInteger(state.reclosers.length)} religadores`);
  list.innerHTML = "";

  if (state.reclosers.length === 0) {
    list.innerHTML = '<article class="empty-state">Nenhum religador sintético encontrado.</article>';
    return;
  }

  const rankedReclosers = [...state.reclosers].sort((left, right) => {
    return toNumber(right.perda_jusante_gwh) - toNumber(left.perda_jusante_gwh);
  });

  rankedReclosers.forEach((recloser) => {
    const item = document.createElement("article");
    item.className = "recloser-card";

    item.innerHTML = `
      <div class="recloser-card-header">
        <div>
          <strong>${escapeHtml(recloser.codigo_religador)}</strong>
          <p>Trecho protegido: ${escapeHtml(recloser.trecho)}</p>
        </div>
        ${heatBadge(recloser.nivel_calor)}
      </div>

      <div class="recloser-metrics">
        <span>Transformadores<strong>${formatInteger(recloser.transformadores_jusante)}</strong></span>
        <span>UC BT<strong>${formatInteger(recloser.uc_bt_jusante)}</strong></span>
        <span>UC MT<strong>${formatInteger(recloser.uc_mt_jusante)}</strong></span>
        <span>MMGD<strong>${formatInteger(recloser.gd_jusante)}</strong></span>
        <span>Consumo<strong>${formatNumber(recloser.consumo_jusante_gwh, 3)} GWh</strong></span>
        <span>Injetada<strong>${formatNumber(recloser.energia_injetada_jusante_gwh, 3)} GWh</strong></span>
        <span>Perda<strong>${formatNumber(recloser.perda_jusante_gwh, 3)} GWh</strong></span>
        <span>Perda percentual<strong>${formatPercent(recloser.perda_percentual_jusante)}%</strong></span>
      </div>
    `;

    list.appendChild(item);
  });
}

function renderTransformersTable() {
  const tableBody = document.getElementById("transformers-table-body");

  if (!tableBody) {
    return;
  }

  const rankedTransformers = getFilteredTransformers()
    .sort((left, right) => {
      return toNumber(right.perda_estimada_mwh) - toNumber(left.perda_estimada_mwh);
    })
    .slice(0, 10);

  tableBody.innerHTML = "";

  if (rankedTransformers.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="8">Nenhum transformador encontrado para o filtro selecionado.</td></tr>';
    return;
  }

  rankedTransformers.forEach((transformer, index) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${index + 1}</td>
      <td>${escapeHtml(transformer.codigo_transformador)}</td>
      <td>${escapeHtml(transformer.trecho)}</td>
      <td>${formatInteger(transformer.uc_bt)}</td>
      <td>${formatInteger(transformer.gd)}</td>
      <td>${formatNumber(transformer.energia_injetada_mwh, 2)}</td>
      <td><strong>${formatNumber(transformer.perda_estimada_mwh, 2)}</strong></td>
      <td>${heatBadge(transformer.nivel_calor)}</td>
    `;

    tableBody.appendChild(row);
  });
}

function renderSuspiciousInstallationsTable() {
  const tableBody = document.getElementById("suspicious-installations-table-body");

  if (!tableBody) {
    return;
  }

  const installations = buildSyntheticSuspiciousInstallations()
    .filter((item) => {
      if (state.currentHeatFilter === "TODOS") {
        return true;
      }

      return item.riskHeat === state.currentHeatFilter;
    })
    .sort((left, right) => right.riskScore - left.riskScore)
    .slice(0, 12);

  tableBody.innerHTML = "";

  if (installations.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="13">Nenhuma instalação encontrada para o filtro selecionado.</td></tr>';
    return;
  }

  installations.forEach((item, index) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${index + 1}</td>
      <td>${escapeHtml(item.installationCode)}</td>
      <td>${escapeHtml(item.sector)}</td>
      <td>${escapeHtml(item.transformerCode)}</td>
      <td>${formatInteger(item.ntReal)}</td>
      <td>${formatInteger(item.ntImprod)}</td>
      <td>${formatInteger(item.procFraud)}</td>
      <td>${formatInteger(item.procDefect)}</td>
      <td>${item.hasMmgd ? "Sim" : "Não"}</td>
      <td>${formatNumber(item.averageBilledKwh, 1)}</td>
      <td>${formatNumber(item.averageMeasuredKwh, 1)}</td>
      <td>${formatInteger(item.kwhRecovered)}</td>
      <td><span class="risk-score">${formatInteger(item.riskScore)}</span> ${heatBadge(item.riskHeat)}</td>
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

  if (!bounds) {
    return;
  }

  renderRouteLine(bounds);
  renderRoutePoints(map, bounds);
  renderTransformers(map, bounds);
  renderReclosersOnMap(map, bounds);
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
      if (
        point.tipo_ponto === "subestacao" ||
        point.tipo_ponto === "religador" ||
        point.tipo_ponto === "cliente_mt"
      ) {
        return;
      }

      const tooltip = [
        `Percurso: ${point.descricao}`,
        `Sequência: ${point.sequencia}`,
        `Alimentador: ${point.codigo_alimentador}`,
      ].join("\n");

      addMapPoint(map, bounds, point, "transformer baixo", tooltip, "BAIXO");
    });
}

function renderTransformers(map, bounds) {
  state.transformers
    .filter((point) => hasCoordinates(point))
    .forEach((transformer) => {
      const normalizedHeat = normalizeHeat(transformer.nivel_calor);
      const heatClass = heatClassName(normalizedHeat);
      const tooltip = [
        `Trafo: ${transformer.codigo_transformador}`,
        `Trecho: ${transformer.trecho}`,
        `UC BT: ${formatInteger(transformer.uc_bt)}`,
        `UC MT: ${formatInteger(transformer.uc_mt)}`,
        `MMGD: ${formatInteger(transformer.gd)}`,
        `Consumo: ${formatNumber(transformer.consumo_mensal_mwh, 2)} MWh`,
        `Injetada: ${formatNumber(transformer.energia_injetada_mwh, 2)} MWh`,
        `Perda: ${formatNumber(transformer.perda_estimada_mwh, 2)} MWh`,
        `Perda %: ${formatPercent(transformer.perda_percentual)}%`,
        `Calor: ${normalizedHeat}`,
      ].join("\n");

      addMapPoint(map, bounds, transformer, `transformer ${heatClass}`, tooltip, normalizedHeat);
    });
}

function renderReclosersOnMap(map, bounds) {
  state.reclosers
    .filter((point) => hasCoordinates(point))
    .forEach((recloser) => {
      const tooltip = [
        `Religador: ${recloser.codigo_religador}`,
        `Trecho: ${recloser.trecho}`,
        `Trafos a jusante: ${formatInteger(recloser.transformadores_jusante)}`,
        `UC BT a jusante: ${formatInteger(recloser.uc_bt_jusante)}`,
        `UC MT a jusante: ${formatInteger(recloser.uc_mt_jusante)}`,
        `MMGD a jusante: ${formatInteger(recloser.gd_jusante)}`,
        `Perda: ${formatNumber(recloser.perda_jusante_gwh, 3)} GWh`,
        `Perda %: ${formatPercent(recloser.perda_percentual_jusante)}%`,
      ].join("\n");

      addMapPoint(map, bounds, recloser, "recloser", tooltip, "TODOS");
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

      addMapPoint(map, bounds, customer, "mt", tooltip, "TODOS");
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

      addMapPoint(map, bounds, substation, "substation", tooltip, "TODOS");
    });
}

function addMapPoint(map, bounds, point, className, tooltip, heatLevel) {
  if (!map || !bounds || !point || !hasCoordinates(point)) {
    return;
  }

  const position = projectPoint(point, bounds);
  const element = document.createElement("button");
  const normalizedHeat = normalizeHeat(heatLevel);

  element.type = "button";
  element.className = `map-point ${className}`;
  element.style.left = `${position.x}%`;
  element.style.top = `${position.y}%`;
  element.dataset.tooltip = tooltip;

  if (
    state.currentHeatFilter !== "TODOS" &&
    normalizedHeat !== "TODOS" &&
    normalizedHeat !== state.currentHeatFilter
  ) {
    element.classList.add("hidden-by-filter");
  }

  map.appendChild(element);
}

function buildSyntheticSuspiciousInstallations() {
  const selectedTransformers = [...state.transformers]
    .sort((left, right) => {
      return toNumber(right.perda_estimada_mwh) - toNumber(left.perda_estimada_mwh);
    })
    .slice(0, 36);

  return selectedTransformers.map((transformer, index) => {
    const loss = toNumber(transformer.perda_estimada_mwh);
    const billedKwh = Math.max(120, toNumber(transformer.consumo_mensal_mwh) * 31);
    const measuredKwh = Math.max(80, billedKwh - loss * 18 - (index % 4) * 27);
    const hasMmgd = toNumber(transformer.gd) > 0;
    const ntReal = loss > 11 ? 3 : loss > 8 ? 2 : 1;
    const ntImprod = index % 5 === 0 ? 2 : index % 3 === 0 ? 1 : 0;
    const procFraud = loss > 10 ? 1 + (index % 2) : index % 7 === 0 ? 1 : 0;
    const procDefect = loss > 8 && index % 3 === 0 ? 1 : 0;
    const kwhRecovered = Math.round(loss * 95 + procFraud * 240 + procDefect * 120);
    const riskScore = calculateSyntheticRiskScore({
      loss,
      billedKwh,
      measuredKwh,
      ntReal,
      ntImprod,
      procFraud,
      procDefect,
      hasMmgd,
      kwhRecovered,
    });

    return {
      installationCode: `INS-${String(index + 1).padStart(6, "0")}`,
      sector: transformer.trecho || `S${(index % 4) + 1}`,
      transformerCode: transformer.codigo_transformador,
      ntReal,
      ntImprod,
      procFraud,
      procDefect,
      hasMmgd,
      averageBilledKwh: billedKwh,
      averageMeasuredKwh: measuredKwh,
      kwhRecovered,
      riskScore,
      riskHeat: classifySyntheticRisk(riskScore),
    };
  });
}

function calculateSyntheticRiskScore(input) {
  const consumptionGap = Math.max(0, input.billedKwh - input.measuredKwh);
  let score = 0;

  score += Math.min(30, input.loss * 2);
  score += Math.min(20, consumptionGap / 35);
  score += input.ntReal * 5;
  score += input.ntImprod * 2;
  score += input.procFraud * 15;
  score += input.procDefect * 8;
  score += input.hasMmgd ? 4 : 0;
  score += Math.min(12, input.kwhRecovered / 180);

  return Math.round(Math.min(100, score));
}

function classifySyntheticRisk(score) {
  if (score >= 70) {
    return "ALTO";
  }

  if (score >= 45) {
    return "MEDIO";
  }

  return "BAIXO";
}

function getFilteredTransformers() {
  if (state.currentHeatFilter === "TODOS") {
    return [...state.transformers];
  }

  return state.transformers.filter((transformer) => {
    return normalizeHeat(transformer.nivel_calor) === state.currentHeatFilter;
  });
}

function getCriticalSection() {
  return [...state.sections].sort((left, right) => {
    return toNumber(right.perda_estimada_gwh) - toNumber(left.perda_estimada_gwh);
  })[0];
}

function getCriticalRecloser() {
  return [...state.reclosers].sort((left, right) => {
    return toNumber(right.perda_jusante_gwh) - toNumber(left.perda_jusante_gwh);
  })[0];
}

function getCriticalTransformer() {
  return [...state.transformers].sort((left, right) => {
    return toNumber(right.perda_estimada_mwh) - toNumber(left.perda_estimada_mwh);
  })[0];
}

function countByHeat(heatLevel) {
  return state.transformers.filter((item) => normalizeHeat(item.nivel_calor) === heatLevel).length;
}

function updateFilterPill() {
  const text = state.currentHeatFilter === "TODOS" ? "Todos" : `Calor ${state.currentHeatFilter.toLowerCase()}`;
  setText("transformer-filter-pill", text);
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
  const normalizedLevel = normalizeHeat(level);
  const className = heatClassName(normalizedLevel);

  return `<span class="badge ${className}">${escapeHtml(normalizedLevel)}</span>`;
}

function heatClassName(level) {
  const normalizedLevel = normalizeHeat(level);

  if (normalizedLevel === "ALTO") {
    return "alto";
  }

  if (normalizedLevel === "MEDIO") {
    return "medio";
  }

  return "baixo";
}

function normalizeHeat(level) {
  const normalizedLevel = String(level || "BAIXO")
    .trim()
    .toUpperCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

  if (normalizedLevel === "HIGH") {
    return "ALTO";
  }

  if (normalizedLevel === "MEDIUM") {
    return "MEDIO";
  }

  if (normalizedLevel === "LOW") {
    return "BAIXO";
  }

  if (normalizedLevel === "TODOS") {
    return "TODOS";
  }

  if (["ALTO", "MEDIO", "BAIXO"].includes(normalizedLevel)) {
    return normalizedLevel;
  }

  return "BAIXO";
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

function formatDateTime(value) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(value);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}