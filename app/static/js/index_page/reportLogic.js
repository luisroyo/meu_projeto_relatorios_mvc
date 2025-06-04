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
        updateReportUI(data);
        if (formatarParaEmailChecked) {
            updateEmailReportUI(data);
        }
    } catch (error) {
        console.error('Erro em handleProcessReport:', error);
        let userErrorMessage = error.message || CONFIG.messages.communicationFailure;

        if (error.isApiError && error.data) { // Erro específico da API com dados JSON
            // A mensagem principal já vem do apiService
        } else if (error.isNetworkOrParseError) {
            // Mensagem já formatada pelo apiService
        } else if (error.message.includes("CSRF token")) {
             // Já tratado pelo displayStatus no apiService, mas podemos reforçar
             userErrorMessage = error.message;
        } else if (error instanceof SyntaxError && error.message.toLowerCase().includes("unexpected token '<'")) {
            userErrorMessage = (CONFIG.messages.communicationFailure || "") + " Resposta HTML inesperada (CSRF?).";
        } else if (error.message && error.message.includes("Failed to fetch")) {
            userErrorMessage = (CONFIG.messages.communicationFailure || "") + " Falha de conexão.";
        }

        displayStatus(userErrorMessage, 'danger', 'standard');
        if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
            displayStatus(userErrorMessage, 'danger', 'email'); // Pode mostrar o mesmo erro
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
    resetOutputUI(false); // Passa false para showEmailColumn
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

    if (!buttonElement) return; // Se o botão não existe, não faz nada

    // Garante que originalHTML seja definido antes de copiar
    if (!buttonElement.dataset.originalHTML) {
        buttonElement.dataset.originalHTML = buttonElement.innerHTML;
    }
    
    if (!textoParaCopiar || !textoParaCopiar.trim()) {
        alert("Nada para copiar!");
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