# 📱 Guia de Importação do WhatsApp para Rondas

## 🔒 Acesso Restrito

**⚠️ IMPORTANTE:** Esta funcionalidade está disponível **APENAS para administradores**.

## 🎯 Funcionalidade

Esta funcionalidade permite importar conversas do WhatsApp diretamente no formulário de ronda existente. **O sistema processa automaticamente** quando você seleciona a data e escala do plantão, preenchendo o log com as mensagens do período.

## 🚀 Como Usar

### 0. Verificar Permissões
- **Administrador**: Acesso completo à funcionalidade
- **Usuário comum**: Campo não aparece, apenas mensagem informativa

### 1. Exportar Conversa do WhatsApp

1. Abra o WhatsApp no seu celular
2. Vá para a conversa/grupo que deseja exportar
3. Toque no nome da conversa no topo
4. Role para baixo e toque em "Exportar conversa"
5. Escolha "Sem mídia" para arquivo menor
6. Envie o arquivo .txt para seu computador

### 2. Usar no Sistema

1. Acesse **"Registrar Ronda"** no menu
2. Preencha a **data do plantão** e **escala**
3. No campo **"Arquivo WhatsApp (.txt)"**, selecione o arquivo
4. **O log será preenchido automaticamente!** ✨
5. Revise e clique em **"Processar Relatório de Ronda"**
6. Salve a ronda

## ⚡ Processamento Automático

### ✅ Como Funciona
- **Seleciona arquivo** → Sistema aguarda data/escala
- **Seleciona data** → Sistema processa automaticamente
- **Seleciona escala** → Sistema processa automaticamente
- **Resultado** → Log preenchido instantaneamente!

### ✅ Indicadores Visuais
- **Processando**: Botão mostra spinner
- **Sucesso**: Botão fica verde com check
- **Erro**: Mensagem de aviso
- **Nenhuma mensagem**: Aviso informativo

## 📋 Formato Esperado

O arquivo deve estar no formato padrão do WhatsApp:

```
[25/12/2024, 06:30] João Silva: Iniciando plantão diurno
[25/12/2024, 06:45] João Silva: Primeira ronda concluída
[25/12/2024, 07:15] Maria Santos: Ronda 2 - setor B tranquilo
```

## ⚙️ Como Funciona

### ✅ Processamento Automático
- **Data**: Baseado na data selecionada no formulário
- **Escala**: 
  - **06h às 18h**: Busca mensagens das 06:00 às 17:59 (mesmo dia)
  - **18h às 06h**: Busca mensagens das 18:00 às 05:59 (atravessa a meia-noite)

### ✅ Filtro Inteligente para Plantões Noturnos
- **Exemplo**: Selecione data 26/07/2025 + escala "18h às 06h"
- **Resultado**: Sistema busca mensagens das 18h do dia 26/07/2025 até 06h do dia 27/07/2025
- **Lógica**: Automaticamente entende que plantão noturno atravessa a meia-noite
- **✅ CORRIGIDO**: Filtro agora funciona corretamente com data/hora completa

### ✅ Formatação Automática
- Converte mensagens para formato de log
- Ignora mensagens do sistema (fotos, áudios, etc.)
- Organiza por horário cronológico

## 📊 Exemplos de Uso

### 🌅 Plantão Diurno
1. **Selecione**: Data 25/12/2024, Escala "06h às 18h"
2. **Upload**: Arquivo WhatsApp com mensagens do dia
3. **Automático**: Log preenchido com mensagens das 06:00 às 17:59

**Arquivo Original:**
```
[25/12/2024, 06:30] João Silva: Iniciando plantão
[25/12/2024, 06:45] João Silva: Ronda 1 concluída
[25/12/2024, 07:15] Maria Santos: Ronda 2 - tranquilo
```

**Log Formatado Automaticamente:**
```
[06:30, 25/12/2024] João Silva: Iniciando plantão
[06:45, 25/12/2024] João Silva: Ronda 1 concluída
[07:15, 25/12/2024] Maria Santos: Ronda 2 - tranquilo
```

### 🌙 Plantão Noturno (Filtro Inteligente)
1. **Selecione**: Data 26/07/2025, Escala "18h às 06h"
2. **Upload**: Arquivo WhatsApp com mensagens dos dias 26 e 27
3. **Automático**: Log preenchido com mensagens das 18h do dia 26 até 06h do dia 27

**Arquivo Original:**
```
[26/07/2025, 18:15] Pedro Costa: Iniciando plantão noturno
[26/07/2025, 20:30] Ana Silva: Ronda 1 - setor A tranquilo
[26/07/2025, 23:45] Pedro Costa: Ronda 2 - setor B normal
[27/07/2025, 01:30] Ana Silva: Ronda 3 - madrugada tranquila
[27/07/2025, 04:15] Pedro Costa: Ronda 4 - setor C sem ocorrências
[27/07/2025, 06:00] Ana Silva: Finalizando plantão noturno
```

**Log Formatado Automaticamente:**
```
[18:15, 26/07/2025] Pedro Costa: Iniciando plantão noturno
[20:30, 26/07/2025] Ana Silva: Ronda 1 - setor A tranquilo
[23:45, 26/07/2025] Pedro Costa: Ronda 2 - setor B normal
[01:30, 27/07/2025] Ana Silva: Ronda 3 - madrugada tranquila
[04:15, 27/07/2025] Pedro Costa: Ronda 4 - setor C sem ocorrências
[06:00, 27/07/2025] Ana Silva: Finalizando plantão noturno
```

## 🎯 Benefícios

- ⚡ **Processamento Automático**: Não precisa clicar em botões
- 📱 **Conveniência**: Use conversas do WhatsApp
- 🕐 **Precisão**: Separação automática por horário
- 📊 **Organização**: Formato padronizado
- 🔄 **Flexibilidade**: Pode editar o log depois
- 🎨 **Interface Intuitiva**: Indicadores visuais claros

## ⚠️ Observações

- Apenas arquivos .txt são aceitos
- Mensagens do sistema são ignoradas automaticamente
- O sistema filtra baseado na data e escala selecionadas
- Você pode editar o log antes de salvar
- Campo opcional - funciona normalmente sem arquivo
- Processamento acontece em tempo real

## 🆘 Suporte

Se encontrar problemas:
1. Verifique se o arquivo está no formato correto
2. Certifique-se de que há mensagens no período desejado
3. Confirme se a data e escala estão corretas
4. Verifique se o arquivo não está corrompido
5. Entre em contato com o suporte técnico

## 🔧 Dicas de Uso

- **Primeiro**: Selecione a data e escala
- **Depois**: Faça upload do arquivo
- **Aguarde**: O processamento é automático
- **Revise**: Sempre verifique o log gerado
- **Edite**: Pode modificar o log se necessário

---

**Funcionalidade integrada com processamento automático - simples e eficiente!** 📱✨ 