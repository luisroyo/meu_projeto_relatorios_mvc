document.addEventListener('DOMContentLoaded', function() {
    const rondaForm = document.getElementById('rondaForm');
    const nomeCondominioSelect = document.getElementById('nome_condominio_select');
    const outroCondominioDiv = document.getElementById('outro_condominio_div');
    const nomeCondominioOutroInput = document.getElementById('nome_condominio_outro');
    const logBrutoRondas = document.getElementById('log_bruto_rondas');
    const rondaResultadoTexto = document.getElementById('rondaResultadoTexto');
    const rondaActionsDiv = document.getElementById('ronda_actions');
    const copiarBtn = document.getElementById('copiarRelatorioRonda');
    const whatsappBtn = document.getElementById('enviarWhatsAppRonda');
    const salvarRondaBtn = document.getElementById('salvarRonda');
    const supervisorSelect = document.getElementById('supervisor_id_select');

    function toggleOutroCondominio() {
        if (!nomeCondominioSelect || !outroCondominioDiv) return;
        outroCondominioDiv.style.display = (nomeCondominioSelect.value === 'Outro') ? 'block' : 'none';
    }

    function toggleRondaActions() {
        if (!rondaResultadoTexto || !rondaActionsDiv) return;
        const isEditMode = !!document.getElementById('ronda_id_input').value;
        const hasValidReport = rondaResultadoTexto &&
                                 rondaResultadoTexto.textContent.trim() !== '' &&
                                 !rondaResultadoTexto.classList.contains('alert-secondary');
        
        rondaActionsDiv.style.display = (isEditMode || hasValidReport) ? 'block' : 'none';
    }

    function resetForm() {
        rondaForm.reset();
        rondaResultadoTexto.textContent = 'O relatório processado aparecerá aqui.';
        rondaResultadoTexto.className = 'alert alert-secondary text-center';
        rondaActionsDiv.style.display = 'none';
        document.getElementById('ronda_id_input').value = '';
        toggleOutroCondominio();
        
        // Foca no primeiro campo do formulário para agilizar
        if(nomeCondominioSelect) nomeCondominioSelect.focus();
    }

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

    async function salvarRondaCompleta() {
        const dataToSend = {
            ronda_id: document.getElementById('ronda_id_input').value || null,
            log_bruto: logBrutoRondas.value,
            condominio_id: nomeCondominioSelect.value,
            nome_condominio_outro: nomeCondominioOutroInput.value,
            data_plantao: document.getElementById('data_plantao').value,
            escala_plantao: document.getElementById('escala_plantao').value,
            supervisor_id: supervisorSelect.value
        };

        salvarRondaBtn.disabled = true;
        salvarRondaBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...';

        try {
            const csrfToken = document.querySelector('input[name="csrf_token"]').value;
            const response = await fetch('/ronda/salvar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(dataToSend)
            });
            const result = await response.json();

            if (result.success) {
                flashMessage(result.message, 'success');
                if (!dataToSend.ronda_id) {
                    resetForm(); 
                }
            } else {
                flashMessage(result.message || 'Ocorreu um erro desconhecido.', 'danger');
            }
        } catch (error) {
            console.error('Erro no fetch:', error);
            flashMessage('Erro de comunicação com o servidor.', 'danger');
        } finally {
            salvarRondaBtn.disabled = false;
            salvarRondaBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Salvar';
        }
    } // <--- ESTE '}' ESTAVA FALTANDO. Ele fecha a função 'salvarRondaCompleta'.

    // --- Inicializadores de eventos ---
    if (nomeCondominioSelect) {
        nomeCondominioSelect.addEventListener('change', toggleOutroCondominio);
        toggleOutroCondominio();
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

    toggleRondaActions();
});