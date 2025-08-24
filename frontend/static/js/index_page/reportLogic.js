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
  console.log('exibirBotaoRegistrarOcorrencia: Iniciando...');
  console.log('exibirBotaoRegistrarOcorrencia: logBruto:', logBruto ? logBruto.substring(0, 100) + '...' : 'N/A');
  console.log('exibirBotaoRegistrarOcorrencia: relatorioProcessado:', relatorioProcessado ? relatorioProcessado.substring(0, 100) + '...' : 'N/A');
  
  // Encontra o container específico para botões de ação
  const containerBotoes = document.querySelector("#container-botoes-acoes");
  if (!containerBotoes) {
    console.error(
      "Container de botões para o relatório padrão não foi encontrado."
    );
    return;
  }
  
  console.log('exibirBotaoRegistrarOcorrencia: Container encontrado:', containerBotoes);
  
  // Mostra o container
  containerBotoes.style.display = "flex";

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
  
  console.log('exibirBotaoRegistrarOcorrencia: Botão criado e inserido com sucesso');
}

export async function handleProcessReport() {
  console.log('handleProcessReport: Iniciando...');
  console.log('handleProcessReport: DOMElements disponíveis:', Object.keys(DOMElements));
  console.log('handleProcessReport: btnProcessar:', DOMElements.btnProcessar);
  console.log('handleProcessReport: btnCopiar:', DOMElements.btnCopiar);
  
  if (!DOMElements.relatorioBruto || !DOMElements.resultadoProcessamento) {
    console.error('handleProcessReport: Elementos essenciais não encontrados');
    return false;
  }

  if (
    DOMElements.btnProcessar &&
    !DOMElements.btnProcessar.dataset.originalHTML
  ) {
    DOMElements.btnProcessar.dataset.originalHTML =
      DOMElements.btnProcessar.innerHTML;
    console.log('handleProcessReport: HTML original do botão salvo:', DOMElements.btnProcessar.dataset.originalHTML);
  }

  const relatorioBrutoValue = DOMElements.relatorioBruto.value;
  const formatarParaEmailChecked = DOMElements.formatarParaEmailCheckbox
    ? DOMElements.formatarParaEmailCheckbox.checked
    : false;

  console.log('handleProcessReport: Chamando resetOutputUI...');
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

  console.log('handleProcessReport: Chamando setProcessingUI(true)...');
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
    console.log('handleProcessReport: Dados recebidos da API:', data);
    const standardReportSuccess = updateReportUI(data);
    console.log('handleProcessReport: Resultado do updateReportUI:', standardReportSuccess);

    // --- INTEGRAÇÃO CORRIGIDA ---
    // Se o relatório padrão foi gerado com sucesso, mostramos o botão para salvar.
    if (standardReportSuccess) {
      console.log('handleProcessReport: Exibindo botão de registrar ocorrência...');
      const relatorioBrutoOriginal = DOMElements.relatorioBruto.value;
      // CORREÇÃO: Usar 'relatorio_processado' para consistência com a resposta da API.
      const relatorioProcessadoFinal = data.relatorio_processado;
      exibirBotaoRegistrarOcorrencia(
        relatorioBrutoOriginal,
        relatorioProcessadoFinal
      );
    } else {
      console.log('handleProcessReport: Não foi possível exibir botão de registrar ocorrência');
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

    console.log('handleProcessReport: Processamento concluído com sucesso');
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
    console.log('handleProcessReport: Chamando setProcessingUI(false)...');
    setProcessingUI(false);
  }
}

export function handleClearFields() {
  console.log('handleClearFields: Iniciando...');
  
  if (DOMElements.relatorioBruto) {
    DOMElements.relatorioBruto.value = "";
    updateCharCount();
    DOMElements.relatorioBruto.focus();
    console.log('handleClearFields: Campo relatório bruto limpo');
  } else {
    console.warn('handleClearFields: Campo relatório bruto não encontrado');
  }
  
  if (DOMElements.formatarParaEmailCheckbox) {
    DOMElements.formatarParaEmailCheckbox.checked = false;
    if (DOMElements.colunaRelatorioEmail)
      DOMElements.colunaRelatorioEmail.style.display = "none";
    console.log('handleClearFields: Checkbox de email desmarcado');
  } else {
    console.warn('handleClearFields: Checkbox de email não encontrado');
  }
  
  console.log('handleClearFields: Chamando resetOutputUI...');
  resetOutputUI(false);

  // Remove o botão de registrar ocorrência se ele existir
  const botaoRegistrar = document.getElementById("registrarOcorrenciaOficial");
  if (botaoRegistrar) {
    botaoRegistrar.remove();
    console.log('handleClearFields: Botão de registrar ocorrência removido');
  } else {
    console.log('handleClearFields: Botão de registrar ocorrência não encontrado');
  }
  
  console.log('handleClearFields: Concluído');
}

