// app/static/js/relatorio_ronda_page.js
document.addEventListener('DOMContentLoaded', function() {
    // Seletores para os campos do formulário e elementos de resultado
    const selectCondominio = document.getElementById('nome_condominio_select');
    const outroCondominioDiv = document.getElementById('outro_condominio_div');
    const outroCondominioInput = document.getElementById('nome_condominio_outro_input');
    const logBrutoTextarea = document.getElementById('log_bruto_rondas_textarea');
    const resultadoTextoEl = document.getElementById('rondaResultadoTexto'); // O elemento que mostra o resultado
    const btnCopiarRonda = document.getElementById('copiarRelatorioRonda');
    const btnLimparFormRonda = document.getElementById('limparFormRonda');

    function toggleOutroCondominio() {
        if (selectCondominio && outroCondominioDiv) {
            if (selectCondominio.value === 'Outro') {
                outroCondominioDiv.style.display = 'block';
                // Opcional: dar foco ao campo se ele for exibido e estiver vazio
                // if(outroCondominioInput && !outroCondominioInput.value) {
                //     outroCondominioInput.focus();
                // }
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

    if (btnLimparFormRonda) {
        btnLimparFormRonda.addEventListener('click', function() {
            if(logBrutoTextarea) logBrutoTextarea.value = '';

            const form = document.getElementById('formRelatorioRonda');
            if (form) {
                 // Limpa campos específicos, exceto selectCondominio se quiser manter a seleção
                // form.reset(); // Isso resetaria todos os campos, incluindo selects para o primeiro valor
                if (document.getElementById('data_plantao_input')) {
                    // Se quiser resetar a data para hoje, precisa de lógica mais específica
                    // ou deixar que o backend defina o default na próxima carga.
                    // Por simplicidade, vamos apenas limpar o log.
                }
                if (outroCondominioInput) outroCondominioInput.value = '';
                // Resetar selects para o valor padrão (primeira opção)
                if (selectCondominio) selectCondominio.selectedIndex = 0;
                const escalaSelect = document.getElementById('escala_plantao_select');
                if (escalaSelect) escalaSelect.selectedIndex = 0;

                toggleOutroCondominio(); // Reavalia a visibilidade do campo "outro"
            }


            // Reseta o conteúdo e a classe do elemento de resultado para o estado inicial
            const reportOutputContainer = document.querySelector('.report-output-container');
            if(reportOutputContainer) {
                 reportOutputContainer.innerHTML = '<div id="rondaResultadoTexto" class="alert alert-secondary p-3">O relatório processado aparecerá aqui.</div>';
            }
            // A função atualizarVisibilidadeBotaoCopiarRonda (abaixo) será chamada pelo MutationObserver
            // ou pode ser chamada diretamente se não houver observer nesta página.
            if (btnCopiarRonda) {
                btnCopiarRonda.style.display = 'none';
            }
        });
    }

    function atualizarVisibilidadeBotaoCopiarRonda() {
        const novoResultadoTextoEl = document.getElementById('rondaResultadoTexto'); // Re-seleciona caso tenha sido recriado
        if (!novoResultadoTextoEl || !btnCopiarRonda) return; // Verifica se o botão também existe

        const textoResultado = novoResultadoTextoEl.textContent || novoResultadoTextoEl.innerText;
        const isPlaceholder = novoResultadoTextoEl.classList.contains('alert-secondary') &&
                            (textoResultado).includes("O relatório processado aparecerá aqui.");
        const isErrorMessage = novoResultadoTextoEl.classList.contains('alert-danger');
        const isWarningNoData = novoResultadoTextoEl.classList.contains('alert-warning') &&
                              (textoResultado.includes("Nenhum evento de ronda válido") || textoResultado.includes("Nenhum log de ronda fornecido"));
        const isInfoNoResult = novoResultadoTextoEl.classList.contains('alert-info');

        if (textoResultado.trim() && !isPlaceholder && !isErrorMessage && !isWarningNoData && !isInfoNoResult) {
            btnCopiarRonda.style.display = 'inline-block';
        } else {
            btnCopiarRonda.style.display = 'none';
        }
    }

    if (resultadoTextoEl && btnCopiarRonda) {
        atualizarVisibilidadeBotaoCopiarRonda(); // Chama uma vez para o estado inicial

        const resultContainer = document.querySelector('.report-output-container');
        if (resultContainer) {
            const observer = new MutationObserver(function(mutationsList, observer) {
                for(let mutation of mutationsList) {
                    if (mutation.type === 'childList' || mutation.type === 'characterData') {
                        atualizarVisibilidadeBotaoCopiarRonda();
                        break;
                    }
                }
            });
            observer.observe(resultContainer, { childList: true, characterData: true, subtree: true });
        }

        btnCopiarRonda.addEventListener('click', function() {
            const elementoResultadoAtual = document.getElementById('rondaResultadoTexto');
            if (!elementoResultadoAtual) return;

            const textoParaCopiar = elementoResultadoAtual.textContent || elementoResultadoAtual.innerText;
            if (!textoParaCopiar.trim()) return;

            if (navigator.clipboard) {
                navigator.clipboard.writeText(textoParaCopiar)
                    .then(() => {
                        const originalText = btnCopiarRonda.textContent;
                        btnCopiarRonda.innerHTML = '<i class="bi bi-check-lg"></i> Copiado!'; // Adiciona ícone
                        btnCopiarRonda.disabled = true;
                        setTimeout(() => {
                            btnCopiarRonda.textContent = originalText;
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
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            const successful = document.execCommand('copy');
            if (successful && btnCopiarRonda) {
                const originalText = "Copiar Relatório de Ronda";
                btnCopiarRonda.innerHTML = '<i class="bi bi-check-lg"></i> Copiado!'; // Adiciona ícone
                btnCopiarRonda.disabled = true;
                setTimeout(() => {
                    btnCopiarRonda.textContent = originalText;
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

    // Inicialização de tooltips do Bootstrap já é feita no base.html,
    // então não é necessário repetir aqui, a menos que esta página
    // adicione tooltips dinamicamente após o carregamento inicial.
});