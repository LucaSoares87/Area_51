const resultElement = document.getElementById("result");
const friendlyResultElement = document.getElementById("friendlyResult");
const operationStatusElement = document.getElementById("operationStatus");

const summaryTypeElement = document.getElementById("summaryType");
const summaryQueryElement = document.getElementById("summaryQuery");
const summaryRecordsElement = document.getElementById("summaryRecords");
const summaryStatusElement = document.getElementById("summaryStatus");

function getValue(id) {
  return document.getElementById(id).value.trim();
}

function setStatus(message, statusClass) {
  operationStatusElement.textContent = message;
  operationStatusElement.className = `status-text ${statusClass}`;
  summaryStatusElement.textContent = message;
}

function updateSummary({ type = "-", query = "-", records = "-" }) {
  summaryTypeElement.textContent = type;
  summaryQueryElement.textContent = query;
  summaryRecordsElement.textContent = String(records);
}

function showResult(data) {
  resultElement.textContent = JSON.stringify(data, null, 2);
  renderFriendlyResult(data);
}

function showError(error) {
  const payload = {
    status: "error",
    message: error.message || String(error),
  };

  resultElement.textContent = JSON.stringify(payload, null, 2);
  friendlyResultElement.textContent = payload.message;
  updateSummary({ type: "Erro", query: "-", records: "-" });
  setStatus("Erro", "error");
}

function setLoading(message) {
  friendlyResultElement.textContent = message;
  setStatus("Processando", "loading");
}

async function requestJson(url, options = {}) {
  setLoading("Aguardando resposta da API...");

  const response = await fetch(url, options);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Falha na requisição.");
  }

  setStatus("Concluído", "success");
  return data;
}

function renderFriendlyResult(data) {
  if (!data || Object.keys(data).length === 0) {
    friendlyResultElement.textContent = "Execute uma busca ou envie uma imagem para visualizar o resultado.";
    updateSummary({ type: "-", query: "-", records: "-" });
    setStatus("Aguardando", "neutral");
    return;
  }

  if (data.analysis_id) {
    renderUploadResult(data);
    return;
  }

  if (data.records) {
    renderListResult(data);
    return;
  }

  renderSingleSearchResult(data);
}

function renderUploadResult(data) {
  updateSummary({
    type: "Upload de imagem",
    query: data.filename || "-",
    records: data.estimated_roofs ?? "-",
  });

  friendlyResultElement.innerHTML = `
    <strong>Imagem analisada:</strong> ${escapeHtml(data.filename || "-")}<br>
    <strong>Status:</strong> ${escapeHtml(data.status || "-")}<br>
    <strong>Telhados estimados:</strong> ${data.estimated_roofs ?? 0}<br>
    <strong>Confiança média:</strong> ${formatPercent(data.confidence_score)}<br>
    <strong>ID da análise:</strong> ${escapeHtml(data.analysis_id || "-")}
  `;
}

function renderListResult(data) {
  updateSummary({
    type: data.search_type || "-",
    query: data.query || "-",
    records: data.total_records ?? data.records.length,
  });

  if (!data.records.length) {
    friendlyResultElement.innerHTML = `
      Nenhum registro encontrado para <strong>${escapeHtml(data.query || "-")}</strong>.
    `;
    return;
  }

  const items = data.records
    .map((record) => renderAssetLine(record.asset))
    .join("<hr>");

  friendlyResultElement.innerHTML = items;
}

function renderSingleSearchResult(data) {
  updateSummary({
    type: data.search_type || "-",
    query: data.query || "-",
    records: data.asset ? 1 : 0,
  });

  if (!data.asset) {
    friendlyResultElement.innerHTML = `
      Nenhum ativo encontrado para <strong>${escapeHtml(data.query || "-")}</strong>.
    `;
    return;
  }

  const distanceLine = data.distance_meters
    ? `<br><strong>Distância:</strong> ${Number(data.distance_meters).toFixed(2)} m`
    : "";

  friendlyResultElement.innerHTML = `
    ${renderAssetLine(data.asset)}
    ${distanceLine}
  `;
}

