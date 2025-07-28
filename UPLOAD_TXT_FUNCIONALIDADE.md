# Funcionalidade de Upload de Arquivo TXT para Correção de Rondas

## Visão Geral

Foi implementada uma nova funcionalidade que permite fazer upload de arquivos TXT contendo logs de rondas e analisar automaticamente as datas e horários, permitindo selecionar apenas os registros específicos que você deseja processar. **O sistema é inteligente e reconhece automaticamente plantões que cruzam a meia-noite.**

## Como Usar

### 1. Acesse a Página de Correção de Rondas
- Vá para `/rondas/registrar`
- Você verá uma nova seção "UPLOAD DE ARQUIVO TXT"

### 2. Configure a Data e Escala do Plantão
- **IMPORTANTE**: Configure primeiro a **Data do Plantão** e **Escala do Plantão**
- O sistema usa essas informações para filtrar automaticamente os registros corretos

### 3. Faça Upload do Arquivo
- **Arraste e solte** um arquivo TXT na área demarcada, ou
- **Clique na área** para selecionar um arquivo do seu computador
- Apenas arquivos `.txt` são aceitos

### 4. Análise Automática Inteligente
Após o upload, o sistema irá:
- Analisar automaticamente o arquivo
- **Calcular o intervalo correto do plantão** (considerando cruzamento de meia-noite)
- Extrair todas as datas e horários encontrados
- **Filtrar apenas os registros dentro do plantão**
- Identificar eventos de ronda (início, término, etc.)
- Mostrar estatísticas do arquivo

### 5. Seleção de Linhas
- **Visualize** todas as linhas com datas encontradas
- **Linhas dentro do plantão** são destacadas com badge verde "No Plantão"
- **Clique** nas linhas que deseja incluir no processamento
- Use os botões "Selecionar Todos" ou "Limpar Seleção" para facilitar
- Linhas com eventos de ronda são destacadas com uma borda azul

### 6. Extrair Conteúdo Selecionado
- Clique em "Usar Linhas Selecionadas"
- O conteúdo selecionado será automaticamente inserido no campo "Log Bruto das Rondas"
- Continue com o processamento normal da ronda

## 🌙 Tratamento Inteligente de Plantões Noturnos

### Plantão Diurno (06h às 18h)
- **Mesmo dia**: 25/07/2025 06:00 → 25/07/2025 18:00
- Todos os registros ficam na mesma data

### Plantão Noturno (18h às 06h) ⭐ **NOVO**
- **Cruza meia-noite**: 25/07/2025 18:00 → 26/07/2025 06:00
- O sistema automaticamente:
  - Reconhece que o plantão cruza a meia-noite
  - Filtra registros de **25/07/2025** (18h-23h59)
  - Filtra registros de **26/07/2025** (00h-06h)
  - Mostra indicador visual "Plantão cruza meia-noite"

### Exemplo Prático
Se você selecionar:
- **Data**: 25/07/2025
- **Escala**: 18h às 06h

O sistema irá automaticamente incluir:
- ✅ Registros de 25/07/2025 das 18:00 às 23:59
- ✅ Registros de 26/07/2025 das 00:00 às 06:00
- ❌ Registros fora desse intervalo

## Formatos Suportados

O sistema reconhece os seguintes formatos de data/hora:

```
[HH:MM, DD/MM/YYYY] - Formato mais comum
[HH:MM DD/MM/YYYY] - Sem vírgula
DD/MM/YYYY HH:MM - Formato alternativo
HH:MM DD/MM/YYYY - Formato alternativo
[HH:MM] DD/MM/YYYY - Colchetes apenas no horário
DD/MM/YYYY HH:MM - VTR XX: HH:MM - Formato WhatsApp ⭐ NOVO
```

### Formato WhatsApp ⭐ **NOVO**

O sistema agora suporta arquivos de conversa do WhatsApp com o formato:
```
25/07/2025 18:00 - VTR 01: 18:00 Início de ronda
25/07/2025 18:30 - VTR 01: 18:30 termino de ronda
26/07/2025 00:00 - VTR 02: 00:00 Início de ronda
26/07/2025 00:30 - VTR 02: 00:30 termino de ronda
```

