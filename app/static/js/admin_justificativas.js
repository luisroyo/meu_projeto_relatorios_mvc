// static/js/admin_justificativas.js
document.addEventListener('DOMContentLoaded', function () {
    // ... (código inicial do JS, inicialização de tooltips, seletores de DOM como antes) ...
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
                <div class="mb-3"><label for="just_at_data_atestado" class="form-label">Data do Atestado/Afastamento:</label><input type="date" id="just_at_data_atestado" class="form-control"></div>
                
                <div class="mb-3">
                    <label for="just_at_tipo_duracao" class="form-label">Tipo de Duração do Afastamento:</label>
                    <select id="just_at_tipo_duracao" class="form-select">
                        <option value="dias" selected>Dias</option>
                        <option value="horas">Horas</option>
                    </select>
                </div>
                
                <div id="just_at_duracao_dias_wrapper" class="mb-3">
                    <label for="just_at_dias_afastamento" class="form-label">Dias de Afastamento:</label>
                    <input type="number" id="just_at_dias_afastamento" class="form-control" placeholder="Ex: 5" min="1">
                </div>
                
                <div id="just_at_duracao_horas_wrapper" class="mb-3" style="display: none;">
                    <label for="just_at_horas_afastamento" class="form-label">Horas de Afastamento (ex: 2, 2.5, 2h30m):</label>
                    <input type="text" id="just_at_horas_afastamento" class="form-control" placeholder="Ex: 2h30m ou 2.5"> 
                </div>
            `;
        } else if (tipo === "troca_plantao") {
            // ... (código para troca de plantão como antes) ...
            html = `
                <div class="mb-3"><label for="just_tp_colaborador_a_nome" class="form-label">Nome do Colaborador A (que irá cobrir):</label><input type="text" id="just_tp_colaborador_a_nome" class="form-control" placeholder="Ex: João Silva"></div>
                <div class="mb-3"><label for="just_tp_colaborador_a_data_trabalho" class="form-label">Data em que Colaborador A trabalhará (cobrirá B):</label><input type="date" id="just_tp_colaborador_a_data_trabalho" class="form-control"></div>
                <div class="mb-3"><label for="just_tp_colaborador_b_nome" class="form-label">Nome do Colaborador B (terá plantão coberto):</label><input type="text" id="just_tp_colaborador_b_nome" class="form-control" placeholder="Ex: Maria Oliveira"></div>
                <div class="mb-3"><label for="just_tp_colaborador_b_data_compensacao" class="form-label">Data em que Colaborador B compensará (plantão de A):</label><input type="date" id="just_tp_colaborador_b_data_compensacao" class="form-control"></div>
            `;
        } else if (tipo === "atraso") {
            // ... (código para atraso como antes) ...
            html = `
                <div class="mb-3"><label for="just_atr_funcionario" class="form-label">Funcionário:</label><input type="text" id="just_atr_funcionario" class="form-control"></div>
                <div class="mb-3"><label for="just_atr_cargo" class="form-label">Cargo:</label><input type="text" id="just_atr_cargo" class="form-control"></div>
                <div class="mb-3"><label for="just_atr_data_atraso" class="form-label">Data do Atraso:</label><input type="date" id="just_atr_data_atraso" class="form-control"></div>
                <div class="mb-3"><label for="just_atr_motivo" class="form-label">Motivo:</label><textarea id="just_atr_motivo" class="form-control" rows="3" placeholder="Descreva brevemente..."></textarea></div>
            `;
        }
        formFieldsContainer.innerHTML = html;

        if (tipo === "atestado") {
            const tipoDuracaoSelect = document.getElementById("just_at_tipo_duracao");
            const diasWrapper = document.getElementById("just_at_duracao_dias_wrapper");
            const horasWrapper = document.getElementById("just_at_duracao_horas_wrapper");
            if (tipoDuracaoSelect && diasWrapper && horasWrapper) {
                tipoDuracaoSelect.addEventListener('change', function() {
                    if (this.value === "dias") {
                        diasWrapper.style.display = 'block';
                        horasWrapper.style.display = 'none';
                        document.getElementById("just_at_horas_afastamento").value = ''; // Limpa o campo de horas
                    } else { 
                        diasWrapper.style.display = 'none';
                        horasWrapper.style.display = 'block';
                        document.getElementById("just_at_dias_afastamento").value = ''; // Limpa o campo de dias
                    }
                });
                // Garante que o estado inicial está correto
                if (tipoDuracaoSelect.value === "dias") {
                    diasWrapper.style.display = 'block';
                    horasWrapper.style.display = 'none';
                } else {
                    diasWrapper.style.display = 'none';
                    horasWrapper.style.display = 'block';
                }
            }
        }
    }

    function formatarDataParaDisplay(dataInput) { 
        // ... (função como antes) ...
        if (!dataInput) return '';
        const parts = dataInput.split('-');
        if (parts.length === 3) { return `${parts[2]}/${parts[1]}/${parts[0]}`; }
        return dataInput;
    }

    function calcularDiasAfastamento(dataInicioStr, numDias) {
        // ... (função como antes) ...
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
        // ... (código inicial da função, checagens de DOM, etc. permanecem iguais) ...
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
            const dataAtestadoInput = document.getElementById("just_at_data_atestado")?.value;
            const tipoDuracao = document.getElementById("just_at_tipo_duracao")?.value;
            
            payload.dados_variaveis = {
                funcionario: funcionario,
                cargo: cargo,
                data_atestado: formatarDataParaDisplay(dataAtestadoInput),
                tipo_duracao: tipoDuracao
            };

            if (!funcionario || !cargo || !dataAtestadoInput || !tipoDuracao) {
                dados_completos = false;
            } else {
                if (tipoDuracao === "dias") {
                    const diasInput = document.getElementById("just_at_dias_afastamento")?.value;
                    if (!diasInput || parseInt(diasInput) <= 0) {
                        dados_completos = false;
                    } else {
                        const diasNum = parseInt(diasInput);
                        payload.dados_variaveis.dias_afastamento = diasNum;
                        payload.dados_variaveis.lista_dias_afastamento = calcularDiasAfastamento(dataAtestadoInput, diasNum);
                        payload.dados_variaveis.duracao_texto = `${diasNum} dia${diasNum > 1 ? 's' : ''}`;
                    }
                } else { // horas
                    const horasInput = document.getElementById("just_at_horas_afastamento")?.value.trim(); // Pega como texto
                    if (!horasInput) { // Verifica se o campo de horas não está vazio
                        dados_completos = false;
                    } else {
                        payload.dados_variaveis.horas_afastamento_str = horasInput; // Envia a string como "3h21m" ou "2.5"
                        payload.dados_variaveis.lista_dias_afastamento = formatarDataParaDisplay(dataAtestadoInput); // Para horas, a lista é só a data
                        payload.dados_variaveis.duracao_texto = horasInput; // Usa a string diretamente
                    }
                }
            }
        } else if (tipo === "troca_plantao") {
            // ... (lógica para troca_plantao como antes) ...
            const colab_a_nome_val = document.getElementById("just_tp_colaborador_a_nome")?.value.trim();
            const data_colab_a_input_val = document.getElementById("just_tp_colaborador_a_data_trabalho")?.value;
            const colab_b_nome_val = document.getElementById("just_tp_colaborador_b_nome")?.value.trim();
            const data_colab_b_input_val = document.getElementById("just_tp_colaborador_b_data_compensacao")?.value;
            
            if (!colab_a_nome_val || !data_colab_a_input_val || !colab_b_nome_val || !data_colab_b_input_val) {
                dados_completos = false;
            } else {
                payload.dados_variaveis = {
                    NOME_COLABORADOR_A: colab_a_nome_val,
                    DATA_TRABALHO_COLABORADOR_A: formatarDataParaDisplay(data_colab_a_input_val),
                    NOME_COLABORADOR_B: colab_b_nome_val,
                    DATA_COMPENSACAO_COLABORADOR_B: formatarDataParaDisplay(data_colab_b_input_val)
                };
            }
        } else if (tipo === "atraso") {
            // ... (lógica para atraso como antes) ...
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
                    data_atraso: formatarDataParaDisplay(dataAtrasoInput), 
                    motivo: motivo
                };
            }
        }


        if (!dados_completos) {
            statusDiv.innerHTML = '<div class="alert alert-warning mt-3">Por favor, preencha todos os campos corretamente.</div>';
            return;
        }

        // ... (resto da função gerarJustificativaTexto: fetch, .then, .catch, .finally permanece o mesmo) ...
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
                body: JSON.stringify(payload)
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

    // ... (código para copiar justificativa permanece o mesmo) ...
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
