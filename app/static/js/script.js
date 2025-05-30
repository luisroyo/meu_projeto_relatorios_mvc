// app/static/js/script.js
document.addEventListener('DOMContentLoaded', function () {
    const CONFIG = {
        maxInputLengthFrontend: 10000, //
        maxInputLengthServerDisplay: 12000, //
        copySuccessMessageDuration: 2000, //
        apiEndpoint: '/processar_relatorio', //
        selectors: { /* ... (selectors como no original) ... */ }, //
        cssClasses: { /* ... (cssClasses como no original) ... */ }, //
        messages: { /* ... (messages como no original) ... */ }, //
        initialCopyButtonText: "Copiar Padrão", //
        initialCopyEmailButtonText: "Copiar E-mail" //
    };

    const DOMElements = {};
    for (const key in CONFIG.selectors) { //
        DOMElements[key] = document.querySelector(CONFIG.selectors[key]);
        if (!DOMElements[key] && !(key === 'resultadoEmail' || key === 'colunaRelatorioEmail' || key === 'statusProcessamentoEmail' || key === 'btnCopiarEmail')) { //
            // console.warn(`script.js: Elemento DOM para '${key}' não encontrado.`);
        }
    }

    function updateCharCount() { /* ... (código como no original) ... */ } //
    function displayStatus(message, type = 'info', target = 'standard') { /* ... (código como no original) ... */ } //
    function setProcessingUI(isProcessing) { /* ... (código como no original) ... */ } //
    function showCopyFeedback(buttonElement) { /* ... (código como no original) ... */ } //
    function tryFallbackCopy(text, buttonElement) { /* ... (código como no original) ... */ } //

    async function handleProcessReport() {
        // Adiciona verificação para só executar se os elementos principais existirem na página
        if (!DOMElements.relatorioBruto || !DOMElements.btnProcessar || !DOMElements.resultadoProcessamento || !DOMElements.statusProcessamento) {
            // console.log("script.js: Elementos para processar relatório não presentes. Ignorando handleProcessReport de script.js.");
            return;
        }

        const relatorioBrutoValue = DOMElements.relatorioBruto.value; //
        const formatarParaEmailChecked = DOMElements.formatarParaEmailCheckbox ? DOMElements.formatarParaEmailCheckbox.checked : false; //

        // Limpar campos e status (como em index_page.js)
        if(DOMElements.resultadoProcessamento) DOMElements.resultadoProcessamento.value = ''; //
        if (DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = ''; //
        if(DOMElements.statusProcessamento) displayStatus('', 'info', 'standard'); //
        if (DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email'); //
        if (DOMElements.btnCopiar) DOMElements.btnCopiar.style.display = 'none'; //
        if (DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none'; //
        if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = formatarParaEmailChecked ? 'block' : 'none'; //


        if (!relatorioBrutoValue.trim()) { /* ... (validação) ... */ return; } //
        if (relatorioBrutoValue.length > CONFIG.maxInputLengthFrontend) { /* ... (validação) ... */ return; } //


        if(DOMElements.btnProcessar) setProcessingUI(true); //
        if(DOMElements.statusProcessamento) displayStatus(CONFIG.messages.processing, 'info', 'standard'); //
        if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
            displayStatus(CONFIG.messages.processing, 'info', 'email'); //
        }

        const csrfTokenElement = document.querySelector('meta[name="csrf-token"]');
        if (!csrfTokenElement) {
            console.error('script.js: CSRF token meta tag não encontrada!');
            if(DOMElements.statusProcessamento) displayStatus('Erro de configuração: CSRF token não encontrado (script.js).', 'danger', 'standard'); //
            if(DOMElements.btnProcessar) setProcessingUI(false); //
            return;
        }
        const csrfToken = csrfTokenElement.getAttribute('content');
        console.log("CSRF Token a ser enviado (script.js):", csrfToken);

        try {
            const response = await fetch(CONFIG.apiEndpoint, { //
                method: 'POST', //
                headers: {
                    'Content-Type': 'application/json', //
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ //
                    // *** CORREÇÃO APLICADA AQUI ***
                    relatorio_bruto: relatorioBrutoValue,    // Alinhado com o backend
                    format_for_email: formatarParaEmailChecked // Alinhado com o backend
                }),
            });

            let data;
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json(); //
            } else {
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error("Resposta não JSON recebida (script.js):", errorText);
                    let userMessage = CONFIG.messages.communicationFailure; //
                    if (errorText.trim().toLowerCase().startsWith("<!doctype html")) {
                        userMessage += "Possível erro de CSRF ou resposta HTML inesperada do servidor (script.js).";
                    } else {
                        userMessage += `Erro ${response.status}: Resposta não JSON do servidor (script.js).`;
                    }
                    if(DOMElements.statusProcessamento) displayStatus(userMessage, 'danger', 'standard'); //
                    if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
                        displayStatus(userMessage, 'danger', 'email');
                    }
                    if(DOMElements.btnProcessar) setProcessingUI(false); //
                    return;
                }
                data = { erro: CONFIG.messages.unexpectedResponse }; //
            }

            console.log("Dados recebidos do servidor (script.js):", JSON.stringify(data, null, 2));

            if (!response.ok) {
                const errorMessage = data.message || data.erro || `Erro do servidor: ${response.status}`; //
                if(DOMElements.statusProcessamento) displayStatus(CONFIG.messages.errorPrefix + errorMessage, 'danger', 'standard'); //
                if (formatarParaEmailChecked && DOMElements.statusProcessamentoEmail) {
                     if(DOMElements.statusProcessamentoEmail) displayStatus(CONFIG.messages.errorPrefix + (data.erro_email || errorMessage), 'danger', 'email');
                }
                if(DOMElements.btnProcessar) setProcessingUI(false); //
                return;
            }

            // Chaves da resposta do backend: relatorio_processado, erro, relatorio_email, erro_email
            if (data.relatorio_processado) {
                if(DOMElements.resultadoProcessamento) DOMElements.resultadoProcessamento.value = data.relatorio_processado; //
                if(DOMElements.statusProcessamento) displayStatus(CONFIG.messages.success, 'success', 'standard'); //
                if (data.relatorio_processado.trim() && DOMElements.btnCopiar) {
                    DOMElements.btnCopiar.style.display = 'inline-block'; //
                }
            } else if (data.erro) {
                if(DOMElements.statusProcessamento) displayStatus(CONFIG.messages.errorPrefix + data.erro, 'danger', 'standard'); //
            } else if (!data.relatorio_processado && !data.relatorio_email && !data.erro_email && !formatarParaEmailChecked) {
                if(DOMElements.statusProcessamento) displayStatus(CONFIG.messages.unexpectedResponse, 'warning', 'standard'); //
            }

            if (formatarParaEmailChecked) {
                if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'block'; //
                if (data.relatorio_email) {
                    if (DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = data.relatorio_email; //
                    if (DOMElements.statusProcessamentoEmail) displayStatus('Relatório para e-mail gerado com sucesso!', 'success', 'email'); //
                    if (data.relatorio_email.trim() && DOMElements.btnCopiarEmail) {
                        DOMElements.btnCopiarEmail.style.display = 'inline-block'; //
                    }
                } else if (data.erro_email) {
                    if (DOMElements.statusProcessamentoEmail) displayStatus(CONFIG.messages.errorPrefix + data.erro_email, 'danger', 'email'); //
                } else if (!data.erro) {
                     if (DOMElements.statusProcessamentoEmail) displayStatus('Não foi possível gerar o relatório para e-mail ou não foi retornado.', 'warning', 'email'); //
                }
            }

        } catch (error) {
            console.error('Erro no handleProcessReport (script.js):', error); //
            let userErrorMessage = CONFIG.messages.communicationFailure; //
             if (error instanceof SyntaxError && error.message.toLowerCase().includes("unexpected token '<'")) {
                 userErrorMessage += "Resposta HTML inesperada (script.js - CSRF?).";
            } else if (error.message.includes("Failed to fetch")) {
                userErrorMessage += "Falha de conexão (script.js).";
            } else {
                userErrorMessage += error.message;
            }
            if(DOMElements.statusProcessamento) displayStatus(userErrorMessage, 'danger', 'standard'); //
            if (formatarParaEmailChecked && DOMElements.colunaRelatorioEmail && DOMElements.statusProcessamentoEmail) {
                displayStatus(userErrorMessage, 'danger', 'email'); //
            }
        } finally {
            if(DOMElements.btnProcessar) setProcessingUI(false); //
        }
    }

    function handleCopyResult(target = 'standard') { /* ... (código como no original) ... */ } //
    function handleClearFields() { /* ... (código como no original) ... */ } //

    function init() {
        // Adiciona listeners apenas se os elementos relevantes existirem na página ATUAL
        if (DOMElements.relatorioBruto) { //
            DOMElements.relatorioBruto.addEventListener('input', updateCharCount); //
            updateCharCount(); //
        }
        if (DOMElements.btnProcessar) {
             DOMElements.btnProcessar.addEventListener('click', handleProcessReport); //
        }
        if (DOMElements.btnCopiar) { /* ... (como no original, verificando DOMElements) ... */ } //
        if (DOMElements.btnCopiarEmail) { /* ... (como no original, verificando DOMElements) ... */ } //
        if (DOMElements.btnLimpar) { /* ... (como no original, verificando DOMElements) ... */ } //
        if (DOMElements.colunaRelatorioEmail && DOMElements.formatarParaEmailCheckbox) { /* ... (como no original) ... */ } //
    }
    init(); //
});