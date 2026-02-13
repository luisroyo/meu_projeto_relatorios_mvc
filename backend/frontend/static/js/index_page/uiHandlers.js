// app/static/js/index_page/uiHandlers.js
import { CONFIG, DOMElements } from './config.js';

export function updateCharCount() {
    console.log('updateCharCount: Iniciando...');
    console.log('updateCharCount: relatorioBruto:', DOMElements.relatorioBruto);
    console.log('updateCharCount: charCount:', DOMElements.charCount);
    
    if (DOMElements.relatorioBruto && DOMElements.charCount) {
        const currentLength = DOMElements.relatorioBruto.value.length;
        const maxChars = CONFIG.maxInputLengthServerDisplay;
        
        DOMElements.charCount.textContent = `Caracteres: ${currentLength} / ${maxChars}`;
        
        // Remove classes anteriores
        DOMElements.charCount.classList.remove('text-muted', 'text-warning', 'text-danger');
        
        // Aplica cor baseada no progresso
        if (currentLength > maxChars) {
            DOMElements.charCount.classList.add('text-danger');
        } else if (currentLength > maxChars * 0.8) {
            DOMElements.charCount.classList.add('text-warning');
        } else {
            DOMElements.charCount.classList.add('text-muted');
        }
        
        console.log('updateCharCount: Contador atualizado:', {
            currentLength,
            maxChars,
            textContent: DOMElements.charCount.textContent
        });
    } else {
        console.warn('updateCharCount: Elementos não encontrados');
    }
}

export function displayStatus(message, type = 'info', target = 'standard') {
    console.log('displayStatus:', { message, type, target });
    
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
        
        console.log('displayStatus: Status atualizado:', {
            element: statusElement,
            message,
            type,
            display: statusElement.style.display
        });
    } else {
        console.warn('displayStatus: Elemento de status não encontrado para target:', target);
    }
}

