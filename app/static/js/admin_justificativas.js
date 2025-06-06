// static/js/admin_justificativas.js
document.addEventListener('DOMContentLoaded', function () {
    var tooltipTriggerListJustificativa = [].slice.call(document.querySelectorAll('#copiarJustificativa[data-bs-toggle="tooltip"]'));
    if (tooltipTriggerListJustificativa.length > 0 && typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        tooltipTriggerListJustificativa.map(function (tooltipTriggerEl) {
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

    function criarCampoColaboradorHTML(baseId, labelText) {
        return `
            <div class="mb-3 autocomplete-container" data-field-group="${baseId}">
                <label for="${baseId}_nome" class="form-label">${labelText}:</label>
                <input type="text" id="${baseId}_nome" name="${baseId}_nome" class="form-control colaborador-autocomplete-nome" autocomplete="off" data-target-id="${baseId}_id" data-target-cargo="${baseId}_cargo">
                <input type="hidden" id="${baseId}_id" name="${baseId}_id">
                <div class="autocomplete-suggestions" style="display: none;"></div>
            </div>
            <div class="mb-3" data-field-group="${baseId}">
                <label for="${baseId}_cargo" class="form-label">Cargo:</label>
                <input type="text" id="${baseId}_cargo" name="${baseId}_cargo" class="form-control" readonly>
            </div>
        `;
    }

    function inicializarAutocomplete(inputNomeEl) {
        if (!inputNomeEl) return;

        const targetIdEl = document.getElementById(inputNomeEl.dataset.targetId);
        const targetCargoEl = document.getElementById(inputNomeEl.dataset.targetCargo);
        const suggestionsDivEl = inputNomeEl.parentElement.querySelector('.autocomplete-suggestions');

        if (!targetIdEl || !targetCargoEl || !suggestionsDivEl) {
            console.error("Elementos alvo para autocomplete não encontrados para:", inputNomeEl.id);
            return;
        }

        inputNomeEl.addEventListener('input', async function () {
            const termo = this.value.trim();
            targetIdEl.value = '';
            targetCargoEl.value = '';

            if (termo.length < 2) {
                suggestionsDivEl.innerHTML = '';
                suggestionsDivEl.style.display = 'none';
                return;
            }

            try {
                const response = await fetch(`${apiUrlSearchColaboradores}?term=${encodeURIComponent(termo)}`);
                if (!response.ok) {
                    throw new Error(`Erro na API de busca: ${response.status}`);
                }
                const colaboradores = await response.json();
                
                suggestionsDivEl.innerHTML = '';
                if (colaboradores.length > 0) {
                    colaboradores.forEach(col => {
                        const divItem = document.createElement('div');
                        divItem.textContent = `${col.nome_completo} (${col.cargo || 'Cargo não informado'})`;
                        divItem.dataset.colaboradorId = col.id;
                        divItem.dataset.colaboradorNome = col.nome_completo;
                        divItem.dataset.colaboradorCargo = col.cargo || '';
                        
                        divItem.addEventListener('click', function () {
                            inputNomeEl.value = this.dataset.colaboradorNome;
                            targetIdEl.value = this.dataset.colaboradorId;
                            targetCargoEl.value = this.dataset.colaboradorCargo;
                            suggestionsDivEl.innerHTML = '';
                            suggestionsDivEl.style.display = 'none';
                        });
                        suggestionsDivEl.appendChild(divItem);
                    });
                    suggestionsDivEl.style.display = 'block';
                } else {
                    suggestionsDivEl.style.display = 'none';
                }
            } catch (error) {
                console.error("Erro ao buscar colaboradores:", error);
                suggestionsDivEl.innerHTML = '<div class="text-danger p-2">Erro ao buscar.</div>';
                suggestionsDivEl.style.display = 'block';
            }
        });

        document.addEventListener('click', function(e) {
            if (!inputNomeEl.contains(e.target) && !suggestionsDivEl.contains(e.target)) {
                suggestionsDivEl.style.display = 'none';
            }
        });
    }

    function mostrarCamposJustificativa() {
        if (!tipoSelect || !formFieldsContainer) return;
        const tipo = tipoSelect.value;
        let html = "";

        if (tipo === "atestado") {
            html = criarCampoColaboradorHTML('just_at_funcionario', 'Funcionário') + `
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
            html = criarCampoColaboradorHTML('just_tp_colaborador_a', 'Colaborador A (que irá cobrir)') + `
                <div class="mb-3"><label for="just_tp_colaborador_a_data_trabalho" class="form-label">Data em que Colaborador A trabalhará (cobrirá B):</label><input type="date" id="just_tp_colaborador_a_data_trabalho" class="form-control"></div>
            ` + criarCampoColaboradorHTML('just_tp_colaborador_b', 'Colaborador B (terá plantão coberto)') + `
                <div class="mb-3"><label for="just_tp_colaborador_b_data_compensacao" class="form-label">Data em que Colaborador B compensará (plantão de A):</label><input type="date" id="just_tp_colaborador_b_data_compensacao" class="form-control"></div>
            `;
        } else if (tipo === "atraso") {
            html = criarCampoColaboradorHTML('just_atr_funcionario', 'Funcionário') + `
                <div class="mb-3"><label for="just_atr_data_atraso" class="form-label">Data do Atraso:</label><input type="date" id="just_atr_data_atraso" class="form-control"></div>
                <div class="mb-3"><label for="just_atr_motivo" class="form-label">Motivo:</label><textarea id="just_atr_motivo" class="form-control" rows="3" placeholder="Descreva brevemente..."></textarea></div>
            `;
        }
        formFieldsContainer.innerHTML = html;

        formFieldsContainer.querySelectorAll('.colaborador-autocomplete-nome').forEach(inputEl => {
            inicializarAutocomplete(inputEl);
        });

        if (tipo === "atestado") {
            const tipoDuracaoSelect = document.getElementById("just_at_tipo_duracao");
            const diasWrapper = document.getElementById("just_at_duracao_dias_wrapper");
            const horasWrapper = document.getElementById("just_at_duracao_horas_wrapper");
            if (tipoDuracaoSelect && diasWrapper && horasWrapper) {
                function toggleDuracaoFields() {
                    if (tipoDuracaoSelect.value === "dias") {
                        diasWrapper.style.display = 'block';
                        horasWrapper.style.display = 'none';
                        if(document.getElementById("just_at_horas_afastamento")) document.getElementById("just_at_horas_afastamento").value = '';
                    } else {
                        diasWrapper.style.display = 'none';
                        horasWrapper.style.display = 'block';
                        if(document.getElementById("just_at_dias_afastamento")) document.getElementById("just_at_dias_afastamento").value = '';
                    }
                }
                tipoDuracaoSelect.addEventListener('change', toggleDuracaoFields);
                toggleDuracaoFields(); 
            }
        }
    }

    function formatarDataParaDisplay(dataInput) {
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
            const mesF = String(dataAtual.getMonth() + 1).padStart(2, '0');
            if (i < numDias - 1) {
                diasListados += diaF + (i < numDias - 2 ? ", " : "");
            } else {
                diasListados += (numDias > 1 ? " e " : "") + diaF + "/" + mesF + "/" + dataAtual.getFullYear();
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
            const funcionarioNome = document.getElementById("just_at_funcionario_nome")?.value.trim();
            const funcionarioId = document.getElementById("just_at_funcionario_id")?.value;
            const funcionarioCargo = document.getElementById("just_at_funcionario_cargo")?.value.trim();
            const dataAtestadoInput = document.getElementById("just_at_data_atestado")?.value;
            const tipoDuracao = document.getElementById("just_at_tipo_duracao")?.value;
            
            payload.dados_variaveis = {
                funcionario: funcionarioNome,
                cargo: funcionarioCargo,
                data_atestado: formatarDataParaDisplay(dataAtestadoInput),
                tipo_duracao: tipoDuracao
            };

            if (!funcionarioNome || !funcionarioCargo || !dataAtestadoInput || !tipoDuracao) {
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
                    const horasInput = document.getElementById("just_at_horas_afastamento")?.value.trim();
                    if (!horasInput) {
                        dados_completos = false;
                    } else {
                        payload.dados_variaveis.horas_afastamento_str = horasInput;
                        payload.dados_variaveis.lista_dias_afastamento = formatarDataParaDisplay(dataAtestadoInput);
                        payload.dados_variaveis.duracao_texto = horasInput;
                    }
                }
            }
        } else if (tipo === "troca_plantao") {
            const colab_a_nome_val = document.getElementById("just_tp_colaborador_a_nome")?.value.trim();
            const colab_a_cargo_val = document.getElementById("just_tp_colaborador_a_cargo")?.value.trim();
            const data_colab_a_input_val = document.getElementById("just_tp_colaborador_a_data_trabalho")?.value;
            
            const colab_b_nome_val = document.getElementById("just_tp_colaborador_b_nome")?.value.trim();
            const colab_b_cargo_val = document.getElementById("just_tp_colaborador_b_cargo")?.value.trim();
            const data_colab_b_input_val = document.getElementById("just_tp_colaborador_b_data_compensacao")?.value;
            
            if (!colab_a_nome_val || !data_colab_a_input_val || !colab_b_nome_val || !data_colab_b_input_val) {
                dados_completos = false;
            } else {
                // --- CORREÇÃO APLICADA AQUI ---
                payload.dados_variaveis = {
                    colaborador_a_nome: colab_a_nome_val,
                    colaborador_a_data_trabalho: formatarDataParaDisplay(data_colab_a_input_val),
                    colaborador_b_nome: colab_b_nome_val,
                    colaborador_b_data_compensacao: formatarDataParaDisplay(data_colab_b_input_val), // Corrigido para usar o campo de data correto
                    cargo: colab_a_cargo_val || colab_b_cargo_val || ''
                };
            }
        } else if (tipo === "atraso") {
            const funcionarioNome = document.getElementById("just_atr_funcionario_nome")?.value.trim();
            const funcionarioCargo = document.getElementById("just_atr_funcionario_cargo")?.value.trim();
            const dataAtrasoInput = document.getElementById("just_atr_data_atraso")?.value;
            const motivo = document.getElementById("just_atr_motivo")?.value.trim();
            if (!funcionarioNome || !funcionarioCargo || !dataAtrasoInput || !motivo) {
                dados_completos = false;
            } else {
                payload.dados_variaveis = {
                    funcionario: funcionarioNome,
                    cargo: funcionarioCargo,
                    data_atraso: formatarDataParaDisplay(dataAtrasoInput), 
                    motivo: motivo
                };
            }
        }

        if (!dados_completos) {
            statusDiv.innerHTML = '<div class="alert alert-warning mt-3">Por favor, preencha todos os campos obrigatórios corretamente.</div>';
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
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({erro: "Erro ao processar resposta do servidor."}));
                throw new Error(errorData.erro || `Erro do servidor: ${response.status} ${response.statusText}`);
            }
            const data = await response.json();
            if (data.justificativa_gerada) {
                resultadoDiv.innerText = data.justificativa_gerada;
                resultadoWrapper.style.display = 'block';
                statusDiv.innerHTML = '<div class="alert alert-success mt-3">Justificativa gerada!</div>';
            } else if (data.erro) {
                statusDiv.innerHTML = `<div class="alert alert-danger mt-3">Erro ao gerar: ${data.erro}</div>`;
            } else {
                 statusDiv.innerHTML = '<div class="alert alert-warning mt-3">Resposta inesperada do servidor.</div>';
            }
        } catch (e) {
            console.error("Erro na API de justificativa:", e);
            statusDiv.innerHTML = `<div class="alert alert-danger mt-3">Falha na comunicação: ${e.message}</div>`;
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
    
    if (btnGerar) {
        btnGerar.addEventListener('click', gerarJustificativaTexto);
    }
    if (tipoSelect) {
        tipoSelect.addEventListener('change', mostrarCamposJustificativa);
        mostrarCamposJustificativa();
    }
});