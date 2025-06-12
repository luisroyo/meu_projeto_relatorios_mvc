// app/static/js/relatorio_ronda_page.js
document.addEventListener('DOMContentLoaded', function() {
    // Seletores de elementos do DOM
    const nomeCondominioSelect = document.getElementById('nome_condominio_select');
    const outroCondominioDiv = document.getElementById('outro_condominio_div');
    const logBrutoRondas = document.getElementById('log_bruto_rondas');
    const rondaResultadoTexto = document.getElementById('rondaResultadoTexto');
    const rondaActionsDiv = document.getElementById('ronda_actions');
    const copiarBtn = document.getElementById('copiarRelatorioRonda');
    const whatsappBtn = document.getElementById('enviarWhatsAppRonda');
    const salvarRondaBtn = document.getElementById('salvarRonda');

    function toggleOutroCondominio() {
        if (!nomeCondominioSelect || !outroCondominioDiv) return;
        outroCondominioDiv.style.display = (nomeCondominioSelect.value === 'Outro') ? 'block' : 'none';
    }

    function toggleRondaActions() {
        if (!rondaResultadoTexto || !rondaActionsDiv) return;
        const hasValidReport = rondaResultadoTexto &&
                               rondaResultadoTexto.textContent.trim() !== '' &&
                               !rondaResultadoTexto.classList.contains('alert-danger') &&
                               !rondaResultadoTexto.classList.contains('alert-secondary');
        rondaActionsDiv.style.display = hasValidReport ? 'block' : 'none';
    }

    function flashMessage(message, category = 'info') {
        const alertHtml = `
            <div class="alert alert-${category} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        const container = document.querySelector('.container-fluid');
        if (container) {
            const flashContainer = document.createElement('div');
            flashContainer.innerHTML = alertHtml;
            container.insertBefore(flashContainer, container.firstChild);
            setTimeout(() => {
                const newAlert = flashContainer.querySelector('.alert');
                if (newAlert) {
                    new bootstrap.Alert(newAlert).close();
                }
            }, 5000);
        }
    }

    async function salvarRondaCompleta() {
        // --- CORREÇÃO FINAL AQUI ---
        const currentRondaData = {
            ronda_id: rondaDataFromServer.ronda_id || null,
            log_bruto: logBrutoRondas.value,
            relatorio_processado: rondaResultadoTexto.textContent,
            condominio_id: nomeCondominioSelect.value,
            data_plantao: document.getElementById('data_plantao').value,
            escala_plantao: document.getElementById('escala_plantao').value,
            turno_ronda: rondaDataFromServer.turno_ronda,
            total_rondas_no_log: rondaDataFromServer.total_rondas_no_log,
            primeiro_evento_log_dt: rondaDataFromServer.primeiro_evento_log_dt,
            ultimo_evento_log_dt: rondaDataFromServer.ultimo_evento_log_dt,
            duracao_total_rondas_minutos: rondaDataFromServer.duracao_total_rondas_minutos // <-- NOVO CAMPO ADICIONADO
        };

        salvarRondaBtn.disabled = true;
        salvarRondaBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...';

        try {
            const response = await fetch('/ronda/rondas/salvar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify(currentRondaData)
            });
            const result = await response.json();
            if (result.success) {
                flashMessage(result.message, 'success');
                window.location.href = `/ronda/rondas/detalhes/${result.ronda_id}`;
            } else {
                flashMessage(result.message || 'Ocorreu um erro desconhecido ao salvar.', 'danger');
            }
        } catch (error) {
            flashMessage('Erro de comunicação com o servidor. Verifique sua conexão.', 'danger');
        } finally {
            salvarRondaBtn.disabled = false;
            salvarRondaBtn.innerHTML = '<i class="bi bi-check-circle"></i> Salvar';
        }
    }

    if (nomeCondominioSelect) {
        nomeCondominioSelect.addEventListener('change', toggleOutroCondominio);
        toggleOutroCondominio();
    }
    
    if (salvarRondaBtn) {
        salvarRondaBtn.addEventListener('click', salvarRondaCompleta);
    }

    if (copiarBtn) {
        copiarBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(rondaResultadoTexto.textContent)
                .then(() => flashMessage('Relatório copiado!', 'success'));
        });
    }

    if (whatsappBtn) {
        whatsappBtn.addEventListener('click', () => {
            const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(rondaResultadoTexto.textContent)}`;
            window.open(whatsappUrl, '_blank');
        });
    }

    toggleRondaActions();
});