export function handleCopyResult(target = "standard") {
  console.log('handleCopyResult: Iniciando com target:', target);
  console.log('handleCopyResult: DOMElements disponíveis:', Object.keys(DOMElements));
  console.log('handleCopyResult: btnCopiar:', DOMElements.btnCopiar);
  console.log('handleCopyResult: btnCopiarEmail:', DOMElements.btnCopiarEmail);
  
  let textoParaCopiar = "";
  let buttonElement = null;

  if (
    target === "email" &&
    DOMElements.resultadoEmail &&
    DOMElements.btnCopiarEmail
  ) {
    textoParaCopiar = DOMElements.resultadoEmail.value;
    buttonElement = DOMElements.btnCopiarEmail;
    console.log('handleCopyResult: Usando botão de copiar email');
  } else if (
    target === "standard" &&
    DOMElements.resultadoProcessamento &&
    DOMElements.btnCopiar
  ) {
    textoParaCopiar = DOMElements.resultadoProcessamento.value;
    buttonElement = DOMElements.btnCopiar;
    console.log('handleCopyResult: Usando botão de copiar padrão');
  }

  if (!buttonElement) {
    console.error('handleCopyResult: Nenhum botão encontrado para o target:', target);
    return;
  }

  if (!buttonElement.dataset.originalHTML) {
    buttonElement.dataset.originalHTML = buttonElement.innerHTML;
  }

  if (!textoParaCopiar || !textoParaCopiar.trim()) {
    alert("Nada para copiar!");
    return;
  }

  console.log('handleCopyResult: Tentando copiar texto com length:', textoParaCopiar.length);
  
  if (navigator.clipboard) {
    console.log('handleCopyResult: Usando navigator.clipboard');
    navigator.clipboard
      .writeText(textoParaCopiar)
      .then(() => {
        console.log('handleCopyResult: Texto copiado com sucesso via navigator.clipboard');
        showCopyFeedback(buttonElement);
      })
      .catch((err) => {
        console.error("Falha ao copiar com navigator.clipboard: ", err);
        tryFallbackCopy(textoParaCopiar, buttonElement);
      });
  } else {
    console.log('handleCopyResult: Usando fallback copy');
    tryFallbackCopy(textoParaCopiar, buttonElement);
  }
}

export function handleSendToWhatsApp(target = "standard") {
  console.log('handleSendToWhatsApp: Iniciando com target:', target);
  console.log('handleSendToWhatsApp: DOMElements disponíveis:', Object.keys(DOMElements));
  
  let textoParaEnviar = "";

  if (target === "email" && DOMElements.resultadoEmail) {
    textoParaEnviar = DOMElements.resultadoEmail.value;
    console.log('handleSendToWhatsApp: Usando resultado de email');
  } else if (target === "standard" && DOMElements.resultadoProcessamento) {
    textoParaEnviar = DOMElements.resultadoProcessamento.value;
    console.log('handleSendToWhatsApp: Usando resultado padrão');
  } else {
    console.warn('handleSendToWhatsApp: Elementos não encontrados para target:', target);
  }

  if (!textoParaEnviar || !textoParaEnviar.trim()) {
    console.warn('handleSendToWhatsApp: Nada para enviar');
    alert("Nada para enviar via WhatsApp!");
    return;
  }

  const textoCodificado = encodeURIComponent(textoParaEnviar.trim());
  console.log('handleSendToWhatsApp: Texto codificado:', textoCodificado.substring(0, 100) + '...');
  
  // Função para tentar abrir WhatsApp com fallback para web
  const openWhatsApp = (text) => {
    const isMobile = CONFIG.isMobile();
    console.log('handleSendToWhatsApp: Dispositivo mobile:', isMobile);
    
    if (isMobile) {
      // Para mobile: tentar app primeiro, depois web
      const appUrl = `whatsapp://send?text=${text}`;
      const webUrl = `https://wa.me/?text=${text}`;
      
      console.log('handleSendToWhatsApp: Tentando abrir app mobile');
      
      // Tentar abrir o app
      const appWindow = window.open(appUrl, '_blank');
      
      // Se o app não abrir em 1 segundo, tentar web
      setTimeout(() => {
        if (appWindow && appWindow.closed) {
          // App não abriu, tentar web
          console.log('handleSendToWhatsApp: App não abriu, tentando web');
          window.open(webUrl, '_blank');
        }
      }, 1000);
      
    } else {
      // Para desktop: sempre usar web
      const webUrl = `https://wa.me/?text=${text}`;
      console.log('handleSendToWhatsApp: Abrindo WhatsApp web');
      window.open(webUrl, '_blank');
    }
  };
  
  console.log('handleSendToWhatsApp: Chamando openWhatsApp...');
  openWhatsApp(textoCodificado);
  console.log('handleSendToWhatsApp: Concluído');
}
