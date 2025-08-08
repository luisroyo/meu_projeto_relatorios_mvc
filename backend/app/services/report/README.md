# Sistema de Relatórios PDF

Este módulo fornece funcionalidades para geração de relatórios PDF compactos e otimizados.

## Funcionalidades

### Relatórios Padrão
- `generate_ronda_dashboard_pdf()` - Relatório completo de rondas
- `generate_ocorrencia_dashboard_pdf()` - Relatório completo de ocorrências

### Relatórios Compactos (NOVO)
- `generate_compact_ronda_dashboard_pdf()` - Relatório ultra-compacto de rondas
- `generate_compact_ocorrencia_dashboard_pdf()` - Relatório ultra-compacto de ocorrências

## Melhorias Implementadas

### 1. Otimização de Espaçamentos
- **Espaçamentos reduzidos**: De 20pt para 12pt entre seções
- **Margens menores**: De 72pt para 50pt (padrão) e 40pt (compacto)
- **Espaçamentos de títulos**: Reduzidos de 30pt para 15pt

### 2. Tamanhos de Fonte Otimizados
- **Título principal**: 24pt → 20pt
- **Subtítulo**: 16pt → 14pt
- **Cabeçalhos de seção**: 14pt → 12pt
- **Texto de tabelas**: 10pt → 9pt
- **Cabeçalhos de tabela**: 11pt → 10pt

### 3. Layout Compacto
- **Remoção de quebras de página desnecessárias**
- **Tabelas combinadas** em layout mais denso
- **Resumos executivos** integrados
- **Limitação de dados** (ex: top 5 supervisores, top 10 colaboradores)

### 4. Novos Métodos do Builder
- `create_compact_summary_table()` - Combina KPIs e informações do período
- `create_compact_combined_tables()` - Cria múltiplas tabelas em layout compacto

## Como Usar

### Relatório Padrão
```python
from app.services.report.ronda_service import RondaReportService

service = RondaReportService()
pdf_buffer = service.generate_ronda_dashboard_pdf(dashboard_data, filters_info)
```

### Relatório Compacto
```python
from app.services.report.ronda_service import RondaReportService

service = RondaReportService()
pdf_buffer = service.generate_compact_ronda_dashboard_pdf(dashboard_data, filters_info)
```

## Benefícios

1. **Menos páginas**: Redução de ~40-60% no número de páginas
2. **Informações mais concentradas**: Dados importantes em menos espaço
3. **Melhor legibilidade**: Layout mais organizado e denso
4. **Economia de papel**: Ideal para impressão e distribuição
5. **Carregamento mais rápido**: PDFs menores para download

## Estrutura dos Arquivos

```
app/services/report/
├── __init__.py
├── builder.py              # Classe principal para construção de relatórios
├── styles.py               # Estilos e formatação
├── ronda_service.py        # Serviço para relatórios de rondas
├── ocorrencia_service.py   # Serviço para relatórios de ocorrências
└── README.md              # Esta documentação
```

## Configurações de Margem

### Relatórios Padrão
- Margens: 50pt (esquerda/direita), 80pt (topo), 50pt (base)

### Relatórios Compactos
- Margens: 40pt (esquerda/direita), 60pt (topo), 40pt (base)

## Estilos de Tabela

### Tabelas Zebra
- Linhas alternadas com cores diferentes
- Cabeçalhos destacados em azul escuro
- Fonte reduzida para 9pt

### Tabelas de Análise
- Fundo bege para dados
- Alinhamento centralizado
- Bordas em cinza

### Tabelas Compactas
- Espaçamento reduzido entre linhas
- Padding otimizado
- Layout mais denso 