document.addEventListener('DOMContentLoaded', function () {
    const btnProcessar = document.getElementById('btnProcessar');
    const relatorioBrutoEl = document.getElementById('relatorioBruto');
    const outputDiv = document.getElementById('output');
    const errorDiv = document.getElementById('errorDisplay');
    const spinner = document.getElementById('spinner');

    if (btnProcessar) {
        btnProcessar.addEventListener('click', async function () {
            const relatorioBruto = relatorioBrutoEl.value;

            outputDiv.textContent = ''; // Limpa saída anterior
            errorDiv.textContent = ''; // Limpa erro anterior

            if (!relatorioBruto.trim()) {
                errorDiv.textContent = "Por favor, insira o relatório bruto.";
                return;
            }

            spinner.style.display = 'block'; // Mostra spinner

            try {
                const response = await fetch('/processar_relatorio', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ relatorio_bruto: relatorioBruto }),
                });

                spinner.style.display = 'none'; // Esconde spinner
                const data = await response.json(); // Tenta parsear JSON mesmo se não for ok

                if (!response.ok) {
                    // Se data.erro existir, usa, senão uma mensagem genérica.
                    throw new Error(data.erro || `Erro do servidor: ${response.status}`);
                }

                if (data.relatorio_processado) {
                    outputDiv.textContent = data.relatorio_processado;
                } else if (data.erro) { // Caso o servidor retorne um erro JSON conhecido mesmo com status 200 (improvável aqui)
                     errorDiv.textContent = 'Erro ao processar: ' + data.erro;
                }
            } catch (error) {
                spinner.style.display = 'none'; // Esconde spinner em caso de erro de rede/parse
                console.error('Erro no script.js:', error); // Loga o erro no console do navegador
                errorDiv.textContent = 'Falha: ' + error.message;
            }
        });
    } else {
        console.error("Botão 'btnProcessar' não encontrado.");
    }
});