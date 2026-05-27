const registrationInput = document.getElementById("employeeRegistration");
const rememberAccessInput = document.getElementById("rememberAccess");
const loginMessageElement = document.getElementById("loginMessage");
const passwordInput = document.getElementById("password");
const togglePasswordButton = document.getElementById("togglePasswordButton");

const rememberedRegistration = localStorage.getItem("area51_employee_registration");

if (rememberedRegistration) {
  registrationInput.value = rememberedRegistration;
  rememberAccessInput.checked = true;
}

function handleLogin(event) {
  event.preventDefault();

  const registration = registrationInput.value.trim();
  const password = passwordInput.value.trim();

  if (!registration) {
    showMessage("Informe sua matrícula funcional.", "error");
    return;
  }

  if (!password) {
    showMessage("Informe sua senha de acesso.", "error");
    return;
  }

  if (rememberAccessInput.checked) {
    localStorage.setItem("area51_employee_registration", registration);
  } else {
    localStorage.removeItem("area51_employee_registration");
  }

  sessionStorage.setItem("area51_visual_login", "active");
  sessionStorage.setItem("area51_employee_registration", registration);

  showMessage("Acesso validado localmente. Redirecionando...", "success");

  window.setTimeout(() => {
    window.location.href = "/app";
  }, 500);
}

function togglePasswordVisibility() {
  const isPasswordHidden = passwordInput.type === "password";

  passwordInput.type = isPasswordHidden ? "text" : "password";
  togglePasswordButton.textContent = isPasswordHidden ? "Ocultar" : "Ver";
  togglePasswordButton.setAttribute(
    "aria-label",
    isPasswordHidden ? "Ocultar senha" : "Mostrar senha",
  );
  togglePasswordButton.setAttribute(
    "aria-pressed",
    isPasswordHidden ? "true" : "false",
  );
}

function showAccessInfo(event) {
  event.preventDefault();

  showMessage(
    "O primeiro acesso deve ser liberado pelo setor responsável, com matrícula, perfil e senha inicial.",
    "success",
  );
}

function showMessage(message, status) {
  loginMessageElement.textContent = message;
  loginMessageElement.className = `login-message ${status}`;
}