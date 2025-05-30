// app/static/js/index_page.js
document.addEventListener('DOMContentLoaded', function () {
    const CONFIG = {
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
        cssClasses: { /* ... (como antes) ... */ },
        messages: { /* ... (como antes) ... */ },
        initialCopyButtonText: "Copiar Padrão",
        initialCopyEmailButtonText: "Copiar E-mail"
    };

    const DOMElements = {};
    for (const key in CONFIG.selectors) {
        DOMElements[key] = document.querySelector(CONFIG.selectors[key]);
        if (!DOMElements[key]) {
            console.warn(`index_page.js: Elemento DOM para '${key}' (seletor: '${CONFIG.selectors[key]}') NÃO ENCONTRADO.`);
        } else {
            // console.log(`index_page.js: Elemento DOM para '${key}' encontrado.`); // Descomente para depuração intensiva de seletores
        }
    }

    function updateCharCount() {
        if (DOMElements.relatorioBruto && DOMElements.charCount) {
            const currentLength = DOMElements.relatorioBruto.value.length;
            DOMElements.charCount.textContent = `Caracteres: ${currentLength} / ${CONFIG.maxInputLengthServerDisplay}`;
            DOMElements.charCount.classList.toggle(CONFIG.cssClasses.textDanger, currentLength > CONFIG.maxInputLengthFrontend);
        }
    }

    function displayStatus(message, type = 'info', target = 'standard') {
        console.log(`[UI DEBUG] displayStatus: message='${message}', type='${type}', target='${target}'`);
        let statusElement = DOMElements.statusProcessamento;
        if (target === 'email' && DOMElements.statusProcessamentoEmail) {
            statusElement = DOMElements.statusProcessamentoEmail;
        }

        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `${CONFIG.cssClasses.alert} ${CONFIG.cssClasses[`alert${type.charAt(0).toUpperCase() + type.slice(1)}`]} p-2 mt-2`;
            statusElement.style.display = message ? 'block' : 'none';
        } else {
            console.warn(`[UI DEBUG] displayStatus: Elemento de status para target '${target}' não encontrado.`);
        }
    }

    function setProcessingUI(isProcessing) {
        console.log(`[UI DEBUG] setProcessingUI: isProcessing=${isProcessing}`);
        if (DOMElements.spinner) {
            DOMElements.spinner.style.display = isProcessing ? 'inline-block' : 'none';
        } else {
            console.warn("[UI DEBUG] setProcessingUI: Elemento spinner não encontrado.");
        }
        if (DOMElements.btnProcessar) {
            DOMElements.btnProcessar.disabled = isProcessing;
            DOMElements.btnProcessar.innerHTML = isProcessing ?
                `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${CONFIG.messages.processing}` :
                'Processar Relatório';
        } else {
            console.warn("[UI DEBUG] setProcessingUI: Elemento btnProcessar não encontrado.");
        }
    }

    function showCopyFeedback(buttonElement) {
        if (!buttonElement) {
            console.warn("[UI DEBUG] showCopyFeedback: buttonElement é nulo.");
            return;
        }
        console.log("[UI DEBUG] showCopyFeedback: Mostrando feedback para o botão:", buttonElement.id);
        const originalText = buttonElement.dataset.originalText || "Copiar"; // Fallback se dataset não estiver setado
        buttonElement.innerHTML = CONFIG.messages.copied;
        buttonElement.disabled = true;
        setTimeout(() => {
            buttonElement.textContent = originalText;
            buttonElement.disabled = false;
            console.log("[UI DEBUG] showCopyFeedback: Feedback revertido para o botão:", buttonElement.id);
        }, CONFIG.copySuccessMessageDuration);
    }

    function tryFallbackCopy(text, buttonElement) {
        if (!buttonElement) {
            console.warn("[UI DEBUG] tryFallbackCopy: buttonElement é nulo.");
            // return; // Não retorna para ainda tentar copiar para a área de transferência e alertar
        }
        console.log("[UI DEBUG] tryFallbackCopy: Tentando fallback para o botão:", buttonElement ? buttonElement.id : "N/A");
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            const successful = document.execCommand('copy');
            if (successful && buttonElement) { // Só mostra feedback visual se o botão existir
                showCopyFeedback(buttonElement);
            } else if (!successful) {
                 throw new Error('document.execCommand("copy") não teve sucesso.');
            }
        } catch (err) {
            console.error('Falha ao copiar com fallback (execCommand): ', err);
            alert(CONFIG.messages.copyFailure);
        }
        document.body.removeChild(textArea);
    }

    async function handleProcessReport() {
        console.log("[PROCESS DEBUG] handleProcessReport: Iniciado.");
        if (!DOMElements.relatorioBruto || !DOMElements.resultadoProcessamento) {
            console.error("[PROCESS DEBUG] handleProcessReport: Elementos de relatório bruto ou resultado não encontrados.");
            return;
        }

        const relatorioBrutoValue = DOMElements.relatorioBruto.value;
        const formatarParaEmailChecked = DOMElements.formatarParaEmailCheckbox ? DOMElements.formatarParaEmailCheckbox.checked : false;

        console.log("[PROCESS DEBUG] Limpando UI antes do processamento.");
        DOMElements.resultadoProcessamento.value = '';
        if (DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = '';
        displayStatus('', 'info', 'standard');
        if (DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email');
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

        const csrfTokenElement = document.querySelector('meta[name="csrf-token"]');
        if (!csrfTokenElement) {
            console.error('[CSRF DEBUG] CSRF token meta tag não encontrada!');
            displayStatus('Erro de configuração: CSRF token não encontrado.', 'danger', 'standard');
            setProcessingUI(false);
            return;
        }
        const csrfToken = csrfTokenElement.getAttribute('content');
        console.log("[CSRF DEBUG] CSRF Token a ser enviado:", csrfToken);

        try {
            const payload = {
                relatorio_bruto: relatorioBrutoValue,
                format_for_email: formatarParaEmailChecked
            };
            console.log("[FETCH DEBUG] Enviando requisição para:", CONFIG.apiEndpoint, "com payload:", JSON.stringify(payload));

            const response = await fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(payload),
            });
            console.log("[FETCH DEBUG] Resposta Fetch recebida, status:", response.status);

            let data;
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            } else {
                const errorText = await response.text();
                console.error("[FETCH DEBUG] Resposta não JSON recebida:", errorText);
                let userMessage = CONFIG.messages.communicationFailure;
                if (!response.ok && errorText.trim().toLowerCase().startsWith("<!doctype html")) {
                    userMessage += "Possível erro de CSRF ou resposta HTML inesperada do servidor.";
                } else if (!response.ok) {
                    userMessage += `Erro ${response.status}: Resposta não JSON do servidor. Conteúdo: ${errorText.substring(0,100)}...`;
                } else {
                     userMessage += "Resposta inesperada do servidor (não JSON, mas status OK).";
                }
                displayStatus(userMessage, 'danger', 'standard');
                if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
                    displayStatus(userMessage, 'danger', 'email');
                }
                // setProcessingUI(false) será chamado no finally
                return; // Retorna aqui para não tentar processar 'data' que não é o esperado
            }

            console.log("[FETCH DEBUG] Dados JSON recebidos do servidor:", JSON.stringify(data, null, 2));

            if (!response.ok) {
                const errorMessage = data.message || data.erro || `Erro do servidor: ${response.status}`;
                console.error("[FETCH DEBUG] Erro de resposta não OK:", errorMessage);
                displayStatus(CONFIG.messages.errorPrefix + errorMessage, 'danger', 'standard');
                if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
                     displayStatus(CONFIG.messages.errorPrefix + (data.erro_email || errorMessage), 'danger', 'email');
                }
                // setProcessingUI(false) será chamado no finally
                return;
            }

            // Backend (main/routes.py) retorna: relatorio_processado, erro, relatorio_email, erro_email
            if (data.relatorio_processado) {
                console.log("[UI DEBUG] Processando data.relatorio_processado:", data.relatorio_processado.substring(0, 50) + "...");
                if (DOMElements.resultadoProcessamento) DOMElements.resultadoProcessamento.value = data.relatorio_processado;
                displayStatus(CONFIG.messages.success, 'success', 'standard');
                if (data.relatorio_processado.trim() && DOMElements.btnCopiar) {
                    console.log("[UI DEBUG] Mostrando btnCopiar");
                    DOMElements.btnCopiar.style.display = 'inline-block';
                } else {
                    console.log("[UI DEBUG] Não mostrando btnCopiar. Conteúdo vazio ou botão não encontrado?", !!DOMElements.btnCopiar, "Conteúdo:", data.relatorio_processado ? data.relatorio_processado.trim().substring(0,50) : 'N/A');
                }
            } else if (data.erro) {
                console.log("[UI DEBUG] Processando data.erro:", data.erro);
                displayStatus(CONFIG.messages.errorPrefix + data.erro, 'danger', 'standard');
            } else if (!data.relatorio_processado && !data.relatorio_email && !data.erro_email && !formatarParaEmailChecked) {
                console.log("[UI DEBUG] Nenhuma resposta útil (relatório padrão).");
                displayStatus(CONFIG.messages.unexpectedResponse, 'warning', 'standard');
            }

            if (formatarParaEmailChecked) {
                if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'block';
                if (data.relatorio_email) {
                    console.log("[UI DEBUG] Processando data.relatorio_email:", data.relatorio_email.substring(0,50) + "...");
                    if(DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = data.relatorio_email;
                    displayStatus('Relatório para e-mail gerado com sucesso!', 'success', 'email');
                    if (data.relatorio_email.trim() && DOMElements.btnCopiarEmail) {
                        console.log("[UI DEBUG] Mostrando btnCopiarEmail");
                        DOMElements.btnCopiarEmail.style.display = 'inline-block';
                    } else {
                        console.log("[UI DEBUG] Não mostrando btnCopiarEmail. Conteúdo vazio ou botão não encontrado?", !!DOMElements.btnCopiarEmail, "Conteúdo:", data.relatorio_email ? data.relatorio_email.trim().substring(0,50) : 'N/A');
                    }
                } else if (data.erro_email) {
                    console.log("[UI DEBUG] Processando data.erro_email:", data.erro_email);
                    displayStatus(CONFIG.messages.errorPrefix + data.erro_email, 'danger', 'email');
                } else if (!data.erro) {
                    console.log("[UI DEBUG] Nenhuma resposta útil (relatório email).");
                    displayStatus('Não foi possível gerar o relatório para e-mail ou não foi retornado.', 'warning', 'email');
                }
            }

        } catch (error) {
            console.error('[CATCH FINAL] Erro no handleProcessReport (index_page.js):', error);
            let userErrorMessage = CONFIG.messages.communicationFailure;
            if (error instanceof SyntaxError && error.message.toLowerCase().includes("unexpected token '<'")) {
                 userErrorMessage += "Resposta HTML inesperada do servidor (provável erro de CSRF ou servidor). Verifique o console.";
            } else if (error.message && error.message.includes("Failed to fetch")) {
                userErrorMessage += "Falha de conexão com o servidor.";
            } else if (error.message) {
                userErrorMessage += error.message;
            } else {
                userErrorMessage += "Erro desconhecido no processamento.";
            }
            displayStatus(userErrorMessage, 'danger', 'standard');
            if (formatarParaEmailChecked && DOMElements.colunaRelatorioEmail && DOMElements.statusProcessamentoEmail) {
                displayStatus(userErrorMessage, 'danger', 'email');
            }
        } finally {
            console.log("[FINALLY] Chamando setProcessingUI(false)");
            setProcessingUI(false);
        }
    }

    function handleCopyResult(target = 'standard') {
        console.log(`[COPY DEBUG] handleCopyResult: Target=${target}`);
        let textoParaCopiar = '';
        let buttonElement = null;
        let resultadoElement = null;

        if (target === 'email' && DOMElements.resultadoEmail && DOMElements.btnCopiarEmail) {
            resultadoElement = DOMElements.resultadoEmail;
            textoParaCopiar = DOMElements.resultadoEmail.value;
            buttonElement = DOMElements.btnCopiarEmail;
            if (!buttonElement.dataset.originalText) {
                 buttonElement.dataset.originalText = DOMElements.btnCopiarEmail.textContent || CONFIG.initialCopyEmailButtonText;
            }
        } else if (target === 'standard' && DOMElements.resultadoProcessamento && DOMElements.btnCopiar) {
            resultadoElement = DOMElements.resultadoProcessamento;
            textoParaCopiar = DOMElements.resultadoProcessamento.value;
            buttonElement = DOMElements.btnCopiar;
             if (!buttonElement.dataset.originalText) {
                 buttonElement.dataset.originalText = DOMElements.btnCopiar.textContent || CONFIG.initialCopyButtonText;
            }
        }

        console.log("[COPY DEBUG] Texto a ser copiado:", textoParaCopiar ? textoParaCopiar.substring(0,50) + "..." : "VAZIO");
        console.log("[COPY DEBUG] Elemento do botão:", buttonElement ? buttonElement.id : "NÃO ENCONTRADO");
        console.log("[COPY DEBUG] Elemento do resultado:", resultadoElement ? resultadoElement.id : "NÃO ENCONTRADO", "Valor:", resultadoElement ? (resultadoElement.value ? resultadoElement.value.substring(0,50) + "..." : "VAZIO") : "N/A");


        if (!textoParaCopiar || !textoParaCopiar.trim() || !buttonElement) {
            console.warn("[COPY DEBUG] handleCopyResult: Texto para copiar está vazio ou botão não encontrado. Target:", target);
            if (buttonElement) {
                 alert("Nada para copiar!");
            }
            return;
        }

        console.log("[COPY DEBUG] Tentando copiar com navigator.clipboard...");
        if (navigator.clipboard) {
            navigator.clipboard.writeText(textoParaCopiar)
                .then(() => {
                    console.log("[COPY DEBUG] Copiado com sucesso via navigator.clipboard!");
                    showCopyFeedback(buttonElement);
                })
                .catch(err => {
                    console.error('[COPY DEBUG] Falha ao copiar com navigator.clipboard: ', err);
                    console.log("[COPY DEBUG] Tentando fallback de cópia...");
                    tryFallbackCopy(textoParaCopiar, buttonElement);
                });
        } else {
            console.log("[COPY DEBUG] navigator.clipboard não disponível. Tentando fallback de cópia...");
            tryFallbackCopy(textoParaCopiar, buttonElement);
        }
    }
    function handleClearFields() { /* ... (código como fornecido anteriormente, adicione console.logs se precisar depurar) ... */ }

    function init() {
        if (!DOMElements.relatorioBruto || !DOMElements.btnProcessar || !DOMElements.resultadoProcessamento || !DOMElements.statusProcessamento) {
            console.error("index_page.js: Um ou mais elementos essenciais para a página principal não foram encontrados no DOM. A funcionalidade de processamento pode estar desabilitada.");
            if(DOMElements.btnProcessar) DOMElements.btnProcessar.disabled = true;
            return;
        }

        if (DOMElements.relatorioBruto) {
            DOMElements.relatorioBruto.addEventListener('input', updateCharCount);
            updateCharCount();
        }

        DOMElements.btnProcessar.addEventListener('click', handleProcessReport);

        if (DOMElements.btnCopiar) {
            DOMElements.btnCopiar.dataset.originalText = DOMElements.btnCopiar.textContent || CONFIG.initialCopyButtonText;
            DOMElements.btnCopiar.addEventListener('click', () => handleCopyResult('standard'));
            DOMElements.btnCopiar.style.display = 'none';
        }

        if (DOMElements.btnCopiarEmail) {
            DOMElements.btnCopiarEmail.dataset.originalText = DOMElements.btnCopiarEmail.textContent || CONFIG.initialCopyEmailButtonText;
            DOMElements.btnCopiarEmail.addEventListener('click', () => handleCopyResult('email'));
            DOMElements.btnCopiarEmail.style.display = 'none';
        }

        if (DOMElements.btnLimpar) {
            DOMElements.btnLimpar.addEventListener('click', handleClearFields);
        }

        if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'none';

        if(DOMElements.formatarParaEmailCheckbox && DOMElements.colunaRelatorioEmail){
            DOMElements.formatarParaEmailCheckbox.addEventListener('change', function(){
                DOMElements.colunaRelatorioEmail.style.display = this.checked ? 'block' : 'none';
                if(!this.checked && DOMElements.resultadoEmail) {
                    DOMElements.resultadoEmail.value = '';
                    if(DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email');
                    if(DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
                }
            });
        }
        console.log("index_page.js: Inicialização concluída e listeners adicionados.");
    }

    init();
});