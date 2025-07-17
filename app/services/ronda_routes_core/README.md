# Pasta `ronda_routes_core`

Esta pasta contém **toda a lógica de domínio, validação, persistência e helpers** utilizados pelas rotas de ronda do sistema.

- **Não contém código de blueprint/rota Flask.**
- **Contém apenas serviços, regras de negócio, validações e utilitários** usados pelas rotas de ronda.
- O objetivo é centralizar e organizar toda a lógica de backend das rotas de ronda, facilitando manutenção, testes e evolução.

## Estrutura

- `helpers.py`: Funções utilitárias (ex: cálculo de turno)
- `validation.py`: Validações de dados de entrada
- `persistence_service.py`: Persistência e queries (CRUD, filtros, paginação)
- `business_service.py`: Regras de negócio (ex: atribuição de supervisor)
- `routes_service.py`: Orquestrador principal chamado pelas rotas Flask

---

**Atenção:**
- Toda alteração na lógica de backend das rotas de ronda deve ser feita aqui.
- As rotas Flask devem apenas orquestrar requisições e respostas, delegando toda a lógica para os serviços desta pasta. 