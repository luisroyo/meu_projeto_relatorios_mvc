// app/static/js/index_page/main.js
import { CONFIG, DOMElements } from './config.js';
import { updateCharCount, displayStatus } from './uiHandlers.js';
import { handleProcessReport, handleClearFields, handleCopyResult, handleSendToWhatsApp } from './reportLogic.js';

/**
 * Exibe um botão para iniciar o processo de registo de ocorrência oficial.
 * Esta função é chamada após o relatório da IA ser gerado com sucesso.
 * @param {string} logBruto O texto original inserido pelo utilizador.
 * @param {string} relatorioProcessado O texto corrigido pela IA.
 */
function exibirBotaoRegistrarOcorrencia(logBruto, relatorioProcessado) {
    const containerBotoes = document.querySelector('#resultadoProcessamento').parentElement.nextElementSibling;
    if (!containerBotoes) {
        console.error("Container de botões não encontrado.");
        return;
    }

    // Remove o botão antigo para evitar duplicação
    const botaoAntigo = document.getElementById('registrarOcorrenciaOficial');
    if (botaoAntigo) {
        botaoAntigo.remove();
    }

    const botaoSalvar = document.createElement('button');
    botaoSalvar.id = 'registrarOcorrenciaOficial';
    botaoSalvar.type = 'button';
    botaoSalvar.className = 'btn btn-success btn-lg w-100 mt-2'; // Cor verde para destacar a ação principal
    botaoSalvar.innerHTML = '<i class="bi bi-shield-plus me-2"></i>Registrar Ocorrência Oficial';
    botaoSalvar.setAttribute('data-bs-toggle', 'tooltip');
    botaoSalvar.setAttribute('data-bs-placement', 'top');
    botaoSalvar.setAttribute('title', 'Salva este relatório como um registo oficial de ocorrência.');

    botaoSalvar.addEventListener('click', () => {
        // Guarda os dados na memória do navegador para a próxima página
        localStorage.setItem('novoLogRondaBruto', logBruto);
        localStorage.setItem('novoRelatorioProcessado', relatorioProcessado);
        
        // Redireciona para o novo formulário unificado que criamos
        window.location.href = '/ronda/ocorrencia/registrar_direto';
    });

    containerBotoes.prepend(botaoSalvar); // Adiciona como o primeiro botão na área de resultados

    // Inicializa o tooltip para o novo botão
    new bootstrap.Tooltip(botaoSalvar);
}


document.addEventListener('DOMContentLoaded', function () {
    function init() {
        if (!DOMElements.relatorioBruto || !DOMElements.btnProcessar || !DOMElements.resultadoProcessamento || !DOMElements.statusProcessamento) {
            console.error("index_page/main.js: Um ou mais elementos DOM essenciais não foram encontrados.");
            if(DOMElements.btnProcessar) DOMElements.btnProcessar.disabled = true;
            return;
        }

        // Define o HTML inicial dos botões a partir do CONFIG
        if (DOMElements.btnProcessar && CONFIG.initialProcessButtonHTML) {
            DOMElements.btnProcessar.innerHTML = CONFIG.initialProcessButtonHTML;
            DOMElements.btnProcessar.dataset.originalHTML = DOMElements.btnProcessar.innerHTML;
        }
        if (DOMElements.btnCopiar && CONFIG.initialCopyButtonHTML) {
            DOMElements.btnCopiar.innerHTML = CONFIG.initialCopyButtonHTML;
            DOMElements.btnCopiar.dataset.originalHTML = DOMElements.btnCopiar.innerHTML;
        }
        if (DOMElements.btnCopiarEmail && CONFIG.initialCopyEmailButtonHTML) {
            DOMElements.btnCopiarEmail.innerHTML = CONFIG.initialCopyEmailButtonHTML;
            DOMElements.btnCopiarEmail.dataset.originalHTML = DOMElements.btnCopiarEmail.innerHTML;
        }
        if (DOMElements.btnLimpar && CONFIG.initialClearButtonHTML) {
             DOMElements.btnLimpar.innerHTML = CONFIG.initialClearButtonHTML;
        }
        
        if (DOMElements.relatorioBruto) {
            DOMElements.relatorioBruto.addEventListener('input', updateCharCount);
            updateCharCount();
        }

        // --- ALTERAÇÃO PRINCIPAL ---
        // Modificamos o event listener para chamar a nova função após o sucesso.
        if(DOMElements.btnProcessar) {
            DOMElements.btnProcessar.addEventListener('click', async () => {
                // handleProcessReport já mostra o spinner e trata dos status.
                // Assumimos que ele retorna 'true' em caso de sucesso.
                const sucesso = await handleProcessReport(); 

                if (sucesso) {
                    // Se o processamento foi bem-sucedido, pegamos os textos
                    const relatorioBrutoOriginal = DOMElements.relatorioBruto.value;
                    const relatorioProcessadoFinal = DOMElements.resultadoProcessamento.value;
                    
                    // E chamamos nossa nova função para exibir o botão de registro
                    exibirBotaoRegistrarOcorrencia(relatorioBrutoOriginal, relatorioProcessadoFinal);
                }
            });
        }
        
        if (DOMElements.btnCopiar) {
            DOMElements.btnCopiar.addEventListener('click', () => handleCopyResult('standard'));
            DOMElements.btnCopiar.style.display = 'none';
        }
        
        if (DOMElements.btnCopiarEmail) {
            DOMElements.btnCopiarEmail.addEventListener('click', () => handleCopyResult('email'));
            DOMElements.btnCopiarEmail.style.display = 'none';
        }
        
        if (DOMElements.btnEnviarWhatsAppResultado) {
            DOMElements.btnEnviarWhatsAppResultado.addEventListener('click', () => handleSendToWhatsApp('standard'));
            DOMElements.btnEnviarWhatsAppResultado.style.display = 'none'; 
        }
        
        if (DOMElements.btnEnviarWhatsAppEmail) {
            DOMElements.btnEnviarWhatsAppEmail.addEventListener('click', () => handleSendToWhatsApp('email'));
            DOMElements.btnEnviarWhatsAppEmail.style.display = 'none'; 
        }

        if (DOMElements.btnLimpar) {
            DOMElements.btnLimpar.addEventListener('click', handleClearFields);
        }

        if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'none';

        if(DOMElements.formatarParaEmailCheckbox && DOMElements.colunaRelatorioEmail){
            DOMElements.formatarParaEmailCheckbox.addEventListener('change', function(){
                const showEmailColumn = this.checked;
                DOMElements.colunaRelatorioEmail.style.display = showEmailColumn ? 'block' : 'none';
                if (!showEmailColumn) { // Limpa e esconde se desmarcado
                    if(DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = '';
                    if(DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email'); 
                    if(DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
                    if(DOMElements.btnEnviarWhatsAppEmail) DOMElements.btnEnviarWhatsAppEmail.style.display = 'none';
                }
            });
        }
        console.log("index_page/main.js: Inicialização concluída.");
    }
    init();
});
