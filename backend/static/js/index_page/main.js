// app/static/js/index_page/main.js
import { CONFIG, DOMElements, initializeDOMElements } from "./config.js";
import { updateCharCount, displayStatus } from "./uiHandlers.js";
import {
  handleProcessReport,
  handleClearFields,
  handleCopyResult,
  handleSendToWhatsApp,
} from "./reportLogic.js";

// Cache para elementos DOM frequentemente acessados
const DOMCache = new Map();

// Função para obter elemento DOM com cache
function getCachedElement(key) {
  if (!DOMCache.has(key)) {
    DOMCache.set(key, DOMElements[key]);
  }
  const element = DOMCache.get(key);
  
  // Log para debug
  if (!element) {
    console.warn(`getCachedElement: Elemento não encontrado para chave: ${key}`);
    console.warn(`getCachedElement: DOMElements[${key}]:`, DOMElements[key]);
    console.warn(`getCachedElement: DOMElements disponíveis:`, Object.keys(DOMElements));
  }
  
  return element;
}

// Função para inicializar botões com HTML inicial
function initializeButton(buttonKey, configKey) {
  const button = getCachedElement(buttonKey);
  if (button && CONFIG[configKey]) {
    button.innerHTML = CONFIG[configKey];
    button.dataset.originalHTML = button.innerHTML;
  }
}

// Função para configurar event listeners
function setupEventListeners() {
  // Botão processar
  const btnProcessar = getCachedElement('btnProcessar');
  if (btnProcessar) {
    btnProcessar.addEventListener("click", handleProcessReport);
    console.log('main.js: Event listener adicionado ao botão processar');
  } else {
    console.warn('main.js: Botão processar não encontrado');
  }

  // Botão copiar padrão
  const btnCopiar = getCachedElement('btnCopiar');
  if (btnCopiar) {
    btnCopiar.addEventListener("click", () => handleCopyResult("standard"));
    btnCopiar.style.display = "none";
    console.log('main.js: Event listener adicionado ao botão copiar, display definido como none');
  } else {
    console.warn('main.js: Botão copiar não encontrado');
  }

  // Botão copiar email
  const btnCopiarEmail = getCachedElement('btnCopiarEmail');
  if (btnCopiarEmail) {
    btnCopiarEmail.addEventListener("click", () => handleCopyResult("email"));
    btnCopiarEmail.style.display = "none";
  } else {
    console.warn('main.js: Botão copiar email não encontrado');
  }

  // Botão WhatsApp padrão
  const btnEnviarWhatsAppResultado = getCachedElement('btnEnviarWhatsAppResultado');
  if (btnEnviarWhatsAppResultado) {
    btnEnviarWhatsAppResultado.addEventListener("click", () => 
      handleSendToWhatsApp("standard")
    );
    btnEnviarWhatsAppResultado.style.display = "none";
  }

  // Botão WhatsApp email
  const btnEnviarWhatsAppEmail = getCachedElement('btnEnviarWhatsAppEmail');
  if (btnEnviarWhatsAppEmail) {
    btnEnviarWhatsAppEmail.addEventListener("click", () => 
      handleSendToWhatsApp("email")
    );
    btnEnviarWhatsAppEmail.style.display = "none";
  }

  // Botão limpar
  const btnLimpar = getCachedElement('btnLimpar');
  if (btnLimpar) {
    btnLimpar.addEventListener("click", handleClearFields);
  }

  // Relatório bruto com contador de caracteres
  const relatorioBruto = getCachedElement('relatorioBruto');
  if (relatorioBruto) {
    relatorioBruto.addEventListener("input", updateCharCount);
    updateCharCount(); // Contagem inicial
  }
}

// Função para configurar checkbox de email
function setupEmailCheckbox() {
  const checkbox = getCachedElement('formatarParaEmailCheckbox');
  const colunaEmail = getCachedElement('colunaRelatorioEmail');
  
  if (checkbox && colunaEmail) {
    checkbox.addEventListener("change", function() {
      const showEmailColumn = this.checked;
      colunaEmail.style.display = showEmailColumn ? "block" : "none";
      
      if (!showEmailColumn) {
        // Limpa e esconde elementos relacionados ao email
        const resultadoEmail = getCachedElement('resultadoEmail');
        const statusEmail = getCachedElement('statusProcessamentoEmail');
        const btnCopiarEmail = getCachedElement('btnCopiarEmail');
        const btnWhatsAppEmail = getCachedElement('btnEnviarWhatsAppEmail');
        
        if (resultadoEmail) resultadoEmail.value = "";
        if (statusEmail) displayStatus("", "info", "email");
        if (btnCopiarEmail) btnCopiarEmail.style.display = "none";
        if (btnWhatsAppEmail) btnWhatsAppEmail.style.display = "none";
      }
    });
  }
}

// Função para inicializar botões com HTML inicial
function initializeButtons() {
  initializeButton('btnProcessar', 'initialProcessButtonHTML');
  initializeButton('btnCopiar', 'initialCopyButtonHTML');
  initializeButton('btnCopiarEmail', 'initialCopyEmailButtonHTML');
  initializeButton('btnLimpar', 'initialClearButtonHTML');
}

// Função para verificar elementos essenciais
function validateEssentialElements() {
  const essentialElements = [
    'relatorioBruto',
    'btnProcessar', 
    'resultadoProcessamento'
  ];
  
  const missingElements = essentialElements.filter(key => !getCachedElement(key));
  
  if (missingElements.length > 0) {
    console.error(
      `index_page/main.js: Elementos DOM essenciais não encontrados: ${missingElements.join(', ')}`
    );
    
    // Log adicional para debug
    console.error('index_page/main.js: DOMElements disponíveis:', Object.keys(DOMElements));
    console.error('index_page/main.js: Selectors configurados:', CONFIG.selectors);
    
    const btnProcessar = getCachedElement('btnProcessar');
    if (btnProcessar) btnProcessar.disabled = true;
    
    return false;
  }
  
  return true;
}

// Função para configurar estado inicial da interface
function setupInitialUIState() {
  const colunaEmail = getCachedElement('colunaRelatorioEmail');
  if (colunaEmail) {
    colunaEmail.style.display = "none";
  }
}

document.addEventListener("DOMContentLoaded", function () {
  function init() {
    console.log("index_page/main.js: Iniciando inicialização...");
    
    try {
      // Inicializar elementos DOM primeiro
      console.log("index_page/main.js: Inicializando elementos DOM...");
      initializeDOMElements();
      
      // Validação de elementos essenciais
      if (!validateEssentialElements()) {
        console.error("index_page/main.js: Falha na validação de elementos essenciais.");
        return;
      }

      // Inicialização dos componentes
      initializeButtons();
      setupEventListeners();
      setupEmailCheckbox();
      setupInitialUIState();
      
      console.log("index_page/main.js: Inicialização concluída com sucesso.");
    } catch (error) {
      console.error("index_page/main.js: Erro durante a inicialização:", error);
    }
  }
  
  init();
});
