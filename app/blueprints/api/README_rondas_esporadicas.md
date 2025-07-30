# APIs de Rondas Esporádicas - PWA

Este documento descreve as APIs para gerenciar rondas esporádicas via PWA (Progressive Web App).

## 📋 **Visão Geral**

As rondas esporádicas são registros de entrada e saída em condomínios específicos, permitindo:
- Iniciar e finalizar rondas individualmente
- Validar horários de entrada/saída
- Consolidar relatórios por turno
- Integração com sistema existente

## 🔗 **Endpoints Disponíveis**

### **1. Validar Horário de Entrada**
```http
POST /api/rondas-esporadicas/validar-horario
```

**Payload:**
```json
{
  "hora_entrada": "14:30"
}
```

**Resposta:**
```json
{
  "sucesso": true,
  "horario_valido": true,
  "mensagem": "Horário válido",
  "hora_atual": "14:25",
  "hora_informada": "14:30"
}
```

### **2. Verificar Ronda em Andamento**
```http
GET /api/rondas-esporadicas/em-andamento/{condominio_id}?data_plantao=2025-01-30
```

**Resposta:**
```json
{
  "em_andamento": true,
  "ronda": {
    "id": 1,
    "hora_entrada": "14:30",
    "data_plantao": "2025-01-30",
    "escala_plantao": "06h às 18h",
    "turno": "Diurno",
    "observacoes": "Início da ronda",
    "user_id": 1,
    "supervisor_id": 2
  }
}
```

### **3. Iniciar Ronda**
```http
POST /api/rondas-esporadicas/iniciar
```

**Payload:**
```json
{
  "condominio_id": 1,
  "user_id": 1,
  "data_plantao": "2025-01-30",
  "hora_entrada": "14:30",
  "escala_plantao": "06h às 18h",
  "supervisor_id": 2,
  "observacoes": "Início da ronda"
}
```

**Resposta:**
```json
{
  "sucesso": true,
  "message": "Ronda iniciada com sucesso!",
  "ronda_id": 1
}
```

### **4. Finalizar Ronda**
```http
PUT /api/rondas-esporadicas/finalizar/{ronda_id}
```

**Payload:**
```json
{
  "hora_saida": "18:00",
  "observacoes": "Finalização da ronda"
}
```

**Resposta:**
```json
{
  "sucesso": true,
  "message": "Ronda finalizada com sucesso!"
}
```

### **5. Atualizar Ronda**
```http
PUT /api/rondas-esporadicas/atualizar/{ronda_id}
```

**Payload:**
```json
{
  "observacoes": "Nova observação durante a ronda"
}
```

**Resposta:**
```json
{
  "sucesso": true,
  "message": "Ronda atualizada com sucesso!"
}
```

### **6. Listar Rondas do Dia**
```http
GET /api/rondas-esporadicas/do-dia/{condominio_id}/{data}
```

**Exemplo:** `GET /api/rondas-esporadicas/do-dia/1/2025-01-30`

**Resposta:**
```json
{
  "rondas": [
    {
      "id": 1,
      "condominio_id": 1,
      "condominio_nome": "Residencial A",
      "user_id": 1,
      "user_nome": "João Silva",
      "supervisor_id": 2,
      "supervisor_nome": "Maria Santos",
      "data_plantao": "2025-01-30",
      "escala_plantao": "06h às 18h",
      "turno": "Diurno",
      "hora_entrada": "14:30",
      "hora_saida": "18:00",
      "duracao_formatada": "3h 30min",
      "duracao_minutos": 210,
      "status": "finalizada",
      "observacoes": "Ronda completa",
      "data_criacao": "2025-01-30T14:30:00Z",
      "data_modificacao": "2025-01-30T18:00:00Z"
    }
  ]
}
```

### **7. Consolidar Turno**
```http
POST /api/rondas-esporadicas/consolidar-turno/{condominio_id}/{data}
```

**Exemplo:** `POST /api/rondas-esporadicas/consolidar-turno/1/2025-01-30`

**Resposta:**
```json
{
  "sucesso": true,
  "total_rondas": 3,
  "rondas_finalizadas": 3,
  "duracao_total_minutos": 630,
  "relatorio": "RELATÓRIO DE RONDAS ESPORÁDICAS - Residencial A\nData: 30/01/2025\nTotal de Rondas: 3\nRondas Finalizadas: 3\nDuração Total: 630 minutos\n\nRonda 1:\n  Entrada: 14:30\n  Saída: 18:00\n  Duração: 3h 30min\n  Status: finalizada\n  Observações: Ronda completa\n\n..."
}
```

### **8. Detalhes da Ronda**
```http
GET /api/rondas-esporadicas/{ronda_id}
```

