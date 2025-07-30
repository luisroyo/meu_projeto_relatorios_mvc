// app/static/js/index_page/reportLogic.js
import { CONFIG, DOMElements } from "./config.js";
import {
  updateCharCount,
  displayStatus,
  setProcessingUI,
  showCopyFeedback,
  tryFallbackCopy,
  resetOutputUI,
  updateReportUI,
  updateEmailReportUI,
} from "./uiHandlers.js";
import { callProcessReportAPI } from "./apiService.js";

/**
 * Cria e exibe o botão para registar o relatório como uma ocorrência oficial.
 * Esta função é chamada internamente após o sucesso do processamento da IA.
 * @param {string} logBruto O texto original que o utilizador inseriu.
 * @param {string} relatorioProcessado O texto final corrigido pela IA.
 */
function exibirBotaoRegistrarOcorrencia(logBruto, relatorioProcessado) {
  // Encontra o container onde os botões de ação (copiar, whatsapp) são inseridos.
  const containerBotoes = document.querySelector("#resultadoProcessamento")
    .parentElement.nextElementSibling;
  if (!containerBotoes) {
    console.error(
      "Container de botões para o relatório padrão não foi encontrado."
    );
    return;
  }

  // Remove qualquer botão antigo para evitar duplicados se o utilizador processar novamente.
  const botaoAntigo = document.getElementById("registrarOcorrenciaOficial");
  if (botaoAntigo) {
    botaoAntigo.remove();
  }

  const botaoSalvar = document.createElement("button");
  botaoSalvar.id = "registrarOcorrenciaOficial";
  botaoSalvar.type = "button";
  botaoSalvar.className = "btn btn-success btn-lg w-100 mt-2";
  botaoSalvar.innerHTML =
    '<i class="bi bi-shield-plus me-2"></i>Registrar Ocorrência Oficial';
  botaoSalvar.setAttribute("data-bs-toggle", "tooltip");
  botaoSalvar.setAttribute("data-bs-placement", "top");
  botaoSalvar.setAttribute(
    "title",
    "Salva este relatório como um registo oficial no sistema de rondas."
  );

  // Adiciona o evento de clique que guarda os dados e redireciona.
  botaoSalvar.addEventListener("click", () => {
    localStorage.setItem("novoLogRondaBruto", logBruto);
    localStorage.setItem("novoRelatorioProcessado", relatorioProcessado);
    window.location.href = "/ocorrencias/registrar";
  });

  // Insere o novo botão no topo da pilha de botões de ação.
  containerBotoes.prepend(botaoSalvar);

  // Ativa o tooltip do Bootstrap para o novo botão.
  new bootstrap.Tooltip(botaoSalvar);
}

export async function handleProcessReport() {
  if (!DOMElements.relatorioBruto || !DOMElements.resultadoProcessamento)
    return false;

  if (
    DOMElements.btnProcessar &&
    !DOMElements.btnProcessar.dataset.originalHTML
  ) {
    DOMElements.btnProcessar.dataset.originalHTML =
      DOMElements.btnProcessar.innerHTML;
  }

  const relatorioBrutoValue = DOMElements.relatorioBruto.value;
  const formatarParaEmailChecked = DOMElements.formatarParaEmailCheckbox
    ? DOMElements.formatarParaEmailCheckbox.checked
    : false;

  resetOutputUI(formatarParaEmailChecked);

  if (!relatorioBrutoValue.trim()) {
    displayStatus(CONFIG.messages.emptyReport, "warning", "standard");
    if (DOMElements.relatorioBruto) DOMElements.relatorioBruto.focus();
    return false;
  }
  if (relatorioBrutoValue.length > CONFIG.maxInputLengthFrontend) {
    displayStatus(
      CONFIG.messages.reportTooLongFrontend(
        CONFIG.maxInputLengthFrontend,
        relatorioBrutoValue.length
      ),
      "danger",
      "standard"
    );
    if (DOMElements.relatorioBruto) DOMElements.relatorioBruto.focus();
    return false;
  }

  setProcessingUI(true);
  displayStatus(CONFIG.messages.processing, "info", "standard");
  if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
    displayStatus(CONFIG.messages.processing, "info", "email");
  }

  try {
    const data = await callProcessReportAPI(
      relatorioBrutoValue,
      formatarParaEmailChecked
    );
    const standardReportSuccess = updateReportUI(data);

    // --- INTEGRAÇÃO CORRIGIDA ---
    // Se o relatório padrão foi gerado com sucesso, mostramos o botão para salvar.
    if (standardReportSuccess) {
      const relatorioBrutoOriginal = DOMElements.relatorioBruto.value;
      // CORREÇÃO: Usar 'relatorio_processado' para consistência com a resposta da API.
      const relatorioProcessadoFinal = data.relatorio_processado;
      exibirBotaoRegistrarOcorrencia(
        relatorioBrutoOriginal,
        relatorioProcessadoFinal
      );
    }
    // --- FIM DA CORREÇÃO ---

    if (formatarParaEmailChecked) {
      if (DOMElements.colunaRelatorioEmail)
        DOMElements.colunaRelatorioEmail.style.display = "block";
      updateEmailReportUI(data);
    } else {
      if (DOMElements.colunaRelatorioEmail)
        DOMElements.colunaRelatorioEmail.style.display = "none";
    }

    return standardReportSuccess; // Retorna o status do sucesso para o main.js
  } catch (error) {
    console.error("Erro em handleProcessReport:", error);
    let userErrorMessage =
      error.message || CONFIG.messages.communicationFailure;
    displayStatus(userErrorMessage, "danger", "standard");
    if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
      if (DOMElements.colunaRelatorioEmail)
        DOMElements.colunaRelatorioEmail.style.display = "block";
      displayStatus(userErrorMessage, "danger", "email");
    }
    return false; // Retorna falso em caso de erro
  } finally {
    setProcessingUI(false);
  }
}

