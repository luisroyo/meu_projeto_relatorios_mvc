# Módulo `dashboard`

## Visão Geral
O módulo `dashboard` é responsável pela análise, agregação e apresentação de dados operacionais de rondas e ocorrências em painéis gerenciais. Ele centraliza a lógica de processamento de métricas, geração de comparativos, dashboards de acompanhamento e suporte a filtros dinâmicos, fornecendo informações estratégicas para a gestão de segurança.

---

## Estrutura dos Arquivos

- **`__init__.py`**  
  Exposição dos principais serviços e dashboards do módulo.
- **`main_dashboard.py`**  
  Lógica do dashboard principal, agregando dados gerais e indicadores-chave.
- **`ronda_dashboard.py`**  
  Processamento e análise de dados de rondas para visualização em dashboards.
- **`ocorrencia_dashboard.py`**  
  Processamento e análise de dados de ocorrências para dashboards.
- **`comparativo_dashboard.py`**  
  Dashboard comparativo, com análise de períodos, ranking, médias e resumos executivos.
- **`comparativo/`**  
  Módulo especializado para lógica de filtros, agregação, métricas e processamento detalhado do dashboard comparativo.
- **`helpers/`**  
  Funções auxiliares e utilitários para manipulação de dados e suporte aos dashboards.

---

## Fluxo de Processamento dos Dashboards

1. **Recebimento dos Dados**
   - Os serviços recebem dados brutos de rondas, ocorrências e parâmetros de filtro.
2. **Aplicação de Filtros**
   - Filtros dinâmicos são aplicados conforme seleção do usuário ou regras de negócio.
3. **Agregação e Cálculo de Métricas**
   - Dados são agregados, métricas calculadas (totais, médias, rankings, comparativos, etc.).
4. **Preparação para Visualização**
   - Os dados processados são organizados em estruturas prontas para exibição em dashboards, gráficos e tabelas.

---

## Principais Funções e Responsabilidades

### `main_dashboard.py`
- Agrega dados gerais, calcula KPIs globais e prepara informações para o painel principal.

### `ronda_dashboard.py`
- Processa logs e registros de rondas, calcula indicadores, distribuições por turno, rankings e tendências.

### `ocorrencia_dashboard.py`
- Analisa ocorrências, classifica por tipo, severidade, local, período e gera resumos executivos.

### `comparativo_dashboard.py` e `comparativo/`
- Realiza análises comparativas entre períodos, gera rankings, médias, resumos e fornece opções de filtros avançados.
- O submódulo `comparativo/` está dividido em:
  - `filters.py`: Lógica de filtros dinâmicos
  - `aggregator.py`: Agregação de dados
  - `metrics.py`: Cálculo de métricas
  - `breakdown.py`: Análise detalhada
  - `processor.py`: Orquestração do processamento

### `helpers/`
- Funções utilitárias para manipulação de datas, formatação, agrupamentos e suporte aos dashboards.

---

## Exemplo de Uso

```python
from app.services.dashboard.ronda_dashboard import gerar_kpis_ronda

dados = {...}  # Dados brutos de rondas
kpis = gerar_kpis_ronda(dados, filtros={...})
print(kpis)
```

---

## Pontos de Extensão

- **Novos dashboards:** Implemente novos arquivos seguindo o padrão dos existentes.
- **Novos filtros ou métricas:** Expanda os arquivos do submódulo `comparativo/`.
- **Novos utilitários:** Adicione funções em `helpers/` para facilitar reuso.

---

## Boas Práticas
- Separe lógica de processamento, agregação e visualização.
- Centralize filtros e métricas em módulos próprios.
- Escreva testes para garantir a consistência dos indicadores.
- Documente funções e parâmetros para facilitar manutenção.

---

## Contato
Dúvidas ou sugestões? Entre em contato com o time de desenvolvimento. 