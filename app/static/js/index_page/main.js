// app/static/js/index_page/main.js
import { CONFIG, DOMElements } from './config.js';
import { updateCharCount, displayStatus } from './uiHandlers.js'; // Apenas as que são diretamente chamadas aqui
import { handleProcessReport, handleClearFields, handleCopyResult } from './reportLogic.js';

document.addEventListener('DOMContentLoaded', function () {
    function init() {
        if (!DOMElements.relatorioBruto || !DOMElements.btnProcessar || !DOMElements.resultadoProcessamento || !DOMElements.statusProcessamento) {
            console.error("index_page/main.js: Um ou mais elementos DOM essenciais não foram encontrados.");
            if(DOMElements.btnProcessar) DOMElements.btnProcessar.disabled = true;
            return;
        }

        // Define o HTML inicial dos botões a partir do CONFIG
        // e salva esse HTML no dataset para restauração posterior.
        if (DOMElements.btnProcessar) {
            DOMElements.btnProcessar.innerHTML = CONFIG.initialProcessButtonHTML || 'Processar Relatório';
            DOMElements.btnProcessar.dataset.originalHTML = DOMElements.btnProcessar.innerHTML;
        }
        if (DOMElements.btnCopiar) {
            DOMElements.btnCopiar.innerHTML = CONFIG.initialCopyButtonHTML || 'Copiar Padrão';
            DOMElements.btnCopiar.dataset.originalHTML = DOMElements.btnCopiar.innerHTML;
        }
        if (DOMElements.btnCopiarEmail) {
            DOMElements.btnCopiarEmail.innerHTML = CONFIG.initialCopyEmailButtonHTML || 'Copiar E-mail';
            DOMElements.btnCopiarEmail.dataset.originalHTML = DOMElements.btnCopiarEmail.innerHTML;
        }
        if (DOMElements.btnLimpar) {
             DOMElements.btnLimpar.innerHTML = CONFIG.initialClearButtonHTML || 'Limpar Tudo';
             DOMElements.btnLimpar.dataset.originalHTML = DOMElements.btnLimpar.innerHTML; // Salvar se for mudar dinamicamente
        }

        if (DOMElements.relatorioBruto) {
            DOMElements.relatorioBruto.addEventListener('input', updateCharCount);
            updateCharCount();
        }

        if(DOMElements.btnProcessar) DOMElements.btnProcessar.addEventListener('click', handleProcessReport);
        
        if (DOMElements.btnCopiar) {
            DOMElements.btnCopiar.addEventListener('click', () => handleCopyResult('standard'));
            DOMElements.btnCopiar.style.display = 'none';
        }
        
        if (DOMElements.btnCopiarEmail) {
            DOMElements.btnCopiarEmail.addEventListener('click', () => handleCopyResult('email'));
            DOMElements.btnCopiarEmail.style.display = 'none';
        }

        if (DOMElements.btnLimpar) {
            DOMElements.btnLimpar.addEventListener('click', handleClearFields);
        }

        if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'none';

        if(DOMElements.formatarParaEmailCheckbox && DOMElements.colunaRelatorioEmail){
            DOMElements.formatarParaEmailCheckbox.addEventListener('change', function(){
                if (!this.checked) {
                    if(DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = '';
                    // Passando DOMElements explicitamente para displayStatus se ela não tiver acesso global a ele
                    if(DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email'); 
                    if(DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
                    DOMElements.colunaRelatorioEmail.style.display = 'none';
                } else {
                     DOMElements.colunaRelatorioEmail.style.display = 'block';
                }
            });
        }
        console.log("index_page/main.js: Inicialização concluída.");
    }
    init();
});