export function handleClearFields() {
  if (DOMElements.relatorioBruto) {
    DOMElements.relatorioBruto.value = "";
    updateCharCount();
    DOMElements.relatorioBruto.focus();
  }
  if (DOMElements.formatarParaEmailCheckbox) {
    DOMElements.formatarParaEmailCheckbox.checked = false;
    if (DOMElements.colunaRelatorioEmail)
      DOMElements.colunaRelatorioEmail.style.display = "none";
  }
  resetOutputUI(false);

  // Remove o botão de registrar ocorrência se ele existir
  const botaoRegistrar = document.getElementById("registrarOcorrenciaOficial");
  if (botaoRegistrar) {
    botaoRegistrar.remove();
  }
}

export function handleCopyResult(target = "standard") {
  let textoParaCopiar = "";
  let buttonElement = null;

  if (
    target === "email" &&
    DOMElements.resultadoEmail &&
    DOMElements.btnCopiarEmail
  ) {
    textoParaCopiar = DOMElements.resultadoEmail.value;
    buttonElement = DOMElements.btnCopiarEmail;
  } else if (
    target === "standard" &&
    DOMElements.resultadoProcessamento &&
    DOMElements.btnCopiar
  ) {
    textoParaCopiar = DOMElements.resultadoProcessamento.value;
    buttonElement = DOMElements.btnCopiar;
  }

  if (!buttonElement) return;

  if (!buttonElement.dataset.originalHTML) {
    buttonElement.dataset.originalHTML = buttonElement.innerHTML;
  }

  if (!textoParaCopiar || !textoParaCopiar.trim()) {
    alert("Nada para copiar!");
    return;
  }

  if (navigator.clipboard) {
    navigator.clipboard
      .writeText(textoParaCopiar)
      .then(() => showCopyFeedback(buttonElement))
      .catch((err) => {
        console.error("Falha ao copiar com navigator.clipboard: ", err);
        tryFallbackCopy(textoParaCopiar, buttonElement);
      });
  } else {
    tryFallbackCopy(textoParaCopiar, buttonElement);
  }
}

export function handleSendToWhatsApp(target = "standard") {
  let textoParaEnviar = "";

  if (target === "email" && DOMElements.resultadoEmail) {
    textoParaEnviar = DOMElements.resultadoEmail.value;
  } else if (target === "standard" && DOMElements.resultadoProcessamento) {
    textoParaEnviar = DOMElements.resultadoProcessamento.value;
  }

  if (!textoParaEnviar || !textoParaEnviar.trim()) {
    alert("Nada para enviar via WhatsApp!");
    return;
  }

  const textoCodificado = encodeURIComponent(textoParaEnviar.trim());
  
  // Função para tentar abrir WhatsApp com fallback para web
  const openWhatsApp = (text) => {
    const isMobile = CONFIG.isMobile();
    
    if (isMobile) {
      // Para mobile: tentar app primeiro, depois web
      const appUrl = `whatsapp://send?text=${text}`;
      const webUrl = `https://wa.me/?text=${text}`;
      
      // Tentar abrir o app
      const appWindow = window.open(appUrl, '_blank');
      
      // Se o app não abrir em 1 segundo, tentar web
      setTimeout(() => {
        if (appWindow && appWindow.closed) {
          // App não abriu, tentar web
          window.open(webUrl, '_blank');
        }
      }, 1000);
      
    } else {
      // Para desktop: sempre usar web
      const webUrl = `https://wa.me/?text=${text}`;
      window.open(webUrl, '_blank');
    }
  };
  
  openWhatsApp(textoCodificado);
}
