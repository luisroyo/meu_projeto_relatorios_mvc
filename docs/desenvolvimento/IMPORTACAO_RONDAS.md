# 📥 Guia de Importação de Arquivos de Ronda

Este documento explica como importar arquivos de ronda (.txt) no sistema, tanto manualmente quanto automaticamente.

## 📋 Índice

1. [Importação Manual via Interface Web](#importação-manual-via-interface-web)
2. [Importação Automática via Diretório](#importação-automática-via-diretório)
3. [Formato dos Arquivos](#formato-dos-arquivos)
4. [Verificação de Alertas](#verificação-de-alertas)

---

## 🌐 Importação Manual via Interface Web

### Rota: `/rondas/upload-process-ronda`

A interface web permite fazer upload e processamento manual de arquivos de ronda do WhatsApp.

**Acesso:**
- URL: `http://seu-servidor/rondas/upload-process-ronda`
- Requer: Login e permissão de administrador

**Funcionalidades:**
- Upload de arquivo .txt do WhatsApp
- Seleção de mês e ano para filtragem
- Processamento automático de múltiplos plantões
- Identificação automática do condomínio pelo nome do arquivo
- Feedback detalhado sobre o processamento

**Como usar:**
1. Acesse a rota `/rondas/upload-process-ronda`
2. Selecione o arquivo .txt do WhatsApp
3. (Opcional) Selecione mês e ano para filtrar
4. Clique em "Processar"
5. O sistema processará todos os plantões encontrados no arquivo

**Exemplo de nome de arquivo:**
- `Residencial_Exemplo_WhatsApp.txt`
- `Condominio_ABC_2025.txt`

O sistema identifica o condomínio pelo nome do arquivo, então é importante que o nome contenha parte do nome do condomínio cadastrado.

---

## 📁 Importação Automática via Diretório

### Sistema de Automação de Rondas

O sistema possui um serviço de automação que monitora um diretório e processa automaticamente arquivos .txt de ronda.

### Configuração do Diretório

Para usar a importação automática, você precisa configurar três diretórios:

1. **Diretório de Entrada** (`whatsapp_files_dir`): Onde você coloca os arquivos .txt para processamento
2. **Diretório de Processados** (`processed_files_dir`): Para onde os arquivos são movidos após processamento bem-sucedido
3. **Diretório de Erros** (`error_files_dir`): Para onde os arquivos são movidos em caso de erro

### Localização Recomendada dos Diretórios

**Windows:**
```
C:\rondas\
├── entrada\          # Coloque os arquivos .txt aqui
├── processados\      # Arquivos processados com sucesso
└── erros\           # Arquivos com erro
```

**Linux/Mac:**
```
/var/rondas/
├── entrada/
├── processados/
└── erros/
```

### Como Usar a Importação Automática

1. **Coloque o arquivo .txt no diretório de entrada**
   - O nome do arquivo deve conter parte do nome do condomínio
   - Exemplo: `Residencial_Exemplo_WhatsApp.txt`

2. **Execute o processamento**
   - O processamento pode ser feito via comando CLI ou agendado
   - O sistema processará todos os plantões encontrados no arquivo

3. **Verifique os resultados**
   - Arquivos processados com sucesso são movidos para `processados/`
   - Arquivos com erro são movidos para `erros/`
   - Verifique os logs para detalhes

### Exemplo de Uso do Serviço

```python
from app.services.ronda_automation_service import RondaAutomationService

# Configurar diretórios
service = RondaAutomationService(
    whatsapp_files_dir="C:/rondas/entrada",
    processed_files_dir="C:/rondas/processados",
    error_files_dir="C:/rondas/erros"
)

# Processar todos os arquivos
service.process_new_whatsapp_files()

# Processar apenas um mês específico
service.process_new_whatsapp_files(month=8, year=2025)
```

---

## 📄 Formato dos Arquivos

### Formato Esperado (WhatsApp Export)

O sistema espera arquivos .txt no formato de exportação do WhatsApp:

```
[15/07/2024, 19:41] VTR 01: Início de ronda
[15/07/2024, 20:10] VTR 01: Término de ronda
[15/07/2024, 21:30] VTR 02: Início de ronda
[15/07/2024, 22:00] VTR 02: Término de ronda
```

**Formatos aceitos:**
- `[DD/MM/YYYY, HH:MM] Autor: Mensagem`
- `DD/MM/YYYY HH:MM - Autor: Mensagem`

**Eventos reconhecidos:**
- Início de ronda: "Início de ronda", "inicio ronda", etc.
- Término de ronda: "Término de ronda", "termino ronda", "fim ronda", etc.

### Identificação do Condomínio

O sistema identifica o condomínio pelo **nome do arquivo**. O nome deve conter parte do nome do condomínio cadastrado no sistema.

**Exemplos:**
- Arquivo: `Residencial_Exemplo.txt` → Condomínio: "Residencial Exemplo"
- Arquivo: `Condominio_ABC_2025.txt` → Condomínio: "Condominio ABC"

---

## ⚠️ Verificação de Alertas

### Comando: `flask verificar-alertas-rondas`

Após processar as rondas, você pode verificar quais têm alertas de erro usando o comando CLI.

**Uso básico:**
```bash
flask verificar-alertas-rondas
```

**Com opções:**
```bash
# Salvar relatório em arquivo
flask verificar-alertas-rondas -o relatorio_alertas.txt

# Filtrar por condomínio
flask verificar-alertas-rondas --condominio-id 1

# Filtrar por período
flask verificar-alertas-rondas --data-inicio 2025-01-01 --data-fim 2025-12-31

# Combinar filtros
flask verificar-alertas-rondas --condominio-id 1 --data-inicio 2025-08-01 -o alertas_agosto.txt
```

### Tipos de Alertas Identificados

O comando identifica os seguintes tipos de alertas:

1. **⚠️ Alertas de Horário**
   - Término ocorreu antes do início
   - Horários inconsistentes

2. **⚠️ Rondas sem Início**
   - Término de ronda sem início correspondente

3. **⚠️ Rondas sem Término**
   - Início de ronda sem término correspondente
   - Início pendente no final do log

4. **⚠️ Outros Alertas**
   - Eventos inválidos
   - Problemas de parsing

### Exemplo de Saída

```
====================================================================================================
RELATÓRIO DE VARREURA DE ALERTAS EM RONDAS
Data da Verificação: 15/08/2025 14:30:00
Total de Rondas Verificadas: 150
Rondas com Alertas: 5
Total de Alertas Encontrados: 8
====================================================================================================

📊 RESUMO POR TIPO DE ALERTA:
----------------------------------------------------------------------------------------------------
  ⚠️  Alertas de Horário: 2
  ⚠️  Rondas sem Início: 3
  ⚠️  Rondas sem Término: 2
  ⚠️  Outros Alertas: 1

📋 LISTA DETALHADA DE RONDAS COM ALERTAS:
====================================================================================================

1. RONDA ID #123
   📅 Data do Plantão: 10/08/2025
   🏢 Condomínio: Residencial Exemplo (ID: 1)
   👨‍💼 Supervisor: Luis Royo
   ⏰ Turno: Diurno Par
   📊 Total de Rondas no Log: 12
   ⚠️  Total de Alertas: 2

   ALERTAS ENCONTRADOS:
      1. Término de ronda para VTR 01 às 10/08/2025 20:30 sem início correspondente...
      2. Início de ronda para VTR 02 às 10/08/2025 21:00 sem término no final do log...
----------------------------------------------------------------------------------------------------
```

---

## 🔍 Troubleshooting

### Arquivo não é processado

**Problema:** O arquivo não é identificado ou processado.

**Soluções:**
1. Verifique se o nome do arquivo contém parte do nome do condomínio
2. Verifique se o condomínio está cadastrado no sistema
3. Verifique o formato do arquivo (deve ser .txt)
4. Verifique os logs para mensagens de erro

### Condomínio não identificado

**Problema:** Sistema não consegue identificar o condomínio pelo nome do arquivo.

**Soluções:**
1. Renomeie o arquivo para incluir o nome exato do condomínio
2. Verifique se o condomínio está cadastrado no sistema
3. Use a importação manual via interface web

### Alertas em rondas processadas

**Problema:** Rondas processadas têm alertas de erro.

**Soluções:**
1. Execute `flask verificar-alertas-rondas` para identificar as rondas
2. Revise o log bruto da ronda para entender o problema
3. Corrija o arquivo original e reprocesse se necessário

---

## 📚 Referências

- [Documentação do Processador de Rondas](../ronda_logic/README.md)
- [API de Rondas](../../API_DOCUMENTATION.md#rondas)
- [Comandos CLI](../../README.md#comandos-cli-avançados)

---

**Última atualização:** 15/08/2025

