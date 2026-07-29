# CLAUDE.md

Leia e cumpra [AGENTS.md](AGENTS.md) e [GOVERNANCE.md](GOVERNANCE.md) antes de modificar o repositório.

## Ordem de contexto

1. `AGENTS.md`
2. contrato específico em `contracts/`
3. ADRs em `docs/decisions/`
4. testes do módulo alterado
5. código

## Comandos seguros

```bash
make check
make lint
make typecheck
PYTHONPATH=src python3 -m bonoai info
```

Não execute ingestão real, treinamento pesado, geração de um milhão de candidatos ou
publicação externa sem solicitação explícita. Nunca inclua o concurso-alvo nas features.