function renderAssetLine(asset) {
  if (!asset) {
    return "Ativo não encontrado.";
  }

  return `
    <strong>Área:</strong> ${escapeHtml(asset.area_id || "-")}<br>
    <strong>Transformador:</strong> ${escapeHtml(asset.transformer_code || "-")}<br>
    <strong>Alimentador:</strong> ${escapeHtml(asset.feeder_code || "-")}<br>
    <strong>Subestação:</strong> ${escapeHtml(asset.substation_code || "-")}<br>
    <strong>Localidade:</strong> ${escapeHtml(asset.neighborhood || "-")} - ${escapeHtml(asset.city || "-")}
  `;
}

async function searchCustomer() {
  try {
    const customerId = getValue("customerId");
    const referenceMonth = getValue("referenceMonth");

    if (!customerId) {
      throw new Error("Informe a matrícula.");
    }

    const data = await requestJson(
      `/operational/search/customer/${encodeURIComponent(customerId)}?reference_month=${encodeURIComponent(referenceMonth)}`,
    );

    showResult(data);
  } catch (error) {
    showError(error);
  }
}

async function searchTransformer() {
  try {
    const transformerCode = getValue("transformerCode");

    if (!transformerCode) {
      throw new Error("Informe o código do transformador.");
    }

    const data = await requestJson(
      `/operational/search/transformer/${encodeURIComponent(transformerCode)}`,
    );

    showResult(data);
  } catch (error) {
    showError(error);
  }
}

async function searchFeeder() {
  try {
    const feederCode = getValue("feederCode");

    if (!feederCode) {
      throw new Error("Informe o código do alimentador.");
    }

    const data = await requestJson(
      `/operational/search/feeder/${encodeURIComponent(feederCode)}`,
    );

    showResult(data);
  } catch (error) {
    showError(error);
  }
}

async function searchSubstation() {
  try {
    const substationCode = getValue("substationCode");

    if (!substationCode) {
      throw new Error("Informe o código da subestação.");
    }

    const data = await requestJson(
      `/operational/search/substation/${encodeURIComponent(substationCode)}`,
    );

    showResult(data);
  } catch (error) {
    showError(error);
  }
}

async function searchCoordinates() {
  try {
    const latitude = getValue("latitude");
    const longitude = getValue("longitude");

    if (!latitude || !longitude) {
      throw new Error("Informe latitude e longitude.");
    }

    const data = await requestJson(
      `/operational/search/coordinates?latitude=${encodeURIComponent(latitude)}&longitude=${encodeURIComponent(longitude)}`,
    );

    showResult(data);
  } catch (error) {
    showError(error);
  }
}

async function uploadRoofImage() {
  try {
    const input = document.getElementById("roofImage");

    if (!input.files || input.files.length === 0) {
      throw new Error("Selecione uma imagem.");
    }

    const formData = new FormData();
    formData.append("file", input.files[0]);

    const data = await requestJson("/roof/upload", {
      method: "POST",
      body: formData,
    });

    showResult(data);
  } catch (error) {
    showError(error);
  }
}

function previewSelectedImage() {
  const input = document.getElementById("roofImage");
  const previewCard = document.getElementById("imagePreviewCard");
  const preview = document.getElementById("imagePreview");
  const imageName = document.getElementById("imageName");
  const imageSize = document.getElementById("imageSize");

  if (!input.files || input.files.length === 0) {
    previewCard.classList.add("hidden");
    return;
  }

  const file = input.files[0];
  const objectUrl = URL.createObjectURL(file);

  preview.src = objectUrl;
  imageName.textContent = file.name;
  imageSize.textContent = formatFileSize(file.size);
  previewCard.classList.remove("hidden");
}

function clearResult() {
  showResult({});
}

function formatPercent(value) {
  const numericValue = Number(value || 0);
  return `${(numericValue * 100).toFixed(2)}%`;
}

function formatFileSize(sizeBytes) {
  if (!sizeBytes) {
    return "0 KB";
  }

  const sizeKb = sizeBytes / 1024;

  if (sizeKb < 1024) {
    return `${sizeKb.toFixed(2)} KB`;
  }

  return `${(sizeKb / 1024).toFixed(2)} MB`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}