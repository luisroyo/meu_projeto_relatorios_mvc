# Sistema de Rondas - Documentação Técnica

## 📋 Visão Geral

O sistema de rondas permite o registro e gerenciamento de rondas de segurança em múltiplos condomínios, com suporte a diferentes turnos e geração de relatórios.

## 🏗️ Arquitetura

### Serviços Principais

#### 1. RondaTempoRealService (OFICIAL)
- **Arquivo**: `app/services/ronda_tempo_real_service.py`
- **Status**: ✅ **ATIVO** - Use este serviço
- **Responsabilidades**:
  - Iniciar/finalizar rondas em tempo real
  - Gerenciar múltiplos condomínios por usuário
  - Gerar relatórios por plantão
  - Controle de exportação de relatórios

#### 2. RondaEsporadicaService (OBSOLETO)
- **Arquivo**: `app/services/ronda_esporadica_service.py`
- **Status**: ❌ **OBSOLETO** - Não use este serviço
- **Motivo**: Substituído pelo `RondaTempoRealService`

### Utilitários Centralizados

#### RondaUtils
- **Arquivo**: `app/services/ronda_utils.py`
- **Funções disponíveis**:
  - `identificar_plantao(hora_entrada)` - Identifica plantão (06h-18h ou 18h-06h)
  - `inferir_turno(escala_plantao)` - Infere turno (Diurno/Noturno)
  - `verificar_ronda_em_andamento()` - Verifica rondas ativas
  - `calcular_duracao_minutos()` - Calcula duração entre entrada/saída
  - `formatar_duracao()` - Formata duração para exibição
  - `obter_condominio_por_id()` - Busca condomínio com tratamento de erro
  - `obter_ronda_por_id()` - Busca ronda com tratamento de erro

## 🔌 APIs

### API Oficial (`/api/ronda-tempo-real/`)
- **Status**: ✅ **ATIVA**
- **Endpoints principais**:
  - `POST /iniciar` - Iniciar nova ronda
  - `POST /finalizar/<id>` - Finalizar ronda
  - `POST /cancelar/<id>` - Cancelar ronda
  - `GET /em-andamento` - Listar rondas ativas
  - `GET /estatisticas` - Obter estatísticas
  - `GET /condominios-com-ronda` - Condomínios com atividade
  - `GET /rondas-condominio/<id>` - Rondas de um condomínio
  - `POST /marcar-exportado-plantao-anterior` - Marcar plantão como exportado

### API Legada (`/api/rondas-esporadicas/`)
- **Status**: ⚠️ **OBSOLETA** - Com deprecation warnings
- **Ação**: Será desabilitada em versão futura
- **Migração**: Use `/api/ronda-tempo-real/`

## 📊 Modelo de Dados

### RondaEsporadica
```python
class RondaEsporadica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    data_plantao = db.Column(db.Date, nullable=False)
    escala_plantao = db.Column(db.String(20), nullable=False)  # "06h às 18h" ou "18h às 06h"
    turno = db.Column(db.String(20), nullable=False)  # "Diurno" ou "Noturno"
    hora_entrada = db.Column(db.Time, nullable=False)
    hora_saida = db.Column(db.Time)
    status = db.Column(db.String(20), default='em_andamento')  # em_andamento, finalizada, cancelada
    observacoes = db.Column(db.Text)
    exportado = db.Column(db.Boolean, default=False)  # Controle de exportação
```

## 🔄 Fluxo de Uso

### 1. Iniciar Ronda
```python
service = RondaTempoRealService(user_id=123)
ronda_data = service.iniciar_ronda(
    condominio_id=1,
    hora_entrada=time(18, 30),
    observacoes="Início do plantão noturno"
)
```

### 2. Finalizar Ronda
```python
ronda_data = service.finalizar_ronda(
    ronda_id=456,
    hora_saida=time(19, 15),
    observacoes="Ronda concluída sem incidentes"
)
```

### 3. Gerar Relatório
```python
relatorio = service.gerar_relatorio_plantao()
# Retorna lista de strings formatadas por condomínio
```

## 🎯 Identificação de Plantão

O sistema identifica automaticamente o plantão baseado na hora de entrada:

- **Plantão Diurno**: 06h às 18h
- **Plantão Noturno**: 18h às 06h (próximo dia)

## 📈 Funcionalidades Avançadas

### Controle de Exportação
- Campo `exportado` para controlar relatórios enviados
- Verificação de plantão anterior pendente
- Botão "Finalizar e marcar como enviado"

### Múltiplos Condomínios
- Um usuário pode ter rondas em vários condomínios
- Interface mostra condomínios com atividade
- Modal com detalhes por condomínio

### Relatórios Detalhados
- Formato padronizado por condomínio
- Cálculo automático de duração
- Total de rondas completas

## 🚨 Tratamento de Erros

### Erros Comuns
1. **Ronda não encontrada**: Verificar se ID existe
2. **Condomínio não encontrado**: Verificar se condomínio existe
3. **Ronda já finalizada**: Não permite finalizar duas vezes
4. **Usuário não autorizado**: Só pode gerenciar próprias rondas

### Logs
- Todos os erros são logados com `logging.error()`
- Deprecation warnings para APIs obsoletas
- Logs de criação/finalização de rondas

## 🔧 Configuração

### Variáveis de Ambiente
- `FLASK_ENV=development` - Habilita interface de rondas em tempo real
- `DATABASE_URL` - Conexão com banco de dados

### Dependências
- Flask-SQLAlchemy
- psycopg2-binary (PostgreSQL)
- Flask-Login (autenticação)

## 📝 Exemplos de Uso

### Via API REST
```bash
# Iniciar ronda
curl -X POST http://localhost:5000/api/ronda-tempo-real/iniciar \
  -H "Content-Type: application/json" \
  -d '{"condominio_id": 1, "hora_entrada": "18:30", "observacoes": "Início"}'

# Finalizar ronda
curl -X POST http://localhost:5000/api/ronda-tempo-real/finalizar/123 \
  -H "Content-Type: application/json" \
  -d '{"hora_saida": "19:15", "observacoes": "Concluída"}'
```

### Via Python
```python
from app.services.ronda_tempo_real_service import RondaTempoRealService
from datetime import time

service = RondaTempoRealService(user_id=123)

# Iniciar ronda
ronda = service.iniciar_ronda(1, time(18, 30))

# Listar rondas ativas
ativas = service.listar_rondas_em_andamento()

# Gerar relatório
relatorio = service.gerar_relatorio_plantao()
```

## 🔄 Migração de APIs

### De API Legada para Oficial
```python
# ANTES (OBSOLETO)
POST /api/rondas-esporadicas/iniciar
{
  "condominio_id": 1,
  "user_id": 123,
  "data_plantao": "2025-01-30",
  "hora_entrada": "18:30",
  "escala_plantao": "18h às 06h"
}

# DEPOIS (OFICIAL)
POST /api/ronda-tempo-real/iniciar
{
  "condominio_id": 1,
  "hora_entrada": "18:30",
  "observacoes": "Início do plantão"
}
```

## 📚 Referências

- [REFATORACAO_RONDAS.md](../REFATORACAO_RONDAS.md) - Plano de refatoração
- [README.md](../README.md) - Documentação geral do projeto
- [app/models/ronda_esporadica.py](../models/ronda_esporadica.py) - Modelo de dados

---

**Última atualização**: 2025-01-30
**Versão**: 1.0
**Status**: Ativo 