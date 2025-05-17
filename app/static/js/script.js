document.addEventListener('DOMContentLoaded', function () {
    const btnProcessar = document.getElementById('btnProcessar');
    const relatorioBrutoEl = document.getElementById('relatorioBruto');
    const outputDiv = document.getElementById('output');
    const errorDiv = document.getElementById('errorDisplay');
    const spinner = document.getElementById('spinner');
    const btnCopiar = document.getElementById('btnCopiar');

    const MAX_INPUT_LENGTH = 10000; // Limite de caracteres no frontend

    function displayError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = message ? 'block' : 'none';
    }

    function displayOutput(message) {
        outputDiv.textContent = message;
    }

    if (btnProcessar) {
        btnProcessar.addEventListener('click', async function () {
            const relatorioBruto = relatorioBrutoEl.value;

            displayOutput(''); // Limpa saída anterior
            displayError(''); // Limpa erro anterior
            btnCopiar.style.display = 'none'; // Esconde o botão de copiar
            
            if (!relatorioBruto.trim()) {
                displayError("Por favor, insira o relatório bruto.");
                relatorioBrutoEl.focus();
                return;
            }

            if (relatorioBruto.length > MAX_INPUT_LENGTH) {
                displayError(`O relatório é muito longo. Máximo de ${MAX_INPUT_LENGTH} caracteres permitidos. Você digitou ${relatorioBruto.length}.`);
                relatorioBrutoEl.focus();
                return;
            }
            
            spinner.style.display = 'block';
            btnProcessar.disabled = true;
            btnProcessar.textContent = 'Processando...';

            try {
                const response = await fetch('/processar_relatorio', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ relatorio_bruto: relatorioBruto }),
                });

                const data = await response.json(); 

                if (!response.ok) {
                    throw new Error(data.erro || `Erro do servidor: ${response.status} - ${response.statusText}`);
                }

                if (data.relatorio_processado) {
                    displayOutput(data.relatorio_processado);
                    if(data.relatorio_processado.trim() !== "") { 
                        btnCopiar.style.display = 'block';
                    }
                } else if (data.erro) { 
                     displayError('Erro ao processar: ' + data.erro);
                } else {
                     displayError('Resposta inesperada do servidor.');
                }
            } catch (error) {
                console.error('Erro no script.js ao processar:', error);
                displayError('Falha na comunicação ou processamento: ' + error.message);
            } finally { 
                spinner.style.display = 'none';
                btnProcessar.disabled = false;
                btnProcessar.textContent = 'Processar Relatório';
            }
        });
    } else {
        console.error("Elemento 'btnProcessar' não encontrado no DOM.");
    }

    if (btnCopiar) {
        btnCopiar.addEventListener('click', function() {
            const textoParaCopiar = outputDiv.textContent;
            if (!textoParaCopiar) return;

            if (navigator.clipboard) {
                navigator.clipboard.writeText(textoParaCopiar)
                    .then(() => {
                        const originalText = btnCopiar.textContent;
                        btnCopiar.textContent = 'Copiado!';
                        btnCopiar.disabled = true;
                        setTimeout(() => {
                            btnCopiar.textContent = originalText;
                            btnCopiar.disabled = false;
                        }, 2000);
                    })
                    .catch(err => {
                        console.error('Falha ao copiar texto com navigator.clipboard: ', err);
                        // Tenta fallback se o erro não for por falta de suporte (ex: permissão negada)
                        tryFallbackCopy(textoParaCopiar);
                    });
            } else {
                tryFallbackCopy(textoParaCopiar);
            }
        });
    } else {
        console.error("Elemento 'btnCopiar' não encontrado no DOM.");
    }

    function tryFallbackCopy(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed"; // Evita rolagem
        textArea.style.opacity = "0"; // Torna invisível
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                const originalText = btnCopiar.textContent; // Assume que btnCopiar está no escopo se chamado
                btnCopiar.textContent = 'Copiado!';
                btnCopiar.disabled = true;
                setTimeout(() => {
                    btnCopiar.textContent = originalText;
                    btnCopiar.disabled = false;
                }, 2000);
            } else {
                 throw new Error('document.execCommand("copy") não teve sucesso.');
            }
        } catch (err) {
            console.error('Falha ao copiar texto com fallback (execCommand): ', err);
            alert('Não foi possível copiar o texto. Por favor, copie manualmente.');
        }
        document.body.removeChild(textArea);
    }
});