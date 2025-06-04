// app/static/js/index_page/main.js
import { CONFIG, DOMElements } from './config.js'; // DOMElements será populado em config.js
import { updateCharCount, displayStatus } from './uiHandlers.js';
import { handleProcessReport, handleClearFields, handleCopyResult } from './reportLogic.js';

document.addEventListener('DOMContentLoaded', function () {
    function init() {
        // Verifica se os elementos essenciais da página existem
        if (!DOMElements.relatorioBruto || !DOMElements.btnProcessar || !DOMElements.resultadoProcessamento || !DOMElements.statusProcessamento) {
            console.error("index_page/main.js: Um ou mais elementos DOM essenciais não foram encontrados. Funcionalidades podem estar desabilitadas.");
            if(DOMElements.btnProcessar) DOMElements.btnProcessar.disabled = true;
            return;
        }

        // Salvar HTML original dos botões para restauração
        if (DOMElements.btnProcessar && !DOMElements.btnProcessar.dataset.originalHTML) {
            DOMElements.btnProcessar.dataset.originalHTML = DOMElements.btnProcessar.innerHTML;
        }
        if (DOMElements.btnCopiar && !DOMElements.btnCopiar.dataset.originalHTML) {
             DOMElements.btnCopiar.dataset.originalHTML = DOMElements.btnCopiar.innerHTML || CONFIG.initialCopyButtonText;
        }
        if (DOMElements.btnCopiarEmail && !DOMElements.btnCopiarEmail.dataset.originalHTML) {
             DOMElements.btnCopiarEmail.dataset.originalHTML = DOMElements.btnCopiarEmail.innerHTML || CONFIG.initialCopyEmailButtonText;
        }


        if (DOMElements.relatorioBruto) {
            DOMElements.relatorioBruto.addEventListener('input', updateCharCount);
            updateCharCount(); // Chamada inicial
        }

        if(DOMElements.btnProcessar) DOMElements.btnProcessar.addEventListener('click', handleProcessReport);
        
        if (DOMElements.btnCopiar) {
            DOMElements.btnCopiar.addEventListener('click', () => handleCopyResult('standard'));
            DOMElements.btnCopiar.style.display = 'none'; // Estado inicial
        }
        
        if (DOMElements.btnCopiarEmail) {
            DOMElements.btnCopiarEmail.addEventListener('click', () => handleCopyResult('email'));
            DOMElements.btnCopiarEmail.style.display = 'none'; // Estado inicial
        }

        if (DOMElements.btnLimpar) {
            DOMElements.btnLimpar.addEventListener('click', handleClearFields);
        }

        if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'none'; // Estado inicial

        if(DOMElements.formatarParaEmailCheckbox && DOMElements.colunaRelatorioEmail){
            DOMElements.formatarParaEmailCheckbox.addEventListener('change', function(){
                if (!this.checked) { // Se desmarcado, limpa e esconde
                    if(DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = '';
                    if(DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email');
                    if(DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
                    DOMElements.colunaRelatorioEmail.style.display = 'none';
                } else { // Se marcado, apenas mostra a coluna (resetOutputUI em handleProcessReport cuidará da limpeza se necessário)
                     DOMElements.colunaRelatorioEmail.style.display = 'block';
                }
            });
        }
        console.log("index_page/main.js: Inicialização concluída e listeners adicionados.");
    }

    init();
});