**Características:**
- ✅ Reconhece automaticamente o formato do WhatsApp
- ✅ Extrai a data da mensagem e o horário da ronda
- ✅ Identifica eventos de início e término de ronda
- ✅ Suporta plantões que cruzam meia-noite
- ✅ Filtra automaticamente por intervalo do plantão

## Palavras-chave Reconhecidas

O sistema identifica automaticamente eventos de ronda baseado em palavras-chave:
- **Início**: início, inicio, start, começo, comeco
- **Término**: término, termino, fim, end, final
- **Ronda**: ronda, patrulha, vigilância, vigilancia

## Exemplos de Arquivos

### Plantão Diurno (exemplo_arquivo_ronda.txt)
```
[06:30, 15/01/2024] VTR 01: Início ronda 06:30
[07:00, 15/01/2024] VTR 01: Término ronda 07:00
[08:00, 15/01/2024] VTR 02: Início ronda 08:00
[08:30, 15/01/2024] VTR 02: Término ronda 08:30
```

### Plantão Noturno (exemplo_plantao_noturno.txt) ⭐ **NOVO**
```
[18:00, 25/07/2025] VTR 01: Início plantão noturno 18:00
[23:30, 25/07/2025] VTR 02: Término ronda 23:30
[00:00, 26/07/2025] VTR 01: Início ronda 00:00
[06:00, 26/07/2025] VTR 01: Término plantão noturno 06:00
```

### Formato WhatsApp (exemplo_whatsapp.txt) ⭐ **NOVO**
```
25/07/2025 18:00 - VTR 01: 18:00 Início de ronda
25/07/2025 18:30 - VTR 01: 18:30 termino de ronda
25/07/2025 23:30 - VTR 02: 23:30 termino de ronda
26/07/2025 00:00 - VTR 01: 00:00 Início de ronda
26/07/2025 06:00 - VTR 01: 06:00 termino de plantão
```

## Benefícios

1. **Automatização**: Não precisa copiar e colar manualmente
2. **Precisão**: Análise automática de datas e horários
3. **Inteligência**: **Reconhece automaticamente plantões que cruzam meia-noite**
4. **Flexibilidade**: Selecione apenas as linhas que precisa
5. **Eficiência**: Processamento mais rápido e sem erros
6. **Organização**: Visualização clara de todos os eventos
7. **Filtragem Inteligente**: Mostra apenas registros relevantes ao plantão

## Funcionalidades Técnicas

### Backend
- **TXTAnalyzer**: Classe responsável pela análise de arquivos
- **Cálculo de Intervalo**: Função que calcula corretamente plantões noturnos
- **Filtragem Inteligente**: Filtra registros dentro do intervalo do plantão
- **Rotas**: `/rondas/analisar-arquivo` e `/rondas/extrair-linhas-selecionadas`
- **Validação**: Verificação de formato de arquivo e encoding

### Frontend
- **Drag & Drop**: Interface intuitiva para upload
- **Análise em Tempo Real**: Resultados imediatos após upload
- **Indicadores Visuais**: Badges para "No Plantão" e "Plantão cruza meia-noite"
- **Seleção Interativa**: Interface visual para escolher linhas
- **Feedback Visual**: Indicadores visuais para eventos de ronda

## Tratamento de Erros

- **Arquivo inválido**: Apenas arquivos .txt são aceitos
- **Encoding**: Suporte para UTF-8 e Latin-1
- **Formato**: Mensagens claras para formatos não reconhecidos
- **Rede**: Tratamento de erros de comunicação
- **Plantão**: Validação de formato de escala (ex: "18h às 06h")

## Compatibilidade

- **Navegadores**: Chrome, Firefox, Safari, Edge (modernos)
- **Tamanho**: Sem limite específico (limitado pelo servidor)
- **Encoding**: UTF-8 (preferencial) e Latin-1 (fallback)
- **Plantões**: Diurnos (06h-18h) e Noturnos (18h-06h)

## Dicas de Uso

1. **Configure sempre** a data e escala do plantão antes do upload
2. **Use o arquivo de exemplo** `exemplo_plantao_noturno.txt` para testar plantões noturnos
3. **Observe os badges** "No Plantão" para ver quais registros são relevantes
4. **Verifique o indicador** "Plantão cruza meia-noite" para confirmar o tipo de plantão
5. **Selecione apenas** as linhas que realmente pertencem ao seu plantão 