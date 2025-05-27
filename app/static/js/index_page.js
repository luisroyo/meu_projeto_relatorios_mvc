// app/static/js/index_page.js
document.addEventListener('DOMContentLoaded', function () {
    const CONFIG = {
        maxInputLengthFrontend: 10000,
        maxInputLengthServerDisplay: 12000,
        copySuccessMessageDuration: 2000,
        apiEndpoint: '/processar_relatorio', // Endpoint da main.py para relatórios IA
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
        // Avisos para elementos não encontrados ainda podem ser úteis durante o desenvolvimento
        if (!DOMElements[key]) {
            console.warn(`index_page.js: Elemento DOM para '${key}' (selector: '${CONFIG.selectors[key]}') não encontrado na página atual.`);
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
        if (target === 'email' && DOMElements.statusProcessamentoEmail) {
            statusElement = DOMElements.statusProcessamentoEmail;
        }

        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `${CONFIG.cssClasses.alert} ${CONFIG.cssClasses[`alert${type.charAt(0).toUpperCase() + type.slice(1)}`]} p-2 mt-2`; // Adicionado padding e margin
            statusElement.style.display = message ? 'block' : 'none';
        }
    }

    function setProcessingUI(isProcessing) {
        if (DOMElements.spinner) {
            DOMElements.spinner.style.display = isProcessing ? 'inline-block' : 'none';
        }
        if (DOMElements.btnProcessar) {
            DOMElements.btnProcessar.disabled = isProcessing;
            DOMElements.btnProcessar.innerHTML = isProcessing ?
                `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${CONFIG.messages.processing}` :
                'Processar Relatório';
        }
    }

    function showCopyFeedback(buttonElement) {
        const originalText = buttonElement.dataset.originalText;
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
        if (!DOMElements.relatorioBruto || !DOMElements.resultadoProcessamento) {
            console.error("Elementos de relatório bruto ou resultado não encontrados.");
            return;
        }

        const relatorioBrutoValue = DOMElements.relatorioBruto.value;
        const formatarParaEmailChecked = DOMElements.formatarParaEmailCheckbox ? DOMElements.formatarParaEmailCheckbox.checked : false;

        DOMElements.resultadoProcessamento.value = '';
        if (DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = ''; // Limpa campo de email
        displayStatus('', 'info', 'standard');
        if (DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email'); // Limpa status de email

        if (DOMElements.btnCopiar) DOMElements.btnCopiar.style.display = 'none';
        if (DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
        if (DOMElements.colunaRelatorioEmail) {
             DOMElements.colunaRelatorioEmail.style.display = formatarParaEmailChecked ? 'block' : 'none';
        }


        if (!relatorioBrutoValue.trim()) {
            displayStatus(CONFIG.messages.emptyReport, 'warning', 'standard');
            DOMElements.relatorioBruto.focus();
            return;
        }
        if (relatorioBrutoValue.length > CONFIG.maxInputLengthFrontend) {
            displayStatus(CONFIG.messages.reportTooLongFrontend(CONFIG.maxInputLengthFrontend, relatorioBrutoValue.length), 'danger', 'standard');
            DOMElements.relatorioBruto.focus();
            return;
        }

        setProcessingUI(true);
        displayStatus(CONFIG.messages.processing, 'info', 'standard');
        if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
            displayStatus(CONFIG.messages.processing, 'info', 'email');
        }

        try {
            const response = await fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    relatorio_bruto: relatorioBrutoValue,
                    format_for_email: formatarParaEmailChecked // Corrigido de format_for_email para formatarParaEmailChecked
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                const errorMessage = data.erro || `Erro do servidor: ${response.status}`;
                displayStatus(CONFIG.messages.errorPrefix + errorMessage, 'danger', 'standard');
                if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
                     displayStatus(CONFIG.messages.errorPrefix + errorMessage, 'danger', 'email');
                }
                // throw new Error(errorMessage); // Não precisa dar throw se já está mostrando o erro
                return; // Termina a execução aqui em caso de erro de resposta não ok
            }

            // Processar relatório padrão
            if (data.relatorio_processado) {
                DOMElements.resultadoProcessamento.value = data.relatorio_processado;
                displayStatus(CONFIG.messages.success, 'success', 'standard');
                if (data.relatorio_processado.trim() && DOMElements.btnCopiar) {
                    DOMElements.btnCopiar.style.display = 'inline-block';
                }
            } else if (data.erro) { // Se houve erro mas não é para email, ou se o padrão falhou
                displayStatus(CONFIG.messages.errorPrefix + data.erro, 'danger', 'standard');
            } else if (!data.relatorio_processado && !data.erro_email && !formatarParaEmailChecked) { // Nenhuma resposta útil
                displayStatus(CONFIG.messages.unexpectedResponse, 'warning', 'standard');
            }

            // Processar relatório de email se solicitado
            if (formatarParaEmailChecked) {
                if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'block';
                if (data.relatorio_email) {
                    if(DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = data.relatorio_email;
                    displayStatus('Relatório para e-mail gerado com sucesso!', 'success', 'email');
                    if (data.relatorio_email.trim() && DOMElements.btnCopiarEmail) {
                        DOMElements.btnCopiarEmail.style.display = 'inline-block';
                    }
                } else if (data.erro_email) {
                    displayStatus(CONFIG.messages.errorPrefix + data.erro_email, 'danger', 'email');
                } else { // Se não houve erro_email específico, mas relatorio_email não veio
                    displayStatus('Não foi possível gerar o relatório para e-mail ou não foi retornado.', 'warning', 'email');
                }
            }
             // Se o erro principal ocorreu e afetou ambos, ou se o erro padrão ocorreu e o email não era pra ser gerado
            if (data.erro && !data.relatorio_processado && (!formatarParaEmailChecked || (formatarParaEmailChecked && !data.relatorio_email && !data.erro_email))) {
                // Isso garante que se o erro principal afetou o fluxo e não há saídas, ele seja exibido
                 displayStatus(CONFIG.messages.errorPrefix + data.erro, 'danger', 'standard');
                 if(formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) displayStatus(CONFIG.messages.errorPrefix + data.erro, 'danger', 'email');
            }


        } catch (error) {
            console.error('Erro no handleProcessReport:', error);
            const RrMessage = error.message.includes("Failed to fetch") ? "Falha de conexão com o servidor." : error.message;
            displayStatus(CONFIG.messages.communicationFailure + RrMessage, 'danger', 'standard');
            if (formatarParaEmailChecked && DOMElements.colunaRelatorioEmail && DOMElements.statusProcessamentoEmail) {
                displayStatus(CONFIG.messages.communicationFailure + RrMessage, 'danger', 'email');
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
            if (!buttonElement.dataset.originalText) {
                 buttonElement.dataset.originalText = DOMElements.btnCopiarEmail.textContent || CONFIG.initialCopyEmailButtonText;
            }
        } else if (target === 'standard' && DOMElements.resultadoProcessamento && DOMElements.btnCopiar) { // Adicionado 'standard' para clareza
            textoParaCopiar = DOMElements.resultadoProcessamento.value;
            buttonElement = DOMElements.btnCopiar;
             if (!buttonElement.dataset.originalText) {
                 buttonElement.dataset.originalText = DOMElements.btnCopiar.textContent || CONFIG.initialCopyButtonText;
            }
        }

        if (!textoParaCopiar || !buttonElement) {
            console.warn("Texto ou botão de cópia não encontrado para o alvo:", target);
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
        // Verifica apenas os elementos essenciais para esta página (index.html)
        if (!DOMElements.relatorioBruto || !DOMElements.btnProcessar || !DOMElements.resultadoProcessamento || !DOMElements.statusProcessamento) {
            console.error("index_page.js: Um ou mais elementos essenciais para a página principal não foram encontrados no DOM.");
            if(DOMElements.btnProcessar) DOMElements.btnProcessar.disabled = true; // Desabilita se algo crucial falta
            return; // Interrompe a inicialização se elementos cruciais faltam
        }

        if (DOMElements.relatorioBruto) {
            DOMElements.relatorioBruto.addEventListener('input', updateCharCount);
            updateCharCount();
        }

        DOMElements.btnProcessar.addEventListener('click', handleProcessReport);

        if (DOMElements.btnCopiar) {
            DOMElements.btnCopiar.dataset.originalText = DOMElements.btnCopiar.textContent || CONFIG.initialCopyButtonText;
            DOMElements.btnCopiar.addEventListener('click', () => handleCopyResult('standard'));
            DOMElements.btnCopiar.style.display = 'none'; // Começa oculto
        }

        if (DOMElements.btnCopiarEmail) {
            DOMElements.btnCopiarEmail.dataset.originalText = DOMElements.btnCopiarEmail.textContent || CONFIG.initialCopyEmailButtonText;
            DOMElements.btnCopiarEmail.addEventListener('click', () => handleCopyResult('email'));
            DOMElements.btnCopiarEmail.style.display = 'none'; // Começa oculto
        }

        if (DOMElements.btnLimpar) {
            DOMElements.btnLimpar.addEventListener('click', handleClearFields);
        }

        if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'none'; // Garante que comece oculto

        if(DOMElements.formatarParaEmailCheckbox && DOMElements.colunaRelatorioEmail){
            DOMElements.formatarParaEmailCheckbox.addEventListener('change', function(){
                DOMElements.colunaRelatorioEmail.style.display = this.checked ? 'block' : 'none';
                if(!this.checked && DOMElements.resultadoEmail) { // Limpa se desmarcado
                    DOMElements.resultadoEmail.value = '';
                    if(DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email');
                    if(DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
                }
            });
        }
    }

    init();
});