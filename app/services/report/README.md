# Módulo `report`

## Visão Geral
O módulo `report` é responsável pela geração de relatórios PDF profissionais para rondas de segurança e ocorrências, utilizando o ReportLab. Ele centraliza a lógica de construção, estilização e organização dos relatórios, garantindo padronização visual, clareza das informações e flexibilidade para diferentes tipos de relatório.

---

## Estrutura dos Arquivos

- **`__init__.py`**  
  Exposição dos principais serviços de relatório do módulo.
- **`builder.py`**  
  Responsável pela construção do PDF, montagem de páginas, cabeçalhos, rodapés, tabelas, KPIs e elementos visuais.
- **`styles.py`**  
  Centraliza estilos, paletas de cores, fontes e padrões visuais utilizados nos relatórios.
- **`ronda_service.py`**  
  Serviço especializado na geração de relatórios de rondas de segurança, incluindo análise, KPIs, tabelas e gráficos.
- **`ocorrencia_service.py`**  
  Serviço especializado na geração de relatórios de ocorrências, com seções detalhadas, agrupamentos e destaques.

---

## Fluxo de Geração de Relatório

1. **Recebimento dos Dados**
   - Os serviços recebem dados processados (rondas, ocorrências, métricas, etc.) e parâmetros de filtro.
2. **Construção do Relatório**
   - O `builder.py` monta o PDF, aplicando estilos, cabeçalhos, rodapés, tabelas, gráficos e KPIs.
3. **Estilização**
   - O `styles.py` define cores, fontes, espaçamentos e padrões visuais, garantindo identidade visual consistente.
4. **Exportação**
   - O relatório é exportado em PDF, pronto para download ou envio.

---

## Principais Funções e Responsabilidades

### `ronda_service.py`
- **`gerar_relatorio_ronda_pdf`**
  - Gera o relatório PDF de rondas, incluindo KPIs, tabelas, análises por turno, ranking de supervisores, comparativos e resumo executivo.

### `ocorrencia_service.py`
- **`gerar_relatorio_ocorrencia_pdf`**
  - Gera o relatório PDF de ocorrências, com agrupamentos, destaques, tabelas e análises detalhadas.

### `builder.py`
- **`ReportBuilder`**
  - Classe principal para construção do PDF, com métodos para adicionar páginas, cabeçalhos, rodapés, tabelas, gráficos, barras de progresso e KPIs.

### `styles.py`
- **Paleta de cores, fontes e estilos**
  - Define padrões visuais, garantindo relatórios modernos, legíveis e alinhados à identidade visual da Associação Master.

---

## Exemplo de Uso

```python
from app.services.report.ronda_service import gerar_relatorio_ronda_pdf

dados = {...}  # Dados processados das rondas
buffer_pdf = gerar_relatorio_ronda_pdf(dados, filtros={...})
with open('relatorio_ronda.pdf', 'wb') as f:
    f.write(buffer_pdf.getvalue())
```

---

## Pontos de Extensão

- **Novos tipos de relatório:** Implemente novos serviços seguindo o padrão de `ronda_service.py` e `ocorrencia_service.py`.
- **Novos estilos ou temas:** Adicione ou altere estilos em `styles.py`.
- **Elementos visuais customizados:** Expanda o `builder.py` para novos tipos de gráficos, tabelas ou componentes visuais.

---

## Boas Práticas
- Centralize estilos e padrões visuais em `styles.py`.
- Mantenha a lógica de construção de PDF isolada em `builder.py`.
- Separe serviços por tipo de relatório para facilitar manutenção e evolução.
- Escreva testes para garantir a integridade dos PDFs gerados.

---

## Contato
Dúvidas ou sugestões? Entre em contato com o time de desenvolvimento. 