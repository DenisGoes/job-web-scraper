<!-- # Scheduler

## Objetivo

O Scheduler é responsável por executar tarefas automáticas em horários definidos.

Atualmente ele possui algums responsabilidades: 

- enviar lembretes
- excluir vagas expiradas

---

## Regras de negócio

### Vaga salva

Quando o usuário salva uma vaga: 

- a data é registrada.
- durante 3 dias serão enviados lembretes.
- após o terceiro dia a vaga será removida.

---

### Vaga aplicada

Quando o usuário marca uma vaga como aplicada:

- ela permanece no banco de dados por 7 dias.
- após esse período é removida.

--- -->
