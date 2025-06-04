// app/static/js/index_page/main.js
// (Conteúdo como fornecido na resposta anterior, já está correto para usar o CONFIG)
import { CONFIG, DOMElements } from './config.js';
import { updateCharCount, displayStatus } from './uiHandlers.js';
import { handleProcessReport, handleClearFields, handleCopyResult } from './reportLogic.js';

document.addEventListener('DOMContentLoaded', function () {
    function init() {
        if (!DOMElements.relatorioBruto || !DOMElements.btnProcessar || !DOMElements.resultadoProcessamento || !DOMElements.statusProcessamento) {
            console.error("index_page/main.js: Um ou mais elementos DOM essenciais não foram encontrados.");
            if(DOMElements.btnProcessar) DOMElements.btnProcessar.disabled = true;
            return;
        }

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
             DOMElements.btnLimpar.dataset.originalHTML = DOMElements.btnLimpar.innerHTML;
        }

        if (DOMElements.relatorioBruto) {
            DOMElements.relatorioBruto.addEventListener('input', updateCharCount);
            updateCharCount();
        }

        if(DOMElements.btnProcessar) DOMElements.btnProcessar.addEventListener('click', handleProcessReport);
        if (DOMElements.btnCopiar) DOMElements.btnCopiar.addEventListener('click', () => handleCopyResult('standard'));
        if (DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.addEventListener('click', () => handleCopyResult('email'));
        if (DOMElements.btnLimpar) DOMElements.btnLimpar.addEventListener('click', handleClearFields);

        if (DOMElements.colunaRelatorioEmail) DOMElements.colunaRelatorioEmail.style.display = 'none';
        if(DOMElements.formatarParaEmailCheckbox && DOMElements.colunaRelatorioEmail){
            DOMElements.formatarParaEmailCheckbox.addEventListener('change', function(){
                if (!this.checked) {
                    if(DOMElements.resultadoEmail) DOMElements.resultadoEmail.value = '';
                    if(DOMElements.statusProcessamentoEmail) displayStatus('', 'info', 'email');
                    if(DOMElements.btnCopiarEmail) DOMElements.btnCopiarEmail.style.display = 'none';
                    DOMElements.colunaRelatorioEmail.style.display = 'none';
                } else {
                     DOMElements.colunaRelatorioEmail.style.display = 'block';
                }
            });
        }
        console.log("index_page/main.js: Inicialização concluída e listeners adicionados com textos/icones dos botões definidos via config.");
    }
    init();
});