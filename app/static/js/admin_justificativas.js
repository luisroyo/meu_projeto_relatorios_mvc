// static/js/admin_justificativas.js
document.addEventListener('DOMContentLoaded', function () {
    // Inicializa tooltips
    var tooltipTriggerListJustificativa = [].slice.call(document.querySelectorAll('#copiarJustificativa[data-bs-toggle="tooltip"]'));
    if (tooltipTriggerListJustificativa.length > 0 && typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        var tooltipListJustificativa = tooltipTriggerListJustificativa.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    const tipoSelect = document.getElementById("tipo_justificativa");
    const formFieldsContainer = document.getElementById("form-fields-justificativa");
    const resultadoDiv = document.getElementById("resultado_justificativa_texto");
    const statusDiv = document.getElementById("statusGeracaoJustificativa");
    const btnCopiar = document.getElementById('copiarJustificativa');
    const btnGerar = document.getElementById('btnGerarJustificativa'); 
    const spinner = document.getElementById('spinnerGerarJustificativa');
    const resultadoWrapper = document.getElementById('resultado_justificativa_wrapper');

    if (btnGerar) {
        btnGerar.addEventListener('click', gerarJustificativaTexto);
    }
    if (tipoSelect) {
        tipoSelect.addEventListener('change', mostrarCamposJustificativa);
        mostrarCamposJustificativa(); 
    }

    function mostrarCamposJustificativa() {
        if (!tipoSelect || !formFieldsContainer) return; 

        const tipo = tipoSelect.value;
        let html = "";

        if (tipo === "atestado") {
            html = `
                <div class="mb-3"><label for="just_at_funcionario" class="form-label">Funcionário:</label><input type="text" id="just_at_funcionario" class="form-control"></div>
                <div class="mb-3"><label for="just_at_cargo" class="form-label">Cargo:</label><input type="text" id="just_at_cargo" class="form-control"></div>
                <div class="mb-3"><label for="just_at_data_atestado" class="form-label">Data Inicial do Atestado:</label><input type="date" id="just_at_data_atestado" class="form-control"></div>
                <div class="mb-3"><label for="just_at_dias_afastamento" class="form-label">Dias de Afastamento:</label><input type="number" id="just_at_dias_afastamento" class="form-control" placeholder="Ex: 5" min="1"></div>
            `;
        } else if (tipo === "troca_plantao") {
            // Campos para Troca de Plantão
            html = `
                <div class="mb-3">
                    <label for="just_tp_colaborador_a_nome" class="form-label">Nome do Colaborador A (que irá cobrir):</label>
                    <input type="text" id="just_tp_colaborador_a_nome" class="form-control" placeholder="Ex: João Silva">
                </div>
                <div class="mb-3">
                    <label for="just_tp_colaborador_a_data_trabalho" class="form-label">Data em que Colaborador A trabalhará (cobrirá o plantão de B):</label>
                    <input type="date" id="just_tp_colaborador_a_data_trabalho" class="form-control">
                </div>
                <div class="mb-3">
                    <label for="just_tp_colaborador_b_nome" class="form-label">Nome do Colaborador B (terá o plantão coberto/folgará):</label>
                    <input type="text" id="just_tp_colaborador_b_nome" class="form-control" placeholder="Ex: Maria Oliveira">
                </div>
                <div class="mb-3">
                    <label for="just_tp_colaborador_b_data_compensacao" class="form-label">Data em que Colaborador B compensará (no plantão original de A):</label>
                    <input type="date" id="just_tp_colaborador_b_data_compensacao" class="form-control">
                </div>
            `;
        } else if (tipo === "atraso") {
            html = `
                <div class="mb-3"><label for="just_atr_funcionario" class="form-label">Funcionário:</label><input type="text" id="just_atr_funcionario" class="form-control"></div>
                <div class="mb-3"><label for="just_atr_cargo" class="form-label">Cargo:</label><input type="text" id="just_atr_cargo" class="form-control"></div>
                <div class="mb-3"><label for="just_atr_data_atraso" class="form-label">Data do Atraso:</label><input type="date" id="just_atr_data_atraso" class="form-control"></div>
                <div class="mb-3"><label for="just_atr_motivo" class="form-label">Motivo:</label><textarea id="just_atr_motivo" class="form-control" rows="3" placeholder="Descreva brevemente..."></textarea></div>
            `;
        }
        formFieldsContainer.innerHTML = html;
    }

    function formatarDataParaDisplay(dataInput) { // YYYY-MM-DD -> DD/MM/YYYY
        if (!dataInput) return '';
        const parts = dataInput.split('-');
        if (parts.length === 3) { return `${parts[2]}/${parts[1]}/${parts[0]}`; }
        return dataInput;
    }

    function calcularDiasAfastamento(dataInicioStr, numDias) {
        if (!dataInicioStr || isNaN(numDias) || numDias <= 0) return "Datas inválidas";
        const [year, month, day] = dataInicioStr.split('-').map(Number);
        const dataInicio = new Date(year, month - 1, day);
        let diasListados = "";
        for (let i = 0; i < numDias; i++) {
            const dataAtual = new Date(dataInicio);
            dataAtual.setDate(dataInicio.getDate() + i);
            const diaF = String(dataAtual.getDate()).padStart(2, '0');
            if (i < numDias - 1) {
                diasListados += diaF + (i < numDias - 2 ? ", " : "");
            } else {
                diasListados += (numDias > 1 ? " e " : "") + diaF + "/" + String(dataAtual.getMonth() + 1).padStart(2, '0') + "/" + dataAtual.getFullYear();
            }
        }
        return diasListados;
    }

    async function gerarJustificativaTexto() {
        if (!tipoSelect || !resultadoDiv || !statusDiv || !btnCopiar || !btnGerar || !spinner || !resultadoWrapper) {
            if (statusDiv) statusDiv.innerHTML = '<div class="alert alert-danger mt-3">Erro de interface. Recarregue a página.</div>';
            return;
        }
        const tipo = tipoSelect.value;
        if (!tipo) {
            statusDiv.innerHTML = '<div class="alert alert-warning mt-3">Por favor, selecione um tipo de justificativa.</div>';
            return;
        }

        let payload = { tipo_justificativa: tipo, dados_variaveis: {} };
        let dados_completos = true;

        if (tipo === "atestado") {
            const funcionario = document.getElementById("just_at_funcionario")?.value.trim();
            const cargo = document.getElementById("just_at_cargo")?.value.trim();
            const dataInicioInput = document.getElementById("just_at_data_atestado")?.value;
            const diasInput = document.getElementById("just_at_dias_afastamento")?.value;
            if (!funcionario || !cargo || !dataInicioInput || !diasInput || parseInt(diasInput) <= 0) {
                dados_completos = false;
            } else {
                payload.dados_variaveis = {
                    funcionario: funcionario,
                    cargo: cargo,
                    data_atestado: formatarDataParaDisplay(dataInicioInput), // DD/MM/YYYY
                    dias_afastamento: parseInt(diasInput),
                    lista_dias_afastamento: calcularDiasAfastamento(dataInicioInput, parseInt(diasInput))
                };
            }
        } else if (tipo === "troca_plantao") {
            const colab_a_nome = document.getElementById("just_tp_colaborador_a_nome")?.value.trim();
            const data_colab_a_input = document.getElementById("just_tp_colaborador_a_data_trabalho")?.value;
            const colab_b_nome = document.getElementById("just_tp_colaborador_b_nome")?.value.trim();
            const data_colab_b_input = document.getElementById("just_tp_colaborador_b_data_compensacao")?.value;
            
            if (!colab_a_nome || !data_colab_a_input || !colab_b_nome || !data_colab_b_input) {
                dados_completos = false;
            } else {
                payload.dados_variaveis = {
                    colaborador_a_nome: colab_a_nome,
                    colaborador_a_data_trabalho: formatarDataParaDisplay(data_colab_a_input), // DD/MM/YYYY
                    colaborador_b_nome: colab_b_nome,
                    colaborador_b_data_compensacao: formatarDataParaDisplay(data_colab_b_input) // DD/MM/YYYY
                };
            }
        } else if (tipo === "atraso") {
            const funcionario = document.getElementById("just_atr_funcionario")?.value.trim();
            const cargo = document.getElementById("just_atr_cargo")?.value.trim();
            const dataAtrasoInput = document.getElementById("just_atr_data_atraso")?.value;
            const motivo = document.getElementById("just_atr_motivo")?.value.trim();
            if (!funcionario || !cargo || !dataAtrasoInput || !motivo) {
                dados_completos = false;
            } else {
                payload.dados_variaveis = {
                    funcionario: funcionario,
                    cargo: cargo,
                    data_atraso: formatarDataParaDisplay(dataAtrasoInput), // DD/MM/YYYY
                    motivo: motivo
                };
            }
        }

        if (!dados_completos) {
            statusDiv.innerHTML = '<div class="alert alert-warning mt-3">Por favor, preencha todos os campos corretamente.</div>';
            return;
        }

        resultadoWrapper.style.display = 'none';
        statusDiv.innerHTML = '<div class="alert alert-info mt-3">Enviando para IA e gerando texto...</div>';
        if(spinner) spinner.style.display = 'inline-block';
        if(btnGerar) btnGerar.disabled = true;

        try {
            if (typeof justificativaApiUrl === 'undefined' || typeof csrfToken === 'undefined') {
                throw new Error("Variáveis de configuração da API não definidas no HTML.");
            }
            const response = await fetch(justificativaApiUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify(payload) // Envia o payload com tipo_justificativa e dados_variaveis
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({erro: "Erro ao processar resposta."}));
                throw new Error(errorData.erro || `Erro do servidor: ${response.status} ${response.statusText}`);
            }
            const data = await response.json();
            if (data.justificativa_gerada) {
                resultadoDiv.innerText = data.justificativa_gerada;
                resultadoWrapper.style.display = 'block';
                statusDiv.innerHTML = '<div class="alert alert-success mt-3">Justificativa gerada!</div>';
            } else if (data.erro) {
                statusDiv.innerHTML = `<div class="alert alert-danger mt-3">Erro: ${data.erro}</div>`;
            } else {
                 statusDiv.innerHTML = '<div class="alert alert-warning mt-3">Resposta inesperada.</div>';
            }
        } catch (e) {
            console.error("Erro na API:", e);
            statusDiv.innerHTML = `<div class="alert alert-danger mt-3">Falha: ${e.message}</div>`;
        } finally {
            if(spinner) spinner.style.display = 'none';
            if(btnGerar) btnGerar.disabled = false;
        }
    }

    const btnCopiarJustificativaEl = document.getElementById('copiarJustificativa');
    const resultadoJustificativaTextoEl = document.getElementById('resultado_justificativa_texto');
    if (btnCopiarJustificativaEl && resultadoJustificativaTextoEl) {
        var tooltipCopiarJust = (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) ? new bootstrap.Tooltip(btnCopiarJustificativaEl) : null;
        btnCopiarJustificativaEl.addEventListener('click', function() {
            const textoParaCopiar = resultadoJustificativaTextoEl.innerText;
            if (!textoParaCopiar.trim()) return;
            navigator.clipboard.writeText(textoParaCopiar).then(() => {
                const originalHTML = btnCopiarJustificativaEl.innerHTML;
                btnCopiarJustificativaEl.innerHTML = '<i class="bi bi-check-lg me-1"></i>Copiado!';
                btnCopiarJustificativaEl.setAttribute('data-bs-original-title', 'Copiado!');
                if (tooltipCopiarJust && typeof tooltipCopiarJust.show === 'function') tooltipCopiarJust.show();
                setTimeout(() => {
                    btnCopiarJustificativaEl.innerHTML = originalHTML;
                    btnCopiarJustificativaEl.setAttribute('data-bs-original-title', 'Copiar para a área de transferência');
                    if (tooltipCopiarJust && typeof tooltipCopiarJust.hide === 'function') tooltipCopiarJust.hide();
                }, 2000);
            }).catch(err => console.error('Falha ao copiar: ', err));
        });
    }
});
