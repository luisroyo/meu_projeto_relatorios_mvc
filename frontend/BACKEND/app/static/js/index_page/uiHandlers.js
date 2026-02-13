// app/static/js/index_page/uiHandlers.js
import { CONFIG, DOMElements } from './config.js';

export function updateCharCount() {
    if (DOMElements.relatorioBruto && DOMElements.charCount) {
        const currentLength = DOMElements.relatorioBruto.value.length;
        DOMElements.charCount.textContent = `Caracteres: ${currentLength} / ${CONFIG.maxInputLengthServerDisplay}`;
        DOMElements.charCount.classList.toggle(CONFIG.cssClasses.textDanger, currentLength > CONFIG.maxInputLengthFrontend);
    }
}

export function displayStatus(message, type = 'info', target = 'standard') {
    let statusElement = DOMElements.statusProcessamento;
    if (target === 'email' && DOMElements.statusProcessamentoEmail) {
        statusElement = DOMElements.statusProcessamentoEmail;
    }
    if (statusElement) {
        statusElement.textContent = message;
        const alertBaseClass = CONFIG.cssClasses.alert;
        // Corrigido para usar o nome da classe diretamente do CONFIG.cssClasses
        const alertTypeClass = CONFIG.cssClasses[`alert${type.charAt(0).toUpperCase() + type.slice(1)}`] || `alert-${type}`;
        statusElement.className = `${alertBaseClass} ${alertTypeClass} p-2 mt-2`; // Adicionado padding e margin
        statusElement.style.display = message ? 'block' : 'none';
    }
}

export function setProcessingUI(isProcessing) {
    if (DOMElements.btnProcessar) {
        DOMElements.btnProcessar.disabled = isProcessing;
        if (isProcessing) {
            if (!DOMElements.btnProcessar.dataset.originalHTML) {
                DOMElements.btnProcessar.dataset.originalHTML = DOMElements.btnProcessar.innerHTML;
            }
            DOMElements.btnProcessar.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${CONFIG.messages.processing || 'Processando...'}`;
        } else {
            // Restaura o HTML original do botão que foi salvo no dataset
            DOMElements.btnProcessar.innerHTML = DOMElements.btnProcessar.dataset.originalHTML || 'Processar Relatório';
        }
    }
}


export function showCopyFeedback(buttonElement) {
    if (!buttonElement) return;
    if (!buttonElement.dataset.originalHTML) { // Garante que temos um original
        buttonElement.dataset.originalHTML = buttonElement.innerHTML;
    }
    const originalHTML = buttonElement.dataset.originalHTML;
    buttonElement.innerHTML = CONFIG.messages.copied || '<i class="bi bi-check-lg me-1"></i>Copiado!';
    buttonElement.disabled = true;
    setTimeout(() => {
        buttonElement.innerHTML = originalHTML;
        buttonElement.disabled = false;
    }, CONFIG.copySuccessMessageDuration);
}

export function tryFallbackCopy(text, buttonElement) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    // Estilos para manter o textarea fora da viewport e invisível
    textArea.style.position = "fixed"; textArea.style.top = "-9999px"; textArea.style.left = "-9999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        const successful = document.execCommand('copy');
        if (successful && buttonElement) {
            showCopyFeedback(buttonElement); // Reutiliza a função de feedback
        } else if(!successful) {
             throw new Error('document.execCommand("copy") não teve sucesso.');
        }
    } catch (err) {
        console.error('Falha ao copiar com fallback (execCommand): ', err);
        alert(CONFIG.messages.copyFailure || "Falha ao copiar. Por favor, copie manualmente.");
    }
    document.body.removeChild(textArea);
}

export function resetOutputUI(showEmailColumn = false) {
    if (DOMElements.resultadoProcessamento) DOMElements.resultadoProcessamento.value = '';
    if (DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = '';

    displayStatus('', 'info', 'standard');
    if (DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email');

    if (DOMElements.btnCopiar) DOMElements.btnCopiar.style.display = 'none';
    if (DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
    if (DOMElements.btnEnviarWhatsAppResultado) DOMElements.btnEnviarWhatsAppResultado.style.display = 'none';
    if (DOMElements.btnEnviarWhatsAppEmail) DOMElements.btnEnviarWhatsAppEmail.style.display = 'none';

    if (DOMElements.colunaRelatorioEmail) {
        DOMElements.colunaRelatorioEmail.style.display = showEmailColumn ? 'block' : 'none';
    }
}

export function updateReportUI(data) {
    let standardReportSuccess = false;
    if (data.relatorio_processado) {
        if (DOMElements.resultadoProcessamento) DOMElements.resultadoProcessamento.value = data.relatorio_processado;
        displayStatus(CONFIG.messages.success || "Sucesso!", 'success', 'standard');
        if (data.relatorio_processado.trim()) {
            if(DOMElements.btnCopiar) DOMElements.btnCopiar.style.display = 'block'; // Usar 'block' ou 'inline-block' conforme o layout
            if(DOMElements.btnEnviarWhatsAppResultado) DOMElements.btnEnviarWhatsAppResultado.style.display = 'block';
        }
        standardReportSuccess = true;
    } else if (data.erro) {
        displayStatus((CONFIG.messages.errorPrefix || "Erro: ") + data.erro, 'danger', 'standard');
         if(DOMElements.btnCopiar) DOMElements.btnCopiar.style.display = 'none';
         if(DOMElements.btnEnviarWhatsAppResultado) DOMElements.btnEnviarWhatsAppResultado.style.display = 'none';
    } else if (!data.relatorio_email && !data.erro_email && !(DOMElements.formatarParaEmailCheckbox && DOMElements.formatarParaEmailCheckbox.checked) ) {
        // Este caso pode ser complexo, talvez seja melhor simplificar o que é mostrado ao usuário
        // ou garantir que 'erro' seja populado se 'relatorio_processado' não for.
        displayStatus(CONFIG.messages.unexpectedResponse || "Resposta inesperada.", 'warning', 'standard');
    }
    return standardReportSuccess;
}

export function updateEmailReportUI(data) {
    if (data.relatorio_email) {
        if(DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = data.relatorio_email;
        displayStatus('Relatório para e-mail gerado!', 'success', 'email');
        if (data.relatorio_email.trim()) {
            if(DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'block';
            if(DOMElements.btnEnviarWhatsAppEmail) DOMElements.btnEnviarWhatsAppEmail.style.display = 'block';
        }
    } else if (data.erro_email) {
        displayStatus((CONFIG.messages.errorPrefix || "Erro: ") + data.erro_email, 'danger', 'email');
        if(DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
        if(DOMElements.btnEnviarWhatsAppEmail) DOMElements.btnEnviarWhatsAppEmail.style.display = 'none';
    } else if (!data.erro && (DOMElements.formatarParaEmailCheckbox && DOMElements.formatarParaEmailCheckbox.checked)) { 
        // Só mostra warning se foi solicitado e não houve erro mais geral e nem sucesso
        displayStatus('Relatório para e-mail não gerado ou vazio.', 'warning', 'email');
    }
}