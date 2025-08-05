# Sistema de Rondas em Tempo Real

## Visão Geral

O Sistema de Rondas em Tempo Real permite que agentes registrem rondas em múltiplos condomínios durante seus plantões, com identificação automática do período de trabalho e geração de relatórios formatados.

## Funcionalidades Principais

### 1. Registro de Rondas
- **Iniciar Ronda**: Registra entrada em um condomínio com hora específica
- **Finalizar Ronda**: Registra saída com hora e observações opcionais
- **Cancelar Ronda**: Permite cancelar uma ronda em andamento

### 2. Identificação Automática de Plantão
O sistema identifica automaticamente o plantão baseado na primeira ronda do dia:
- **Plantão Diurno (06h às 18h)**: Se a primeira ronda for iniciada entre 06:00 e 17:59
- **Plantão Noturno (18h às 06h)**: Se a primeira ronda for iniciada entre 18:00 e 05:59

### 3. Agrupamento por Condomínio
- Cada condomínio tem suas rondas registradas separadamente
- Um mesmo agente pode fazer rondas em vários condomínios no mesmo plantão
- As rondas são agrupadas automaticamente por condomínio e plantão

### 4. Relatórios Formatados
Gera relatórios no formato exato solicitado:
```
Plantão 31/07/2025 (18h às 06h)
Residencial: ZERMATT

	Início: 18:11  – Término: 18:31 (20 min)
	Início: 19:24  – Término: 19:49 (25 min)
	Início: 21:04  – Término: 21:24 (20 min)
	Início: 22:28  – Término: 22:48 (20 min)
	Início: 00:17  – Término: 00:38 (21 min)
	Início: 01:49  – Término: 02:05 (16 min)
	Início: 03:01  – Término: 03:26 (25 min)
	Início: 04:30  – Término: 04:52 (22 min)

✅ Total: 8 rondas completas no plantão
```

## Arquitetura

### Serviços
- **`RondaTempoRealService`**: Serviço principal que gerencia toda a lógica de negócio
- **`RondaEsporadica`**: Modelo de dados para as rondas em tempo real

### APIs
- **`/api/ronda-tempo-real/condominios`**: Lista condomínios disponíveis
- **`/api/ronda-tempo-real/iniciar`**: Inicia uma nova ronda
- **`/api/ronda-tempo-real/finalizar/<id>`**: Finaliza uma ronda
- **`/api/ronda-tempo-real/em-andamento`**: Lista rondas em andamento
- **`/api/ronda-tempo-real/relatorio`**: Gera relatório do plantão
- **`/api/ronda-tempo-real/estatisticas`**: Retorna estatísticas
- **`/api/ronda-tempo-real/hora-atual`**: Retorna hora atual do servidor

### Interface Web
- **`/rondas/tempo-real`**: Interface web completa para gerenciar rondas

## Como Usar

### 1. Configuração Inicial
```bash
# Criar condomínios de exemplo
flask seed-condominios
```

### 2. Via Interface Web
1. Acesse `/rondas/tempo-real`
2. Selecione um condomínio e hora de entrada
3. Clique em "Iniciar Ronda"
4. Para finalizar, clique em "Finalizar" na lista de rondas em andamento
5. Gere o relatório clicando em "Gerar Relatório"

### 3. Via API (para app mobile/PWA)
```javascript
// Iniciar ronda
fetch('/api/ronda-tempo-real/iniciar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        condominio_id: 1,
        hora_entrada: "18:11",
        observacoes: "Entrada normal"
    })
});

// Finalizar ronda
fetch('/api/ronda-tempo-real/finalizar/123', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        hora_saida: "18:31",
        observacoes: "Saída normal"
    })
});

// Gerar relatório
fetch('/api/ronda-tempo-real/relatorio')
    .then(response => response.json())
    .then(data => {
        console.log(data.data.relatorios);
    });
```

## Fluxo de Trabalho Típico

1. **Início do Plantão**: Agente inicia primeira ronda em um condomínio
2. **Durante o Plantão**: Agente faz múltiplas rondas em diferentes condomínios
3. **Finalização**: Agente finaliza cada ronda ao sair do condomínio
4. **Relatório**: No final do plantão, gera relatório formatado por condomínio

## Características Técnicas

### Persistência
- Todas as rondas são salvas no banco de dados em tempo real
- Dados não se perdem mesmo se o app for fechado
- Suporte a múltiplos usuários simultâneos

### Sincronização
- Hora do servidor para evitar problemas de fuso horário
- API para sincronização com apps mobile/PWA

### Segurança
- Autenticação obrigatória para todas as operações
- Usuários só podem gerenciar suas próprias rondas
- Validação de dados em todas as operações

## Exemplo de Uso Completo

### Cenário: Plantão Noturno (18h às 06h)

1. **18:11** - Inicia ronda no ZERMATT
2. **18:31** - Finaliza ronda no ZERMATT
3. **19:24** - Inicia nova ronda no ZERMATT
4. **19:49** - Finaliza ronda no ZERMATT
5. **21:04** - Inicia ronda no RESIDENCIAL VILLA VERDE
6. **21:24** - Finaliza ronda no RESIDENCIAL VILLA VERDE
7. **22:28** - Volta ao ZERMATT, inicia nova ronda
8. **22:48** - Finaliza ronda no ZERMATT
9. **00:17** - Inicia ronda no ZERMATT (após meia-noite)
10. **00:38** - Finaliza ronda no ZERMATT
11. **01:49** - Inicia ronda no ZERMATT
12. **02:05** - Finaliza ronda no ZERMATT
13. **03:01** - Inicia ronda no ZERMATT
14. **03:26** - Finaliza ronda no ZERMATT
15. **04:30** - Inicia última ronda no ZERMATT
16. **04:52** - Finaliza última ronda no ZERMATT

### Relatório Gerado:
```
Plantão 31/07/2025 (18h às 06h)
Residencial: ZERMATT

	Início: 18:11  – Término: 18:31 (20 min)
	Início: 19:24  – Término: 19:49 (25 min)
	Início: 22:28  – Término: 22:48 (20 min)
	Início: 00:17  – Término: 00:38 (21 min)
	Início: 01:49  – Término: 02:05 (16 min)
	Início: 03:01  – Término: 03:26 (25 min)
	Início: 04:30  – Término: 04:52 (22 min)

✅ Total: 7 rondas completas no plantão

Plantão 31/07/2025 (18h às 06h)
Residencial: RESIDENCIAL VILLA VERDE

	Início: 21:04  – Término: 21:24 (20 min)

✅ Total: 1 ronda completa no plantão
```

## Próximos Passos

- [ ] Suporte a funcionamento offline
- [ ] Notificações push para lembretes
- [ ] Integração com GPS para validação de localização
- [ ] Exportação para PDF
- [ ] Dashboard com gráficos e métricas
- [ ] Integração com WhatsApp para envio automático de relatórios 