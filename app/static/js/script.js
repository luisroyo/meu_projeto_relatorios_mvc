document.addEventListener('DOMContentLoaded', function () {
    // --- Configuração Centralizada ---
    const CONFIG = {
        maxInputLengthFrontend: 10000,
        maxInputLengthServerDisplay: 12000, // Usado apenas para exibição na mensagem
        copySuccessMessageDuration: 2000,
        apiEndpoint: '/processar_relatorio',
        selectors: {
            btnProcessar: '#processarRelatorio',
            relatorioBruto: '#relatorioBruto',
            resultadoProcessamento: '#resultadoProcessamento',
            statusProcessamento: '#statusProcessamento',
            spinner: '#processarSpinner',
            btnCopiar: '#copiarResultado',
            btnLimpar: '#limparCampos',
            charCount: '#charCount',
        },
        cssClasses: {
            textDanger: 'text-danger',
            alert: 'alert', // Classe base para status
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
            copied: '<i class="bi bi-check-lg"></i> Copiado!', // Exemplo com ícone Bootstrap
            copyFailure: 'Não foi possível copiar o texto. Por favor, copie manualmente.',
        },
        initialCopyButtonText: "Copiar Resultado" // Texto original do botão copiar
    };

    // --- Seleção de Elementos DOM ---
    const DOMElements = {};
    for (const key in CONFIG.selectors) {
        DOMElements[key] = document.querySelector(CONFIG.selectors[key]);
    }

    // --- Funções Utilitárias de UI ---
    function updateCharCount() {
        if (DOMElements.relatorioBruto && DOMElements.charCount) {
            const currentLength = DOMElements.relatorioBruto.value.length;
            DOMElements.charCount.textContent = `Caracteres: ${currentLength} / ${CONFIG.maxInputLengthServerDisplay}`;
            DOMElements.charCount.classList.toggle(CONFIG.cssClasses.textDanger, currentLength > CONFIG.maxInputLengthFrontend);
        }
    }

    function displayStatus(message, type = 'info') { // type: 'info', 'success', 'warning', 'danger'
        if (DOMElements.statusProcessamento) {
            DOMElements.statusProcessamento.textContent = message;
            DOMElements.statusProcessamento.className = `${CONFIG.cssClasses.alert} ${CONFIG.cssClasses[`alert${type.charAt(0).toUpperCase() + type.slice(1)}`]}`; // ex: alert-info
            DOMElements.statusProcessamento.style.display = message ? 'block' : 'none';
        }
    }

    function setProcessingUI(isProcessing) {
        if (DOMElements.spinner) {
            DOMElements.spinner.style.display = isProcessing ? 'inline-block' : 'none';
        }
        if (DOMElements.btnProcessar) {
            DOMElements.btnProcessar.disabled = isProcessing;
            // Poderia-se alterar o texto do botão aqui também se desejado
            // Ex: DOMElements.btnProcessar.querySelector('.button-text-label').textContent = isProcessing ? 'Processando...' : 'Processar Relatório';
        }
    }

    function showCopyFeedback(buttonElement) {
        const originalText = buttonElement.dataset.originalText || CONFIG.initialCopyButtonText; // Armazena o texto original se não existir
        buttonElement.dataset.originalText = originalText; // Garante que está lá para a próxima vez
        buttonElement.innerHTML = CONFIG.messages.copied;
        buttonElement.disabled = true;
        setTimeout(() => {
            buttonElement.textContent = originalText;
            buttonElement.disabled = false;
        }, CONFIG.copySuccessMessageDuration);
    }

    // --- Manipuladores de Evento ---
    async function handleProcessReport() {
        const relatorioBrutoValue = DOMElements.relatorioBruto.value;

        DOMElements.resultadoProcessamento.value = '';
        displayStatus('');
        if (DOMElements.btnCopiar) DOMElements.btnCopiar.style.display = 'none';

        if (!relatorioBrutoValue.trim()) {
            displayStatus(CONFIG.messages.emptyReport, 'warning');
            DOMElements.relatorioBruto.focus();
            return;
        }

        if (relatorioBrutoValue.length > CONFIG.maxInputLengthFrontend) {
            displayStatus(CONFIG.messages.reportTooLongFrontend(CONFIG.maxInputLengthFrontend, relatorioBrutoValue.length), 'danger');
            DOMElements.relatorioBruto.focus();
            return;
        }

        setProcessingUI(true);
        displayStatus(CONFIG.messages.processing, 'info');

        try {
            const response = await fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ relatorio_bruto: relatorioBrutoValue }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.erro || `Erro do servidor: ${response.status}`);
            }

            if (data.relatorio_processado) {
                DOMElements.resultadoProcessamento.value = data.relatorio_processado;
                displayStatus(CONFIG.messages.success, 'success');
                if (data.relatorio_processado.trim() && DOMElements.btnCopiar) {
                    DOMElements.btnCopiar.style.display = 'inline-block';
                }
            } else if (data.erro) {
                displayStatus(CONFIG.messages.errorPrefix + data.erro, 'danger');
            } else {
                displayStatus(CONFIG.messages.unexpectedResponse, 'warning');
            }
        } catch (error) {
            console.error('Erro no handleProcessReport:', error);
            displayStatus(CONFIG.messages.communicationFailure + error.message, 'danger');
        } finally {
            setProcessingUI(false);
        }
    }

    function handleCopyResult() {
        const textoParaCopiar = DOMElements.resultadoProcessamento.value;
        if (!textoParaCopiar || !DOMElements.btnCopiar) return;

        // Salva o texto original do botão se ainda não foi salvo
        if (!DOMElements.btnCopiar.dataset.originalText) {
            DOMElements.btnCopiar.dataset.originalText = DOMElements.btnCopiar.textContent;
        }

        if (navigator.clipboard) {
            navigator.clipboard.writeText(textoParaCopiar)
                .then(() => showCopyFeedback(DOMElements.btnCopiar))
                .catch(err => {
                    console.error('Falha ao copiar com navigator.clipboard: ', err);
                    tryFallbackCopy(textoParaCopiar, DOMElements.btnCopiar);
                });
        } else {
            tryFallbackCopy(textoParaCopiar, DOMElements.btnCopiar);
        }
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
            alert(CONFIG.messages.copyFailure); // Usar alert como último recurso
            // Não mudar o estado do botão se a cópia falhou completamente
        }
        document.body.removeChild(textArea);
    }

    function handleClearFields() {
        if (DOMElements.relatorioBruto) DOMElements.relatorioBruto.value = '';
        if (DOMElements.resultadoProcessamento) DOMElements.resultadoProcessamento.value = '';
        displayStatus('');
        if (DOMElements.btnCopiar) DOMElements.btnCopiar.style.display = 'none';
        updateCharCount();
        if (DOMElements.relatorioBruto) DOMElements.relatorioBruto.focus();
    }

    // --- Inicialização e Adição de Event Listeners ---
    function init() {
        // Verifica a existência dos elementos essenciais
        if (!DOMElements.relatorioBruto || !DOMElements.btnProcessar || !DOMElements.resultadoProcessamento || !DOMElements.statusProcessamento) {
            console.error("Um ou mais elementos essenciais não foram encontrados no DOM. A aplicação pode não funcionar corretamente.");
            // Poderia desabilitar a interface ou mostrar uma mensagem global de erro
            if(DOMElements.btnProcessar) DOMElements.btnProcessar.disabled = true;
            return;
        }
        
        DOMElements.relatorioBruto.addEventListener('input', updateCharCount);
        updateCharCount(); // Inicializa contagem

        DOMElements.btnProcessar.addEventListener('click', handleProcessReport);

        if (DOMElements.btnCopiar) {
            // Armazena o texto original do botão de cópia para restauração
            DOMElements.btnCopiar.dataset.originalText = DOMElements.btnCopiar.textContent || CONFIG.initialCopyButtonText;
            DOMElements.btnCopiar.addEventListener('click', handleCopyResult);
        } else {
            console.warn("Elemento 'copiarResultado' (botão copiar) não encontrado no DOM. Funcionalidade de cópia não estará disponível.");
        }

        if (DOMElements.btnLimpar) {
            DOMElements.btnLimpar.addEventListener('click', handleClearFields);
        } else {
            console.warn("Elemento 'limparCampos' (botão limpar) não encontrado no DOM.");
        }

        // Esconder o botão de copiar inicialmente, já que não há resultado
        if (DOMElements.btnCopiar) {
            DOMElements.btnCopiar.style.display = 'none';
        }
    }

    init(); // Inicia a aplicação
});