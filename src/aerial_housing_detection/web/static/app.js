const resultElement = document.getElementById("result");

function getValue(id) {
  return document.getElementById(id).value.trim();
}

function showResult(data) {
  resultElement.textContent = JSON.stringify(data, null, 2);
}

function showError(error) {
  showResult({
    status: "error",
    message: error.message || String(error),
  });
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Falha na requisição.");
  }

  return data;
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

function clearResult() {
  showResult({});
}