export function setProcessingUI(isProcessing) {
    if (DOMElements.btnProcessar) {
        if (isProcessing) {
            // Usa o novo sistema de loading do help-system
            if (window.helpSystem) {
                window.helpSystem.setButtonLoading(DOMElements.btnProcessar, true);
            } else {
                // Fallback para o sistema antigo
                DOMElements.btnProcessar.disabled = true;
                if (!DOMElements.btnProcessar.dataset.originalHTML) {
                    DOMElements.btnProcessar.dataset.originalHTML = DOMElements.btnProcessar.innerHTML;
                }
                DOMElements.btnProcessar.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${CONFIG.messages.processing || 'Processando...'}`;
            }
        } else {
            // Restaura estado normal do botão
            if (window.helpSystem) {
                window.helpSystem.setButtonLoading(DOMElements.btnProcessar, false);
            } else {
                // Fallback para o sistema antigo
                DOMElements.btnProcessar.disabled = false;
                DOMElements.btnProcessar.innerHTML = DOMElements.btnProcessar.dataset.originalHTML || 'Processar Relatório';
            }
        }
        
        // Log para debug
        console.log('setProcessingUI:', isProcessing ? 'Processando' : 'Concluído', {
            disabled: DOMElements.btnProcessar.disabled,
            innerHTML: DOMElements.btnProcessar.innerHTML.substring(0, 100),
            hasOriginalHTML: !!DOMElements.btnProcessar.dataset.originalHTML
        });
    }
}


export function showCopyFeedback(buttonElement) {
    console.log('showCopyFeedback: Iniciando...', buttonElement);
    
    if (!buttonElement) {
        console.warn('showCopyFeedback: buttonElement é null ou undefined');
        return;
    }
    
    // Exibe toast de sucesso
    if (window.feedbackComponents) {
        window.feedbackComponents.success(
            'Texto copiado para a área de transferência!',
            'Copiado com Sucesso',
            3000
        );
        console.log('showCopyFeedback: Toast de sucesso exibido');
    } else {
        console.log('showCopyFeedback: feedbackComponents não disponível');
    }
    
    // Atualiza visual do botão temporariamente
    if (!buttonElement.dataset.originalHTML) {
        buttonElement.dataset.originalHTML = buttonElement.innerHTML;
        console.log('showCopyFeedback: HTML original salvo:', buttonElement.dataset.originalHTML);
    }
    const originalHTML = buttonElement.dataset.originalHTML;
    buttonElement.innerHTML = CONFIG.messages.copied || '<i class="bi bi-check-lg me-1"></i>Copiado!';
    buttonElement.disabled = true;
    console.log('showCopyFeedback: Botão atualizado temporariamente');
    
    setTimeout(() => {
        buttonElement.innerHTML = originalHTML;
        buttonElement.disabled = false;
        console.log('showCopyFeedback: Botão restaurado');
    }, CONFIG.copySuccessMessageDuration);
}

export function tryFallbackCopy(text, buttonElement) {
    console.log('tryFallbackCopy: Iniciando fallback copy...');
    console.log('tryFallbackCopy: Texto para copiar:', text ? text.substring(0, 100) + '...' : 'N/A');
    console.log('tryFallbackCopy: Button element:', buttonElement);
    
    const textArea = document.createElement("textarea");
    textArea.value = text;
    // Estilos para manter o textarea fora da viewport e invisível
    textArea.style.position = "fixed"; textArea.style.top = "-9999px"; textArea.style.left = "-9999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        console.log('tryFallbackCopy: execCommand result:', successful);
        
        if (successful && buttonElement) {
            console.log('tryFallbackCopy: Copiado com sucesso, chamando showCopyFeedback');
            showCopyFeedback(buttonElement); // Reutiliza a função de feedback
        } else if(!successful) {
             throw new Error('document.execCommand("copy") não teve sucesso.');
        }
    } catch (err) {
        console.error('Falha ao copiar com fallback (execCommand): ', err);
        
        // Exibe toast de erro ao invés de alert
        if (window.feedbackComponents) {
            window.feedbackComponents.error(
                'Falha ao copiar automaticamente. Selecione o texto e use Ctrl+C para copiar manualmente.',
                'Erro ao Copiar',
                8000
            );
        } else {
            // Fallback para alert se o sistema de toasts não estiver disponível
            alert(CONFIG.messages.copyFailure || "Falha ao copiar. Por favor, copie manualmente.");
        }
    }
    
    document.body.removeChild(textArea);
    console.log('tryFallbackCopy: Fallback copy concluído');
}

export function resetOutputUI(showEmailColumn = false) {
    if (DOMElements.resultadoProcessamento) DOMElements.resultadoProcessamento.value = '';
    if (DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = '';

    displayStatus('', 'info', 'standard');
    if (DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email');

    if (DOMElements.btnCopiar) {
        DOMElements.btnCopiar.style.display = 'none';
        console.log('resetOutputUI: Botão copiar escondido');
    }
    if (DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
    if (DOMElements.btnEnviarWhatsAppResultado) DOMElements.btnEnviarWhatsAppResultado.style.display = 'none';
    if (DOMElements.btnEnviarWhatsAppEmail) DOMElements.btnEnviarWhatsAppEmail.style.display = 'none';

    if (DOMElements.colunaRelatorioEmail) {
        DOMElements.colunaRelatorioEmail.style.display = showEmailColumn ? 'block' : 'none';
    }
    
    console.log('resetOutputUI: Interface resetada');
}

export function updateReportUI(data) {
    console.log('updateReportUI: Iniciando com dados:', data);
    let standardReportSuccess = false;
    
    if (data.relatorio_processado) {
        console.log('updateReportUI: Relatório processado encontrado');
        
        if (DOMElements.resultadoProcessamento) {
            DOMElements.resultadoProcessamento.value = data.relatorio_processado;
            console.log('updateReportUI: Campo resultadoProcessamento atualizado');
        }
        
        // Mensagem diferenciada se foi usado fallback
        const successMessage = data.fallback_usado 
            ? 'Relatório processado localmente (API indisponível)!'
            : (CONFIG.messages.success || "Sucesso!");
        
        displayStatus(successMessage, 'success', 'standard');
        
        // Exibe toast de sucesso
        if (window.feedbackComponents) {
            const toastMessage = data.fallback_usado
                ? 'Relatório processado localmente com sucesso! (API temporariamente indisponível)'
                : 'Relatório processado e corrigido com sucesso!';
            
            window.feedbackComponents.success(
                toastMessage,
                'Processamento Concluído'
            );
        }
        
        if (data.relatorio_processado.trim()) {
            // Exibir botão de copiar
            if(DOMElements.btnCopiar) {
                DOMElements.btnCopiar.style.display = 'block';
                console.log('updateReportUI: Botão copiar exibido com sucesso');
                console.log('updateReportUI: Estado do botão copiar:', {
                    element: DOMElements.btnCopiar,
                    display: DOMElements.btnCopiar.style.display,
                    visible: DOMElements.btnCopiar.offsetParent !== null
                });
            } else {
                console.error('updateReportUI: Botão copiar NÃO encontrado em DOMElements');
                console.error('updateReportUI: DOMElements disponíveis:', Object.keys(DOMElements));
                console.error('updateReportUI: Seletor configurado:', CONFIG.selectors.btnCopiar);
                
                // Tentar encontrar o botão diretamente
                const btnCopiarDirect = document.querySelector(CONFIG.selectors.btnCopiar);
                if (btnCopiarDirect) {
                    console.log('updateReportUI: Botão copiar encontrado diretamente:', btnCopiarDirect);
                    btnCopiarDirect.style.display = 'block';
                } else {
                    console.error('updateReportUI: Botão copiar não encontrado nem diretamente');
                }
            }
            
            if(DOMElements.btnEnviarWhatsAppResultado) {
                DOMElements.btnEnviarWhatsAppResultado.style.display = 'block';
                console.log('updateReportUI: Botão WhatsApp exibido');
            }
        }
        standardReportSuccess = true;
    } else if (data.erro) {
        console.log('updateReportUI: Erro encontrado:', data.erro);
        displayStatus((CONFIG.messages.errorPrefix || "Erro: ") + data.erro, 'danger', 'standard');
        
        // Exibe toast de erro
        if (window.feedbackComponents) {
            window.feedbackComponents.error(
                data.erro,
                'Erro no Processamento'
            );
        }
        
         if(DOMElements.btnCopiar) DOMElements.btnCopiar.style.display = 'none';
         if(DOMElements.btnEnviarWhatsAppResultado) DOMElements.btnEnviarWhatsAppResultado.style.display = 'none';
    } else if (!data.relatorio_email && !data.erro_email && !(DOMElements.formatarParaEmailCheckbox && DOMElements.formatarParaEmailCheckbox.checked) ) {
        console.log('updateReportUI: Resposta inesperada');
        displayStatus(CONFIG.messages.unexpectedResponse || "Resposta inesperada.", 'warning', 'standard');
        
        // Exibe toast de aviso
        if (window.feedbackComponents) {
            window.feedbackComponents.warning(
                'A resposta do servidor não foi reconhecida. Tente novamente.',
                'Resposta Inesperada'
            );
        }
    }
    
    // Log para debug
    console.log('updateReportUI: Resumo final:', {
        hasRelatorioProcessado: !!data.relatorio_processado,
        hasError: !!data.erro,
        btnCopiar: DOMElements.btnCopiar,
        btnCopiarDisplay: DOMElements.btnCopiar ? DOMElements.btnCopiar.style.display : 'N/A',
        standardReportSuccess
    });
    
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