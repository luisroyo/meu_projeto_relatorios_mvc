// app/static/js/index_page/reportLogic.js
import { CONFIG, DOMElements } from './config.js';
import {
    updateCharCount, displayStatus, setProcessingUI, showCopyFeedback,
    tryFallbackCopy, resetOutputUI, updateReportUI, updateEmailReportUI
} from './uiHandlers.js';
import { callProcessReportAPI } from './apiService.js';

export async function handleProcessReport() {
    if (!DOMElements.relatorioBruto || !DOMElements.resultadoProcessamento) return;

    if (DOMElements.btnProcessar && !DOMElements.btnProcessar.dataset.originalHTML) {
        DOMElements.btnProcessar.dataset.originalHTML = DOMElements.btnProcessar.innerHTML;
    }

    const relatorioBrutoValue = DOMElements.relatorioBruto.value;
    const formatarParaEmailChecked = DOMElements.formatarParaEmailCheckbox ? DOMElements.formatarParaEmailCheckbox.checked : false;

    resetOutputUI(formatarParaEmailChecked);

    if (!relatorioBrutoValue.trim()) {
        displayStatus(CONFIG.messages.emptyReport, 'warning', 'standard');
        if (DOMElements.relatorioBruto) DOMElements.relatorioBruto.focus();
        return;
    }
    if (relatorioBrutoValue.length > CONFIG.maxInputLengthFrontend) {
        displayStatus(CONFIG.messages.reportTooLongFrontend(CONFIG.maxInputLengthFrontend, relatorioBrutoValue.length), 'danger', 'standard');
        if (DOMElements.relatorioBruto) DOMElements.relatorioBruto.focus();
        return;
    }

    setProcessingUI(true);
    displayStatus(CONFIG.messages.processing, 'info', 'standard');
    if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
        displayStatus(CONFIG.messages.processing, 'info', 'email');
    }

    try {
        const data = await callProcessReportAPI(relatorioBrutoValue, formatarParaEmailChecked);
        const standardReportSuccess = updateReportUI(data); // Captura se o relatório padrão foi ok

        if (formatarParaEmailChecked) {
             // Garante que a coluna de email seja exibida se a checkbox estiver marcada, 
             // mesmo que o processamento de email em si ainda não tenha uma mensagem de status.
            if(DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'block';
            updateEmailReportUI(data);
        } else {
            // Garante que a coluna de email esteja oculta se a checkbox não estiver marcada.
            if(DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'none';
        }

    } catch (error) {
        console.error('Erro em handleProcessReport:', error);
        let userErrorMessage = error.message || CONFIG.messages.communicationFailure;

        // Tratamento de erros já existente...
        displayStatus(userErrorMessage, 'danger', 'standard');
        if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
            if(DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'block'; // Mostra a coluna para exibir o erro do email
            displayStatus(userErrorMessage, 'danger', 'email');
        }
    } finally {
        setProcessingUI(false);
    }
}

export function handleClearFields() {
    if (DOMElements.relatorioBruto) {
        DOMElements.relatorioBruto.value = '';
        updateCharCount();
        DOMElements.relatorioBruto.focus();
    }
    if (DOMElements.formatarParaEmailCheckbox) {
        DOMElements.formatarParaEmailCheckbox.checked = false;
    }
    resetOutputUI(false);
}

export function handleCopyResult(target = 'standard') {
    let textoParaCopiar = '';
    let buttonElement = null;

    if (target === 'email' && DOMElements.resultadoEmail && DOMElements.btnCopiarEmail) {
        textoParaCopiar = DOMElements.resultadoEmail.value;
        buttonElement = DOMElements.btnCopiarEmail;
    } else if (target === 'standard' && DOMElements.resultadoProcessamento && DOMElements.btnCopiar) {
        textoParaCopiar = DOMElements.resultadoProcessamento.value;
        buttonElement = DOMElements.btnCopiar;
    }

    if (!buttonElement) return; 
    
    if (!buttonElement.dataset.originalHTML) {
        buttonElement.dataset.originalHTML = buttonElement.innerHTML;
    }
    
    if (!textoParaCopiar || !textoParaCopiar.trim()) {
        alert("Nada para copiar!"); // Ou usar displayStatus
        return;
    }

    if (navigator.clipboard) {
        navigator.clipboard.writeText(textoParaCopiar)
            .then(() => showCopyFeedback(buttonElement))
            .catch(err => {
                console.error('Falha ao copiar com navigator.clipboard: ', err);
                tryFallbackCopy(textoParaCopiar, buttonElement);
            });
    } else {
        tryFallbackCopy(textoParaCopiar, buttonElement);
    }
}

// NOVA FUNÇÃO
export function handleSendToWhatsApp(target = 'standard') {
    let textoParaEnviar = '';
    // Não precisamos do buttonElement para feedback aqui, pois abre nova aba

    if (target === 'email' && DOMElements.resultadoEmail) {
        textoParaEnviar = DOMElements.resultadoEmail.value;
    } else if (target === 'standard' && DOMElements.resultadoProcessamento) {
        textoParaEnviar = DOMElements.resultadoProcessamento.value;
    }
    
    if (!textoParaEnviar || !textoParaEnviar.trim()) {
        alert("Nada para enviar via WhatsApp!"); // Ou usar displayStatus
        return;
    }

    const textoCodificado = encodeURIComponent(textoParaEnviar.trim());
    const whatsappUrl = `https://wa.me/?text=${textoCodificado}`;
    
    window.open(whatsappUrl, '_blank');
}