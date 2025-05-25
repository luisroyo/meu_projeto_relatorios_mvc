// app/static/js/script.js
document.addEventListener('DOMContentLoaded', function () {
    const CONFIG = {
        // ... (suas configurações CONFIG completas)
        maxInputLengthFrontend: 10000,
        maxInputLengthServerDisplay: 12000,
        copySuccessMessageDuration: 2000,
        apiEndpoint: '/processar_relatorio',
        selectors: {
            btnProcessar: '#processarRelatorio',
            relatorioBruto: '#relatorioBruto',
            resultadoProcessamento: '#resultadoProcessamento',
            resultadoEmail: '#resultadoEmail',
            colunaRelatorioEmail: '#colunaRelatorioEmail',
            statusProcessamento: '#statusProcessamento',
            statusProcessamentoEmail: '#statusProcessamentoEmail',
            spinner: '#processarSpinner',
            btnCopiar: '#copiarResultado',
            btnCopiarEmail: '#copiarResultadoEmail',
            btnLimpar: '#limparCampos',
            charCount: '#charCount',
            formatarParaEmailCheckbox: '#formatarParaEmail',
        },
        cssClasses: {
            textDanger: 'text-danger',
            alert: 'alert',
            alertInfo: 'alert-info',
            alertSuccess: 'alert-success',
            alertWarning: 'alert-warning',
            alertDanger: 'alert-danger',
        },
        messages: {
            processing: 'Processando...',
            success: 'Relatório processado com sucesso!',
            errorPrefix: 'Erro ao processar: ',
            unexpectedResponse: 'Resposta inesperada do servidor.',
            communicationFailure: 'Falha na comunicação ou processamento: ',
            emptyReport: "Por favor, insira o relatório bruto.",
            reportTooLongFrontend: (maxLength, currentLength) =>
                `O relatório é muito longo. Máximo de ${maxLength} caracteres permitidos no frontend. Você digitou ${currentLength}.`,
            copied: '<i class="bi bi-check-lg"></i> Copiado!',
            copyFailure: 'Não foi possível copiar o texto. Por favor, copie manualmente.',
        },
        initialCopyButtonText: "Copiar Padrão",
        initialCopyEmailButtonText: "Copiar E-mail"
    };

    const DOMElements = {};
    for (const key in CONFIG.selectors) {
        DOMElements[key] = document.querySelector(CONFIG.selectors[key]);
        if (!DOMElements[key] && (key === 'resultadoEmail' || key === 'colunaRelatorioEmail' || key === 'statusProcessamentoEmail' || key === 'btnCopiarEmail')) {
            console.warn(`Elemento DOM para '${key}' não encontrado. Funcionalidades relacionadas podem não operar corretamente.`);
        }
    }

    // --- Funções Utilitárias de UI ---
    function updateCharCount() {
        if (DOMElements.relatorioBruto && DOMElements.charCount) {
            const currentLength = DOMElements.relatorioBruto.value.length;
            DOMElements.charCount.textContent = `Caracteres: ${currentLength} / ${CONFIG.maxInputLengthServerDisplay}`;
            DOMElements.charCount.classList.toggle(CONFIG.cssClasses.textDanger, currentLength > CONFIG.maxInputLengthFrontend);
        }
    }

    function displayStatus(message, type = 'info', target = 'standard') {
        let statusElement = DOMElements.statusProcessamento;
        if (target === 'email') {
            statusElement = DOMElements.statusProcessamentoEmail;
        }

        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `${CONFIG.cssClasses.alert} ${CONFIG.cssClasses[`alert${type.charAt(0).toUpperCase() + type.slice(1)}`]}`;
            statusElement.style.display = message ? 'block' : 'none';
        }
    }

    function setProcessingUI(isProcessing) {
        if (DOMElements.spinner) {
            DOMElements.spinner.style.display = isProcessing ? 'inline-block' : 'none';
        }
        if (DOMElements.btnProcessar) {
            DOMElements.btnProcessar.disabled = isProcessing;
        }
    }

    function showCopyFeedback(buttonElement) {
        const originalText = buttonElement.dataset.originalText // Isso já pega o texto correto para o botão específico
        buttonElement.innerHTML = CONFIG.messages.copied;
        buttonElement.disabled = true;
        setTimeout(() => {
            buttonElement.textContent = originalText;
            buttonElement.disabled = false;
        }, CONFIG.copySuccessMessageDuration);
    }
    
    function tryFallbackCopy(text, buttonElement) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed"; 
        textArea.style.opacity = "0"; 
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                showCopyFeedback(buttonElement);
            } else {
                 throw new Error('document.execCommand("copy") não teve sucesso.');
            }
        } catch (err) {
            console.error('Falha ao copiar com fallback (execCommand): ', err);
            alert(CONFIG.messages.copyFailure);
        }
        document.body.removeChild(textArea);
    }

    // --- Manipuladores de Evento ---
    async function handleProcessReport() {
        const relatorioBrutoValue = DOMElements.relatorioBruto.value;
        const formatarParaEmailChecked = DOMElements.formatarParaEmailCheckbox ? DOMElements.formatarParaEmailCheckbox.checked : false;

        DOMElements.resultadoProcessamento.value = '';
        if (DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = '';
        displayStatus('', 'info', 'standard');
        if (DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email');
        
        if (DOMElements.btnCopiar) DOMElements.btnCopiar.style.display = 'none';
        if (DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
        if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'none';


        if (!relatorioBrutoValue.trim()) {
            displayStatus(CONFIG.messages.emptyReport, 'warning', 'standard');
            DOMElements.relatorioBruto.focus();
            return;
        }
        if (relatorioBrutoValue.length > CONFIG.maxInputLengthFrontend) {
            displayStatus(CONFIG.messages.reportTooLongFrontend(CONFIG.maxInputLengthFrontend, relatorioBrutoValue.length), 'danger');
            DOMElements.relatorioBruto.focus();
            return;
        }


        setProcessingUI(true);
        displayStatus(CONFIG.messages.processing, 'info', 'standard');
        if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
            displayStatus(CONFIG.messages.processing, 'info', 'email');
            if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'block';
        }


        try {
            const response = await fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    relatorio_bruto: relatorioBrutoValue,
                    format_for_email: formatarParaEmailChecked
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                const errorMessage = data.erro || `Erro do servidor: ${response.status}`;
                displayStatus(CONFIG.messages.errorPrefix + errorMessage, 'danger', 'standard');
                if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
                     displayStatus(CONFIG.messages.errorPrefix + errorMessage, 'danger', 'email');
                }
                throw new Error(errorMessage);
            }

            if (data.relatorio_processado) {
                DOMElements.resultadoProcessamento.value = data.relatorio_processado;
                displayStatus(CONFIG.messages.success, 'success', 'standard');
                if (data.relatorio_processado.trim() && DOMElements.btnCopiar) {
                    DOMElements.btnCopiar.style.display = 'inline-block';
                }
            } else if (data.erro && !formatarParaEmailChecked) { 
                displayStatus(CONFIG.messages.errorPrefix + data.erro, 'danger', 'standard');
            } else if (!data.relatorio_processado && !data.erro_email && !formatarParaEmailChecked) {
                displayStatus(CONFIG.messages.unexpectedResponse, 'warning', 'standard');
            }

            if (formatarParaEmailChecked) {
                if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'block'; 
                if (data.relatorio_email) {
                    DOMElements.resultadoEmail.value = data.relatorio_email;
                    displayStatus('Relatório para e-mail gerado com sucesso!', 'success', 'email');
                    if (data.relatorio_email.trim() && DOMElements.btnCopiarEmail) {
                        DOMElements.btnCopiarEmail.style.display = 'inline-block';
                    }
                } else if (data.erro_email) {
                    displayStatus(CONFIG.messages.errorPrefix + data.erro_email, 'danger', 'email');
                } else {
                    displayStatus('Não foi possível gerar o relatório para e-mail ou não foi retornado.', 'warning', 'email');
                }
            }
            if (data.erro && !data.relatorio_processado && (!formatarParaEmailChecked || !data.relatorio_email)) {
                displayStatus(CONFIG.messages.errorPrefix + data.erro, 'danger', 'standard');
                if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail){
                    displayStatus(CONFIG.messages.errorPrefix + data.erro, 'danger', 'email');
                }
            }


        } catch (error) {
            console.error('Erro no handleProcessReport:', error);
            displayStatus(CONFIG.messages.communicationFailure + error.message, 'danger', 'standard');
            if (formatarParaEmailChecked && DOMElements.colunaRelatorioEmail && DOMElements.statusProcessamentoEmail) {
                displayStatus(CONFIG.messages.communicationFailure + error.message, 'danger', 'email');
            }
        } finally {
            setProcessingUI(false);
        }
    }

    function handleCopyResult(target = 'standard') {
        let textoParaCopiar = '';
        let buttonElement = null;

        if (target === 'email' && DOMElements.resultadoEmail && DOMElements.btnCopiarEmail) {
            textoParaCopiar = DOMElements.resultadoEmail.value;
            buttonElement = DOMElements.btnCopiarEmail;
            if (!buttonElement.dataset.originalText) { // Garante que o texto original é pego
                 buttonElement.dataset.originalText = DOMElements.btnCopiarEmail.textContent || CONFIG.initialCopyEmailButtonText;
            }
        } else if (DOMElements.resultadoProcessamento && DOMElements.btnCopiar) {
            textoParaCopiar = DOMElements.resultadoProcessamento.value;
            buttonElement = DOMElements.btnCopiar;
             if (!buttonElement.dataset.originalText) { // Garante que o texto original é pego
                 buttonElement.dataset.originalText = DOMElements.btnCopiar.textContent || CONFIG.initialCopyButtonText;
            }
        }

        if (!textoParaCopiar || !buttonElement) return;
        
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
    
    function handleClearFields() {
        if (DOMElements.relatorioBruto) DOMElements.relatorioBruto.value = '';
        if (DOMElements.resultadoProcessamento) DOMElements.resultadoProcessamento.value = '';
        if (DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = '';
        
        displayStatus('', 'info', 'standard');
        if (DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email');
        
        if (DOMElements.btnCopiar) DOMElements.btnCopiar.style.display = 'none';
        if (DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
        if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'none';

        updateCharCount();
        if (DOMElements.relatorioBruto) DOMElements.relatorioBruto.focus();
        if (DOMElements.formatarParaEmailCheckbox) DOMElements.formatarParaEmailCheckbox.checked = false;
    }

    // --- Inicialização e Adição de Event Listeners ---
    function init() {
        if (!DOMElements.relatorioBruto || !DOMElements.btnProcessar || !DOMElements.resultadoProcessamento || !DOMElements.statusProcessamento) {
            console.error("Um ou mais elementos essenciais (padrão) não foram encontrados no DOM.");
            if(DOMElements.btnProcessar) DOMElements.btnProcessar.disabled = true;
        }
         if (!DOMElements.resultadoEmail || !DOMElements.colunaRelatorioEmail || !DOMElements.statusProcessamentoEmail || !DOMElements.btnCopiarEmail) {
            console.warn("Um ou mais elementos para o relatório de e-mail não foram encontrados. A funcionalidade de e-mail pode ser limitada.");
        }

        if (DOMElements.relatorioBruto) { // Verifica se relatorioBruto existe antes de adicionar listener
            DOMElements.relatorioBruto.addEventListener('input', updateCharCount);
            updateCharCount(); // Chama para inicializar a contagem
        }


        if (DOMElements.btnProcessar) DOMElements.btnProcessar.addEventListener('click', handleProcessReport);

        if (DOMElements.btnCopiar) {
            DOMElements.btnCopiar.dataset.originalText = DOMElements.btnCopiar.textContent || CONFIG.initialCopyButtonText;
            DOMElements.btnCopiar.addEventListener('click', () => handleCopyResult('standard'));
            DOMElements.btnCopiar.style.display = 'none';
        } else {
            console.warn("Elemento 'copiarResultado' (botão copiar padrão) não encontrado.");
        }

        if (DOMElements.btnCopiarEmail) {
            DOMElements.btnCopiarEmail.dataset.originalText = DOMElements.btnCopiarEmail.textContent || CONFIG.initialCopyEmailButtonText;
            DOMElements.btnCopiarEmail.addEventListener('click', () => handleCopyResult('email'));
            DOMElements.btnCopiarEmail.style.display = 'none';
        } else {
            console.warn("Elemento 'copiarResultadoEmail' (botão copiar e-mail) não encontrado.");
        }
        
        if (DOMElements.btnLimpar) {
            DOMElements.btnLimpar.addEventListener('click', handleClearFields);
        } else {
            console.warn("Elemento 'limparCampos' não encontrado.");
        }

        if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'none';
    }

    init(); // Chama init no final
});