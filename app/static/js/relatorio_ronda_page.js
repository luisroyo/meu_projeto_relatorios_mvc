// app/static/js/relatorio_ronda_page.js
document.addEventListener('DOMContentLoaded', function() {
    // ---- SELETORES CORRIGIDOS ----
    const nomeCondominioSelect = document.getElementById('nome_condominio_select'); // CORRIGIDO
    const supervisorSelect = document.getElementById('supervisor_id_select');       // CORRIGIDO

    // Seletores que já estavam corretos
    const outroCondominioDiv = document.getElementById('outro_condominio_div');
    const logBrutoRondas = document.getElementById('log_bruto_rondas');
    const rondaResultadoTexto = document.getElementById('rondaResultadoTexto');
    const rondaActionsDiv = document.getElementById('ronda_actions');
    const copiarBtn = document.getElementById('copiarRelatorioRonda');
    const whatsappBtn = document.getElementById('enviarWhatsAppRonda');
    const salvarRondaBtn = document.getElementById('salvarRonda');

    /**
     * Alterna a visibilidade do campo de texto para inserir um novo condomínio.
     */
    function toggleOutroCondominio() {
        if (!nomeCondominioSelect || !outroCondominioDiv) return;
        outroCondominioDiv.style.display = (nomeCondominioSelect.value === 'Outro') ? 'block' : 'none';
    }

    /**
     * Alterna a visibilidade dos botões de ação (copiar, whatsapp, salvar)
     * com base na presença de um relatório válido.
     */
    function toggleRondaActions() {
        if (!rondaResultadoTexto || !rondaActionsDiv) return;
        const hasValidReport = rondaResultadoTexto &&
                                 rondaResultadoTexto.textContent.trim() !== '' &&
                                 !rondaResultadoTexto.classList.contains('alert-danger') &&
                                 !rondaResultadoTexto.classList.contains('alert-secondary');
        rondaActionsDiv.style.display = hasValidReport ? 'block' : 'none';
    }

    /**
     * Exibe uma mensagem flash (alerta) temporária na tela.
     * @param {string} message - A mensagem a ser exibida.
     * @param {string} category - A categoria do alerta (e.g., 'success', 'danger').
     */
    function flashMessage(message, category = 'info') {
        const alertHtml = `
            <div class="alert alert-${category} alert-dismissible fade show" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 9999;">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        const flashContainer = document.createElement('div');
        flashContainer.innerHTML = alertHtml;
        document.body.appendChild(flashContainer);
        
        setTimeout(() => {
            const newAlert = flashContainer.querySelector('.alert');
            if (newAlert) {
                new bootstrap.Alert(newAlert).close();
            }
        }, 5000);
    }

    /**
     * Coleta todos os dados da ronda do formulário e do objeto 'rondaDataFromServer',
     * e os envia para a rota de salvamento no backend.
     */
    async function salvarRondaCompleta() {
        if (typeof rondaDataFromServer === 'undefined' || !rondaDataFromServer) {
            flashMessage('Não foi possível encontrar os dados processados da ronda para salvar.', 'danger');
            return;
        }

        const currentRondaData = {
            ronda_id: rondaDataFromServer.ronda_id || null,
            log_bruto: logBrutoRondas.value,
            relatorio_processado: rondaResultadoTexto.textContent,
            condominio_id: nomeCondominioSelect.value,
            data_plantao: document.getElementById('data_plantao').value,
            escala_plantao: document.getElementById('escala_plantao').value,
            supervisor_id: supervisorSelect.value, // Agora 'supervisorSelect' não será nulo
            turno_ronda: rondaDataFromServer.turno_ronda,
            total_rondas_no_log: rondaDataFromServer.total_rondas_no_log,
            primeiro_evento_log_dt: rondaDataFromServer.primeiro_evento_log_dt,
            ultimo_evento_log_dt: rondaDataFromServer.ultimo_evento_log_dt,
            duracao_total_rondas_minutos: rondaDataFromServer.duracao_total_rondas_minutos
        };

        salvarRondaBtn.disabled = true;
        salvarRondaBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...';

        try {
            const response = await fetch('/ronda/rondas/salvar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                },
                body: JSON.stringify(currentRondaData)
            });
            const result = await response.json();
            if (result.success) {
                flashMessage(result.message, 'success');
                // Adiciona um pequeno delay antes de redirecionar para o usuário ver a mensagem
                setTimeout(() => {
                    window.location.href = `/ronda/rondas/detalhes/${result.ronda_id}`;
                }, 1000);
            } else {
                flashMessage(result.message || 'Ocorreu um erro desconhecido ao salvar.', 'danger');
            }
        } catch (error) {
            console.error('Erro no fetch:', error);
            flashMessage('Erro de comunicação com o servidor. Verifique sua conexão.', 'danger');
        } finally {
            salvarRondaBtn.disabled = false;
            salvarRondaBtn.innerHTML = '<i class="bi bi-check-circle"></i> Salvar';
        }
    }

    // --- Inicializadores de eventos ---
    if (nomeCondominioSelect) {
        nomeCondominioSelect.addEventListener('change', toggleOutroCondominio);
        toggleOutroCondominio(); // Executa na carga da página
    }
    
    if (salvarRondaBtn) {
        salvarRondaBtn.addEventListener('click', salvarRondaCompleta);
    }

    if (copiarBtn) {
        copiarBtn.addEventListener('click', () => {
            if (rondaResultadoTexto && rondaResultadoTexto.textContent) {
                navigator.clipboard.writeText(rondaResultadoTexto.textContent)
                    .then(() => flashMessage('Relatório copiado!', 'success'))
                    .catch(err => {
                        console.error('Erro ao copiar:', err);
                        flashMessage('Falha ao copiar o relatório.', 'danger');
                    });
            }
        });
    }

    if (whatsappBtn) {
        whatsappBtn.addEventListener('click', () => {
            if (rondaResultadoTexto && rondaResultadoTexto.textContent) {
                const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(rondaResultadoTexto.textContent)}`;
                window.open(whatsappUrl, '_blank');
            }
        });
    }

    // Verifica se os botões de ação devem ser exibidos na carga da página
    toggleRondaActions();
});