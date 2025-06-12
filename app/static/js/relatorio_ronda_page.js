// app/static/js/relatorio_ronda_page.js
document.addEventListener('DOMContentLoaded', function() {
    // Seletores de elementos do DOM
    const nomeCondominioSelect = document.getElementById('nome_condominio_select');
    const outroCondominioDiv = document.getElementById('outro_condominio_div');
    const outroCondominioInput = document.getElementById('nome_condominio_outro');
    const logBrutoRondas = document.getElementById('log_bruto_rondas');
    const rondaResultadoTexto = document.getElementById('rondaResultadoTexto');
    const rondaActionsDiv = document.getElementById('ronda_actions');
    const copiarBtn = document.getElementById('copiarRelatorioRonda');
    const whatsappBtn = document.getElementById('enviarWhatsAppRonda');
    const salvarRondaBtn = document.getElementById('salvarRonda');
    const rondaIdInput = document.getElementById('ronda_id_input');
    const saveFeedbackDiv = document.getElementById('saveFeedback');
    const form = document.getElementById('rondaForm');

    // --- Lógica para o campo "Outro Condomínio" ---
    function toggleOutroCondominio() {
        if (!nomeCondominioSelect || !outroCondominioDiv) return;
        outroCondominioDiv.style.display = (nomeCondominioSelect.value === 'Outro') ? 'block' : 'none';
    }
    if (nomeCondominioSelect) {
        nomeCondominioSelect.addEventListener('change', toggleOutroCondominio);
    }

    // --- Lógica para exibir os botões de ação (Copiar, Salvar, etc.) ---
    function toggleRondaActions() {
        if (!rondaResultadoTexto || !rondaActionsDiv) return;
        const hasValidReport = rondaResultadoTexto &&
                               rondaResultadoTexto.textContent.trim() !== '' &&
                               !rondaResultadoTexto.classList.contains('alert-danger') &&
                               !rondaResultadoTexto.classList.contains('alert-secondary');
        
        rondaActionsDiv.style.display = hasValidReport ? 'block' : 'none';
    }

    // --- Função para exibir mensagens de feedback ---
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
            
            const newAlert = flashContainer.querySelector('.alert');
            // Remove a mensagem após 5 segundos
            setTimeout(() => {
                if (newAlert) newAlert.classList.remove('show');
                setTimeout(() => newAlert.remove(), 150); // espera a transição de fade out
            }, 5000);
        }
    }

    // --- Lógica para salvar a ronda ---
    async function salvarRondaCompleta() {
        // CORREÇÃO CRÍTICA: Incluindo os campos que faltavam
        const currentRondaData = {
            ronda_id: rondaDataFromServer.ronda_id || null,
            log_bruto: logBrutoRondas.value,
            relatorio_processado: rondaResultadoTexto.textContent,
            condominio_id: nomeCondominioSelect.value,
            data_plantao: document.getElementById('data_plantao').value,
            escala_plantao: document.getElementById('escala_plantao').value,
            turno_ronda: rondaDataFromServer.turno_ronda,
            total_rondas_no_log: rondaDataFromServer.total_rondas_no_log,
            primeiro_evento_log_dt: rondaDataFromServer.primeiro_evento_log_dt, // <-- ADICIONADO
            ultimo_evento_log_dt: rondaDataFromServer.ultimo_evento_log_dt     // <-- ADICIONADO
        };

        // Validações no frontend antes de enviar
        if (!currentRondaData.relatorio_processado || rondaResultadoTexto.classList.contains('alert-danger')) {
            return flashMessage('Um relatório processado válido é necessário para salvar.', 'warning');
        }
        if (currentRondaData.total_rondas_no_log > 0 && (!currentRondaData.primeiro_evento_log_dt || !currentRondaData.ultimo_evento_log_dt)) {
            return flashMessage('Erro: O relatório indica rondas, mas as datas de início/fim não foram encontradas. Tente processar novamente.', 'danger');
        }

        salvarRondaBtn.disabled = true;
        salvarRondaBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...';

        try {
            const response = await fetch('/ronda/rondas/salvar', { // URL Hardcoded é mais seguro que url_for no JS
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
                // Redireciona para a página de detalhes da ronda salva
                window.location.href = `/ronda/rondas/detalhes/${result.ronda_id}`;
            } else {
                flashMessage(result.message || 'Ocorreu um erro desconhecido ao salvar.', 'danger');
            }
        } catch (error) {
            console.error('Erro de comunicação ao salvar ronda:', error);
            flashMessage('Erro de comunicação com o servidor. Verifique sua conexão.', 'danger');
        } finally {
            salvarRondaBtn.disabled = false;
            salvarRondaBtn.innerHTML = '<i class="bi bi-check-circle"></i> Salvar';
        }
    }

    if (salvarRondaBtn) {
        salvarRondaBtn.addEventListener('click', salvarRondaCompleta);
    }
    
    // --- Lógica para Copiar e Enviar para WhatsApp ---
    if (copiarBtn) {
        copiarBtn.addEventListener('click', function() {
            const textToCopy = rondaResultadoTexto.innerText || rondaResultadoTexto.textContent;
            navigator.clipboard.writeText(textToCopy)
                .then(() => flashMessage('Relatório copiado!', 'success'))
                .catch(err => {
                    console.error('Erro ao copiar texto: ', err);
                    flashMessage('Falha ao copiar relatório.', 'danger');
                });
        });
    }

    if (whatsappBtn) {
        whatsappBtn.addEventListener('click', function() {
            const textToShare = rondaResultadoTexto.innerText || rondaResultadoTexto.textContent;
            const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(textToShare)}`;
            window.open(whatsappUrl, '_blank');
        });
    }


    // --- Inicialização da página ---
    // Preenche o formulário se os dados vierem do servidor (após processar o log)
    if (typeof rondaDataFromServer !== 'undefined' && Object.keys(rondaDataFromServer).length > 0) {
        if(rondaDataFromServer.condominio_id) nomeCondominioSelect.value = rondaDataFromServer.condominio_id;
        // Os outros campos já mantêm seus valores após o POST, então não precisamos preenchê-los novamente
    }
    // Garante que o estado inicial dos elementos esteja correto
    toggleOutroCondominio();
    toggleRondaActions();
});