document.addEventListener('DOMContentLoaded', function () {
    // IDs do HTML que estamos usando
    const btnProcessar = document.getElementById('processarRelatorio');
    const relatorioBrutoEl = document.getElementById('relatorioBruto');
    const resultadoProcessamentoEl = document.getElementById('resultadoProcessamento'); // Para o resultado (textarea)
    const statusProcessamentoEl = document.getElementById('statusProcessamento');   // Para mensagens de erro/status
    const spinnerEl = document.getElementById('processarSpinner');           // Spinner no botão
    const btnCopiar = document.getElementById('copiarResultado');
    const btnLimpar = document.getElementById('limparCampos');
    const charCountEl = document.getElementById('charCount');

    const MAX_INPUT_LENGTH_FRONTEND = 10000; // Limite no frontend (deve ser <= ao do servidor)
    const MAX_INPUT_LENGTH_SERVER = 12000; // Apenas para referência na mensagem

    function updateCharCount() {
        if (relatorioBrutoEl && charCountEl) {
            const currentLength = relatorioBrutoEl.value.length;
            charCountEl.textContent = `Caracteres: ${currentLength} / ${MAX_INPUT_LENGTH_SERVER}`;
            if (currentLength > MAX_INPUT_LENGTH_FRONTEND) {
                charCountEl.classList.add('text-danger'); // Adiciona cor se exceder limite do frontend
            } else {
                charCountEl.classList.remove('text-danger');
            }
        }
    }

    if (relatorioBrutoEl) {
        relatorioBrutoEl.addEventListener('input', updateCharCount);
        updateCharCount(); // Inicializa a contagem
    }

    function displayStatus(message, type = 'info') { // type pode ser 'info', 'success', 'warning', 'danger'
        if (statusProcessamentoEl) {
            statusProcessamentoEl.textContent = message;
            // Remove classes de alerta anteriores e adiciona a nova
            statusProcessamentoEl.className = 'mb-2 alert'; // Classe base
            if (message) {
                statusProcessamentoEl.classList.add(`alert-${type}`);
                statusProcessamentoEl.style.display = 'block';
            } else {
                statusProcessamentoEl.style.display = 'none';
            }
        }
    }

    if (btnProcessar) {
        btnProcessar.addEventListener('click', async function () {
            const relatorioBrutoValue = relatorioBrutoEl.value;

            resultadoProcessamentoEl.value = ''; // Limpa resultado anterior
            displayStatus('');                // Limpa status/erro anterior
            if(btnCopiar) btnCopiar.style.display = 'none';    // Esconde o botão de copiar
            
            if (!relatorioBrutoValue.trim()) {
                displayStatus("Por favor, insira o relatório bruto.", 'warning');
                relatorioBrutoEl.focus();
                return;
            }

            if (relatorioBrutoValue.length > MAX_INPUT_LENGTH_FRONTEND) {
                displayStatus(`O relatório é muito longo. Máximo de ${MAX_INPUT_LENGTH_FRONTEND} caracteres permitidos no frontend. Você digitou ${relatorioBrutoValue.length}.`, 'danger');
                relatorioBrutoEl.focus();
                return;
            }
            
            if(spinnerEl) spinnerEl.style.display = 'inline-block';
            btnProcessar.disabled = true;
            // Para mudar o texto do botão, é preciso pegar o span ou o nó de texto dentro dele se houver só o spinner.
            // Por simplicidade, vamos assumir que o texto 'Processar Relatório' está fora do spinner no HTML ou não será mudado aqui.
            // Se o texto está junto com o spinner, a lógica de mostrar/esconder o texto e o spinner precisa ser mais granular.

            displayStatus('Processando...', 'info');

            try {
                const response = await fetch('/processar_relatorio', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ relatorio_bruto: relatorioBrutoValue }),
                });

                const data = await response.json(); 

                if (!response.ok) {
                    // Erro HTTP (4xx, 5xx)
                    throw new Error(data.erro || `Erro do servidor: ${response.status}`);
                }

                // Resposta OK (2xx), mas pode conter um erro lógico da aplicação
                if (data.relatorio_processado) {
                    resultadoProcessamentoEl.value = data.relatorio_processado; // Usar .value para textarea
                    displayStatus('Relatório processado com sucesso!', 'success');
                    if(data.relatorio_processado.trim() !== "" && btnCopiar) { 
                        btnCopiar.style.display = 'inline-block'; // Mostra o botão de copiar
                    }
                } else if (data.erro) { 
                     displayStatus('Erro ao processar: ' + data.erro, 'danger');
                } else {
                     displayStatus('Resposta inesperada do servidor.', 'warning');
                }
            } catch (error) {
                console.error('Erro no script.js ao processar:', error);
                displayStatus('Falha na comunicação ou processamento: ' + error.message, 'danger');
            } finally { 
                if(spinnerEl) spinnerEl.style.display = 'none';
                btnProcessar.disabled = false;
                // Restaurar texto do botão se ele foi alterado
            }
        });
    } else {
        console.error("Elemento 'processarRelatorio' (o botão) não encontrado no DOM.");
    }

    if (btnCopiar) {
        btnCopiar.addEventListener('click', function() {
            const textoParaCopiar = resultadoProcessamentoEl.value; // .value para textarea
            if (!textoParaCopiar) return;

            if (navigator.clipboard) {
                navigator.clipboard.writeText(textoParaCopiar)
                    .then(() => {
                        const originalText = btnCopiar.textContent;
                        btnCopiar.innerHTML = '<i class="bi bi-check-lg"></i> Copiado!'; // Exemplo com ícone se usar Bootstrap Icons
                        btnCopiar.disabled = true;
                        setTimeout(() => {
                            btnCopiar.textContent = originalText; //  Precisa ter o texto original guardado ou redefinido
                            btnCopiar.disabled = false;
                        }, 2000);
                    })
                    .catch(err => {
                        console.error('Falha ao copiar texto com navigator.clipboard: ', err);
                        tryFallbackCopy(textoParaCopiar);
                    });
            } else {
                tryFallbackCopy(textoParaCopiar);
            }
        });
    } else {
        console.warn("Elemento 'copiarResultado' (botão copiar) não encontrado no DOM. Isso é normal se não houver resultado ainda.");
    }
    
    if (btnLimpar) {
        btnLimpar.addEventListener('click', function() {
            if(relatorioBrutoEl) relatorioBrutoEl.value = '';
            if(resultadoProcessamentoEl) resultadoProcessamentoEl.value = '';
            displayStatus('');
            if(btnCopiar) btnCopiar.style.display = 'none';
            updateCharCount();
            if(relatorioBrutoEl) relatorioBrutoEl.focus();
        });
    } else {
         console.error("Elemento 'limparCampos' não encontrado no DOM.");
    }

    function tryFallbackCopy(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed"; 
        textArea.style.opacity = "0"; 
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            const successful = document.execCommand('copy');
            if (successful && btnCopiar) { // Checa se btnCopiar existe
                const originalText = "Copiar Resultado"; // Definir o texto original esperado
                btnCopiar.innerHTML = '<i class="bi bi-check-lg"></i> Copiado!';
                btnCopiar.disabled = true;
                setTimeout(() => {
                    btnCopiar.textContent = originalText;
                    btnCopiar.disabled = false;
                }, 2000);
            } else if (!successful) {
                 throw new Error('document.execCommand("copy") não teve sucesso.');
            }
        } catch (err) {
            console.error('Falha ao copiar texto com fallback (execCommand): ', err);
            alert('Não foi possível copiar o texto. Por favor, copie manualmente.');
        }
        document.body.removeChild(textArea);
    }
}); // Fechamento correto do DOMContentLoaded