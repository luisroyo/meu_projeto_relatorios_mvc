// app/static/js/relatorio_ronda_page.js
document.addEventListener('DOMContentLoaded', function() {
    const selectCondominio = document.getElementById('nome_condominio_select');
    const outroCondominioDiv = document.getElementById('outro_condominio_div');
    const outroCondominioInput = document.getElementById('nome_condominio_outro'); // Assumindo que seu form.nome_condominio_outro gera este ID
    const logBrutoTextarea = document.getElementById('log_bruto_rondas'); // Assumindo que seu form.log_bruto_rondas gera este ID
    
    const btnCopiarRonda = document.getElementById('copiarRelatorioRonda');
    // Se você não tem um botão Limpar com este ID no seu HTML, pode remover esta linha e o bloco if(btnLimparFormRonda)
    const btnLimparFormRonda = document.getElementById('limparFormRonda'); 
    const btnEnviarWhatsAppRonda = document.getElementById('enviarWhatsAppRonda');

    function toggleOutroCondominio() {
        if (selectCondominio && outroCondominioDiv) {
            if (selectCondominio.value === 'Outro') {
                outroCondominioDiv.style.display = 'block';
            } else {
                outroCondominioDiv.style.display = 'none';
                if(outroCondominioInput) outroCondominioInput.value = '';
            }
        }
    }

    if (selectCondominio) {
        selectCondominio.addEventListener('change', toggleOutroCondominio);
        toggleOutroCondominio(); // Chama para definir o estado inicial
    }

    // Se você não tem um botão Limpar com id="limparFormRonda", remova este bloco
    if (btnLimparFormRonda) {
        btnLimparFormRonda.addEventListener('click', function() {
            if(logBrutoTextarea) logBrutoTextarea.value = '';

            const form = document.querySelector('form[action="{{ url_for(\'ronda.registrar_ronda\') }}"]'); // Seletor mais específico para o formulário
            if (form) {
                // IDs dos campos do formulário gerados pelo WTForms (verifique o HTML renderizado)
                const dataPlantaoField = form.querySelector('#data_plantao'); // Ajuste o ID se necessário
                const escalaPlantaoField = form.querySelector('#escala_plantao'); // Ajuste o ID se necessário

                if (dataPlantaoField) dataPlantaoField.value = ''; 
                if (outroCondominioInput) outroCondominioInput.value = '';
                if (selectCondominio) selectCondominio.selectedIndex = 0;
                if (escalaPlantaoField) escalaPlantaoField.selectedIndex = 0;

                toggleOutroCondominio();
            }

            const reportOutputContainer = document.querySelector('.report-output-container');
            if(reportOutputContainer) {
                 reportOutputContainer.innerHTML = '<div id="rondaResultadoTexto" class="alert alert-secondary p-3">O relatório processado aparecerá aqui.</div>';
            }
            atualizarVisibilidadeBotoesAcaoRonda(); 
        });
    }

    function atualizarVisibilidadeBotoesAcaoRonda() {
        // console.log("atualizarVisibilidadeBotoesAcaoRonda chamada"); 
        const resultadoTextoEl = document.getElementById('rondaResultadoTexto'); 
        // console.log("resultadoTextoEl:", resultadoTextoEl); 
        
        let mostrarBotoes = false;
        if (resultadoTextoEl) {
            const textoResultado = (resultadoTextoEl.textContent || resultadoTextoEl.innerText || "").trim();
            const isPlaceholder = resultadoTextoEl.classList.contains('alert-secondary') &&
                                (textoResultado).includes("O relatório processado aparecerá aqui.");
            const isErrorMessage = resultadoTextoEl.classList.contains('alert-danger');
            const isWarningNoData = resultadoTextoEl.classList.contains('alert-warning');
            const isInfoNoResult = resultadoTextoEl.classList.contains('alert-info');

            mostrarBotoes = textoResultado && !isPlaceholder && !isErrorMessage && !isWarningNoData && !isInfoNoResult;
            // console.log("Texto:", textoResultado, "Placeholder:", isPlaceholder, "Error:", isErrorMessage, "Warning:", isWarningNoData, "Info:", isInfoNoResult, "Mostrar Botoes:", mostrarBotoes);
        } else {
            // console.warn("Elemento #rondaResultadoTexto não encontrado.");
        }
        
        if (btnCopiarRonda) {
            btnCopiarRonda.style.display = mostrarBotoes ? 'inline-block' : 'none';
        }
        if (btnEnviarWhatsAppRonda) {
            btnEnviarWhatsAppRonda.style.display = mostrarBotoes ? 'inline-block' : 'none';
        }
    }

    const resultContainer = document.querySelector('.report-output-container');
    if (resultContainer) {
        atualizarVisibilidadeBotoesAcaoRonda(); 

        const observer = new MutationObserver(function(mutationsList, observer) {
            atualizarVisibilidadeBotoesAcaoRonda();
        });
        observer.observe(resultContainer, { 
            childList: true, 
            characterData: true, 
            subtree: true, 
            attributes: true, 
            attributeFilter: ['class', 'id'] 
        });
    }

    if (btnCopiarRonda) {
        if (!btnCopiarRonda.dataset.originalHTML) { // Salva o HTML original do botão se não existir
            btnCopiarRonda.dataset.originalHTML = btnCopiarRonda.innerHTML;
        }
        btnCopiarRonda.addEventListener('click', function() {
            const elementoResultadoAtual = document.getElementById('rondaResultadoTexto');
            if (!elementoResultadoAtual) return;

            const textoParaCopiar = (elementoResultadoAtual.textContent || elementoResultadoAtual.innerText || "").trim();
            if (!textoParaCopiar) return;

            if (navigator.clipboard) {
                navigator.clipboard.writeText(textoParaCopiar)
                    .then(() => {
                        btnCopiarRonda.innerHTML = '<i class="bi bi-check-lg"></i> Copiado!'; 
                        btnCopiarRonda.disabled = true;
                        setTimeout(() => {
                            btnCopiarRonda.innerHTML = btnCopiarRonda.dataset.originalHTML; // Restaura
                            btnCopiarRonda.disabled = false;
                        }, 2000);
                    })
                    .catch(err => {
                        console.error('Falha ao copiar com navigator.clipboard: ', err);
                        tryFallbackCopyRonda(textoParaCopiar);
                    });
            } else {
                tryFallbackCopyRonda(textoParaCopiar);
            }
        });
    }
    
    function tryFallbackCopyRonda(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed"; // Posição fixa para evitar scroll
        textArea.style.top = "-9999px";    // Fora da tela
        textArea.style.left = "-9999px";   // Fora da tela
        textArea.style.opacity = "0";      // Invisível
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            const successful = document.execCommand('copy');
            if (successful && btnCopiarRonda) {
                btnCopiarRonda.innerHTML = '<i class="bi bi-check-lg"></i> Copiado!';
                btnCopiarRonda.disabled = true;
                setTimeout(() => {
                    btnCopiarRonda.innerHTML = btnCopiarRonda.dataset.originalHTML; // Restaura
                    btnCopiarRonda.disabled = false;
                }, 2000);
            } else if (!successful) {
                 throw new Error('document.execCommand("copy") falhou.');
            }
        } catch (err) {
            console.error('Falha ao copiar com fallback: ', err);
            alert('Não foi possível copiar o texto. Por favor, copie manualmente.');
        }
        document.body.removeChild(textArea);
    }

    if (btnEnviarWhatsAppRonda) {
        btnEnviarWhatsAppRonda.addEventListener('click', function() {
            const elementoResultadoAtual = document.getElementById('rondaResultadoTexto');
            if (!elementoResultadoAtual) {
                alert("Elemento do resultado não encontrado para enviar via WhatsApp.");
                return;
            }

            const textoRelatorio = (elementoResultadoAtual.textContent || elementoResultadoAtual.innerText || "").trim();
            
            if (textoRelatorio) {
                const textoCodificado = encodeURIComponent(textoRelatorio);
                const whatsappUrl = `https://wa.me/?text=${textoCodificado}`;
                window.open(whatsappUrl, '_blank');
            } else {
                alert("Não há relatório para enviar via WhatsApp.");
            }
        });
    }
});