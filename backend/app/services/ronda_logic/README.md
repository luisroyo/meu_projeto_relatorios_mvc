# Módulo `ronda_logic`

## Visão Geral
O módulo `ronda_logic` é responsável pelo processamento, análise e formatação de logs de rondas de segurança, extraindo eventos relevantes, pareando inícios e términos de rondas, e gerando relatórios detalhados. Ele foi projetado para ser robusto, modular e facilmente extensível, atendendo a diferentes formatos de entrada e cenários operacionais.

---

## Estrutura dos Arquivos

- **`__init__.py`**  
  Exposição da interface principal do módulo.
- **`config.py`**  
  Centraliza expressões regulares e constantes utilizadas em todo o processamento.
- **`processor.py`**  
  Orquestra o fluxo principal de processamento dos logs, desde a leitura até a geração do relatório.
- **`parser.py`**  
  Responsável por extrair e normalizar eventos a partir das linhas dos logs, aplicando regras e heurísticas para diferentes formatos.
- **`processing.py`**  
  Realiza o pareamento dos eventos de início e término de rondas, calcula durações e gera alertas para inconsistências.
- **`report.py`**  
  Formata os dados processados em relatórios textuais claros e informativos.
- **`utils.py`**  
  Funções utilitárias para normalização de datas, horas e outros dados.

---

## Fluxo de Processamento

1. **Entrada de Dados**
   - Recebe um log bruto de rondas (texto), nome do condomínio, data e escala do plantão.
2. **Parsing e Extração**
   - O parser identifica prefixos, datas, horários, VTRs e eventos relevantes em cada linha do log.
3. **Normalização**
   - Datas e horários são convertidos para formatos padronizados, aceitando variações comuns (ex: `06h30`, `6:30`, `18;00`, etc).
4. **Pareamento de Eventos**
   - Eventos de início e término de rondas são pareados por VTR, considerando cruzamento de dias e inconsistências.
5. **Geração de Relatório**
   - O relatório final apresenta as rondas completas, alertas de inconsistências e um resumo do plantão.

---

## Principais Funções e Responsabilidades

### `processar_log_de_rondas`
```python
def processar_log_de_rondas(
    log_bruto_rondas_str: str,
    nome_condominio_str: str,
    data_plantao_manual_str: str = None,
    escala_plantao_str: str = None,
) -> Tuple[str, int, List[dict], List[str], int]
```
- **Descrição:** Função principal para processar o log de rondas.
- **Parâmetros:**
  - `log_bruto_rondas_str`: Log bruto em texto.
  - `nome_condominio_str`: Nome do condomínio.
  - `data_plantao_manual_str`: Data do plantão (opcional).
  - `escala_plantao_str`: Escala do plantão (opcional, ex: "06-18").
- **Retorno:**  
  - Relatório formatado (str)
  - Total de rondas completas (int)
  - Lista de eventos encontrados (list)
  - Lista de alertas/observações (list)
  - Soma total das durações das rondas em minutos (int)

---

### Outras Funções Importantes

- **`calcular_intervalo_plantao`**
  - Calcula o intervalo de início e fim do plantão a partir da data e escala informadas, considerando cruzamento de dias.

- **`parse_linha_log_prefixo`**
  - Extrai hora, data, VTR e mensagem de uma linha de log, aplicando regex robustas.

- **`extrair_eventos_de_bloco` / `extrair_eventos_de_mensagem_simples`**
  - Identificam eventos de início/término de ronda em blocos ou linhas isoladas.

- **`parear_eventos_ronda`**
  - Pareia eventos de início e término, calcula duração e gera alertas para inconsistências.

- **`formatar_relatorio_rondas`**
  - Gera o relatório textual final, apresentando as rondas, alertas e resumo do plantão.

- **Funções utilitárias**
  - `normalizar_data_capturada`, `normalizar_hora_capturada`: Garantem padronização dos dados extraídos.

---

## Exemplo de Uso

```python
from app.services.ronda_logic import processar_log_de_rondas

log = """
[19:41, 15/07/2024] VTR 01: Início de ronda
[20:10, 15/07/2024] VTR 01: Término de ronda
"""
relatorio, total, eventos, alertas, duracao = processar_log_de_rondas(
    log, "Residencial Exemplo", "15/07/2024", "06-18"
)
print(relatorio)
```

---

## Pontos de Extensão

- **Novos padrões de eventos:** Basta adicionar novas regex em `config.py`.
- **Novos formatos de relatório:** Implemente funções adicionais em `report.py`.
- **Validações customizadas:** Adicione regras em `processor.py` ou `processing.py`.

---

## Boas Práticas
- Mantenha as funções puras e bem testadas.
- Centralize configurações e regex em `config.py`.
- Use logging para facilitar o diagnóstico de problemas.
- Escreva testes unitários para cada função crítica.

---

## Contato
Dúvidas ou sugestões? Entre em contato com o time de desenvolvimento. 