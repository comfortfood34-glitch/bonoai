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

A versão `0.2.0` + Marco 2 entrega:

- **Marco 1**: fundação de domínio, baseline uniforme, contratos, e primeira fatia vertical.
  - Atualização incremental pelo RSS oficial da SELAE
  - Esquema canônico CSV versionado (v1 e v2)
  - Arquivo bruto imutável com SHA-256 e manifesto
  - Reconciliação atômica, sem “último valor vence”
  - Conflito explícito quando o mesmo concurso apresenta resultados diferentes

- **Marco 2**: auditoria completa, migração de schema e validação de proveniância.
  - Comando `data-migrate`: migração idempotente de v1 → v2 com backup
  - Auditoria: coleta todos os achados e conflitos, não interrompe
  - Proveniâncias: validação de unicidade, rejeição de duplicatas, ordenação determinística
  - Exit codes: 0=sucesso (com avisos), 1=erro nos dados, 2=falha operacional
  - Distribuição de fontes por tipo (official/auxiliary/manual)
  - Período e datas extremas no relatório de auditoria

- **Marco 3**: backtesting científico com validação walk-forward e integridade temporal.
  - Walk-forward determinístico: cada concurso-alvo é avaliado com dados apenas anteriores
  - run_id canônico: derivado deterministicamente de todos os parâmetros de configuração
  - Artefatos reproduzíveis: 6 arquivos + manifesto com SHA-256 para auditoria
  - Estratégias sem ML: implementações puras sem XGBoost, LightGBM, RandomForest ou ensemble
  - CLI: `bonoai backtest run/list/show/compare/verify` com exit codes 0=sucesso, 1=inválido, 2=erro
  - Intervalo de confiança: normalizado a [0,1] baseado em média de acertos
  - Nenhum vazamento temporal: `TemporalLeakageDetected` detecta dados futuros na treining

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
| `bonoai data-migrate` | Migra dados de schema v1 para v2 (idempotente) |
| `bonoai data-bootstrap` | Carrega dados históricos de arquivo CSV local |
| `bonoai data-audit` | Audita e reconcilia fontes de dados |
| `bonoai backtest run` | Executa backtesting walk-forward determinístico |
| `bonoai backtest list` | Lista todas as execuções de backtest |
| `bonoai backtest show` | Mostra resultados detalhados de um backtest |
| `bonoai backtest compare` | Compara métricas entre dois backtests |
| `bonoai backtest verify` | Verifica integridade SHA-256 dos artefatos |
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
