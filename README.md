# BonoAI

BonoAI é um projeto de pesquisa para analisar resultados da **Bonoloto espanhola**
com dados versionados, regras temporais explícitas e backtesting reproduzível.

O software não afirma prever sorteios aleatórios. Cada combinação simples de seis
números tem a mesma probabilidade de prêmio máximo. Modelos e filtros só podem ser
promovidos quando superarem baselines definidos em avaliações fora da amostra.

## Contrato inicial

- Universo: 6 números distintos de 1 a 49.
- Orçamento operacional padrão: €5.
- Preço de referência por aposta simples: €0,50.
- Saída padrão: exatamente 10 apostas simples e distintas.
- Reintegro: metadado; nunca é atributo preditivo dos seis números.
- Fonte canônica: dados oficiais da SELAE, com origem auxiliar explicitamente marcada.
- Regra temporal: ao avaliar o concurso `T`, todo cálculo usa somente concursos anteriores.

O preço é uma hipótese operacional configurável e deve ser conferido na fonte oficial
antes de registrar uma aposta real.

## Estado atual

A versão `0.2.0` entrega a fundação do domínio, um baseline uniforme reproduzível,
contratos científicos e a primeira fatia vertical do Marco 1:

- atualização incremental pelo RSS oficial da SELAE;
- esquema canônico CSV versionado;
- arquivo bruto imutável com SHA-256 e manifesto;
- reconciliação atômica, sem “último valor vence”;
- conflito explícito quando o mesmo concurso apresenta resultados diferentes.

O RSS oficial contém resultados recentes e serve à atualização incremental. O bootstrap
histórico completo continua sendo uma etapa separada e não é inferido a partir do feed.

## Começar

Requer Python 3.12 ou superior.

```bash
make setup
.venv/bin/bonoai info
.venv/bin/bonoai generate --budget 5.00 --seed 42
.venv/bin/bonoai data-update
.venv/bin/bonoai data-status
make check
```

Sem instalar o pacote:

```bash
PYTHONPATH=src python3 -m bonoai generate --seed 42
```

## Comandos

| Comando | Resultado |
|---|---|
| `bonoai info` | Mostra os invariantes operacionais |
| `bonoai generate` | Gera o baseline uniforme reproduzível |
| `bonoai data-update` | Arquiva e incorpora resultados recentes da SELAE |
| `bonoai data-status` | Mostra quantidade e período da base canônica |
| `make check` | Compila e executa a suíte de testes |
| `make lint` | Executa o Ruff |
| `make typecheck` | Executa o mypy em modo estrito |

## Arquitetura e governança

- [AGENTS.md](AGENTS.md): regras obrigatórias para agentes e contribuidores.
- [CLAUDE.md](CLAUDE.md): ponto de entrada compatível com fluxos Claude Code.
- [contracts/](contracts/): contratos executáveis e científicos do projeto.
- [docs/architecture.md](docs/architecture.md): limites entre as camadas.
- [docs/roadmap.md](docs/roadmap.md): ordem de implementação.
- [docs/decisions/](docs/decisions/): decisões arquiteturais registradas.
