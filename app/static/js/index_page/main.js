// app/static/js/index_page/main.js
import { CONFIG, DOMElements } from './config.js';
import { updateCharCount, displayStatus } from './uiHandlers.js';
// Importe a nova função de reportLogic.js
import { handleProcessReport, handleClearFields, handleCopyResult, handleSendToWhatsApp } from './reportLogic.js';

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
        // Para botões de WhatsApp, o HTML já está no template, mas você pode padronizar se quiser:
        if (DOMElements.btnEnviarWhatsAppResultado && CONFIG.initialWhatsAppButtonHTML) {
             // DOMElements.btnEnviarWhatsAppResultado.innerHTML = CONFIG.initialWhatsAppButtonHTML;
        }
        if (DOMElements.btnEnviarWhatsAppEmail && CONFIG.initialWhatsAppEmailButtonHTML) {
            // DOMElements.btnEnviarWhatsAppEmail.innerHTML = CONFIG.initialWhatsAppEmailButtonHTML;
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
        
        // NOVOS EVENT LISTENERS
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