**Resposta:**
```json
{
  "id": 1,
  "condominio_id": 1,
  "condominio_nome": "Residencial A",
  "user_id": 1,
  "user_nome": "João Silva",
  "supervisor_id": 2,
  "supervisor_nome": "Maria Santos",
  "data_plantao": "2025-01-30",
  "escala_plantao": "06h às 18h",
  "turno": "Diurno",
  "hora_entrada": "14:30",
  "hora_saida": "18:00",
  "duracao_formatada": "3h 30min",
  "duracao_minutos": 210,
  "status": "finalizada",
  "observacoes": "Ronda completa",
  "log_bruto": null,
  "relatorio_processado": null,
  "data_criacao": "2025-01-30T14:30:00Z",
  "data_modificacao": "2025-01-30T18:00:00Z"
}
```

## 🔧 **Validações**

### **Horário de Entrada**
- Tolerância padrão: 30 minutos
- Compara com horário atual do sistema
- Retorna aviso se diferença for muito grande

### **Ronda em Andamento**
- Apenas uma ronda por condomínio por data
- Status: "em_andamento", "finalizada", "cancelada"

### **Formato de Dados**
- **Data**: `YYYY-MM-DD` (ex: "2025-01-30")
- **Hora**: `HH:MM` (ex: "14:30")
- **Escala**: "06h às 18h" ou "18h às 06h"

## 📱 **Uso no PWA**

### **Fluxo Típico:**

1. **Selecionar Condomínio**
2. **Validar Horário de Entrada**
3. **Iniciar Ronda** (se não houver em andamento)
4. **Atualizar Observações** (durante a ronda)
5. **Finalizar Ronda** (com hora de saída)
6. **Consolidar Turno** (ao final do período)

### **Exemplo de Integração:**

```javascript
// Validar horário antes de iniciar
const validarHorario = async (hora) => {
  const response = await fetch('/api/rondas-esporadicas/validar-horario', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hora_entrada: hora })
  });
  return response.json();
};

// Iniciar ronda
const iniciarRonda = async (dados) => {
  const response = await fetch('/api/rondas-esporadicas/iniciar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados)
  });
  return response.json();
};
```

## 🚀 **APIs de Consolidação**

### **9. Consolidar e Enviar WhatsApp**
```http
POST /api/rondas-esporadicas/consolidar-e-enviar/{condominio_id}/{data}
```

**Exemplo:** `POST /api/rondas-esporadicas/consolidar-e-enviar/1/2025-01-30`

**Resposta:**
```json
{
  "sucesso": true,
  "message": "Consolidação realizada com sucesso",
  "whatsapp_enviado": true,
  "ronda_principal_id": 123,
  "total_rondas": 3,
  "duracao_total_minutos": 630,
  "relatorio": "🔄 RELATÓRIO DE RONDAS ESPORÁDICAS..."
}
```

### **10. Marcar Rondas como Processadas**
```http
PUT /api/rondas-esporadicas/marcar-processadas/{condominio_id}/{data}
```

**Exemplo:** `PUT /api/rondas-esporadicas/marcar-processadas/1/2025-01-30`

### **11. Processo Completo**
```http
POST /api/rondas-esporadicas/processo-completo/{condominio_id}/{data}
```

**Executa:** Consolidar → Enviar WhatsApp → Marcar como Processadas

### **12. Status de Consolidação**
```http
GET /api/rondas-esporadicas/status-consolidacao/{condominio_id}/{data}
```

**Resposta:**
```json
{
  "sucesso": true,
  "data": "2025-01-30",
  "condominio_id": 1,
  "status": {
    "total_rondas_esporadicas": 3,
    "rondas_finalizadas": 3,
    "rondas_processadas": 0,
    "duracao_total_minutos": 630,
    "ronda_principal_criada": false,
    "ronda_principal_id": null,
    "pode_consolidar": true,
    "ja_consolidado": false
  },
  "rondas": [...]
}
```

### **13. Estatísticas de Consolidação**
```http
GET /api/rondas-esporadicas/estatisticas/{condominio_id}?data_inicio=2025-01-01&data_fim=2025-01-31
```

## 🔄 **Fluxo de Consolidação**

1. **Coletar Rondas**: Sistema coleta todas as rondas esporádicas do dia
2. **Gerar Relatório**: Formata dados para WhatsApp
3. **Enviar WhatsApp**: Usa serviço existente de patrimonial
4. **Salvar Principal**: Cria registro na tabela `ronda` principal
5. **Marcar Processadas**: Atualiza status das rondas esporádicas

## 📊 **Integração com Sistema Principal**

- **Tabela `ronda_esporadica`**: Armazena rondas individuais
- **Tabela `ronda`**: Recebe dados consolidados (campo `tipo = "esporadica"`)
- **WhatsApp**: Envio automático via `PatrimonialReportService`
- **Relatórios**: Integração com sistema existente

## 🚀 **Próximos Passos**

- [x] Integração com WhatsApp
- [x] Salvamento no banco principal de rondas
- [ ] Dashboard para visualização
- [ ] Relatórios consolidados 