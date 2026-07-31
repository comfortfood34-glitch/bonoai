# ADR 0005 — Marco 3: Walk-Forward Backtesting com Integridade Temporal

- Status: aceito
- Data: 2026-07-30

## Contexto

Marco 1 consolidou ingestão e reconciliação de dados. Marco 2 implementou auditoria
completa com validação científica. Marco 3 adiciona backtesting determinístico sem
vazamento temporal.

Requisitos:
1. Walk-forward validation: cada concurso-alvo usa apenas histórico anterior
2. Nenhuma máquina de ML, ensemble ou otimização
3. Baselines científicos: uniform_random, frequency_only, delay_only, mixed_frequency_delay
4. Reproduzibilidade: mesmos dados + configuração + seed = mesmos resultados
5. Métricas rigorosas: distribuição de acertos, intervalos de confiança, comparação com baseline
6. Artefatos atômicos: escrita segura com SHA-256
7. Dashboard local MVP (read-only)

## Decisão

### Arquitetura de Walk-Forward

```
WalkForwardValidator
├─ all_draws: tuple (ordenado por data)
├─ get_training_data(target_date, window_days)
│  └─ retorna apenas draws com held_on < target_date
├─ get_target_draw(target_date)
│  └─ validação de vazamento temporal
└─ execute(config, strategy_fn)
   └─ itera cada target_date
      ├─ valida history prior
      ├─ executa strategy (determinístico)
      ├─ conta acertos vs. actual
      └─ acumula métricas
```

Invariante: nenhum dado futuro (>= target_date) é exposto ao strategy_builder.

### Baselines (Sem ML)

**uniform_random**: amostra aleatória, seed determinístico (baseline puro)
**frequency_only**: seleciona 6 mais frequentes no histórico
**delay_only**: seleciona 6 com maior "atraso" desde última aparição
**mixed_frequency_delay**: weighted blend (0.6 freq + 0.4 delay)

Todas são determinísticas, não veem o concurso-alvo.

### Controles Científicos

**LeakageTest**: verifica se strategy é determinístico e não revela dados do target
**ReproducibilityTest**: valida datasets idênticos → execuções idênticas
**NegativeControl**: compara strategy vs. shuffle aleatório

### Contratos

```python
@dataclass(frozen=True)
class BacktestConfig:
    strategy_name: str  # uma dos 4 baselines
    start_date: str     # YYYY-MM-DD
    end_date: str
    training_window_days: int
    dataset_sha256: str  # rastreabilidade
    code_commit_sha: str

@dataclass(frozen=True)
class BacktestMetrics:
    hit_distribution: dict[int, int]  # 0-6 hits
    average_hits: float
    hit_rate_2_plus: float
    confidence_intervals: dict[str, ConfidenceInterval]

@dataclass(frozen=True)
class BacktestRun:
    run_id: str (determinístico)
    config: BacktestConfig
    status: "success" | "failed"
    metrics: BacktestMetrics | None
```

Todos frozen, fail-closed, sem defaults silenciosos.

### Artefatos e Reproduzibilidade

Estrutura: `backtests/runs/<run_id>/` com 6 arquivos canônicos:
```
config.json        (BacktestConfig com 9 campos)
metrics.json       (BacktestMetrics com distribuição, rates, intervalos)
draw_results.csv   (cabeçalho: target_date,predicted_numbers,actual_numbers,hits)
tickets.csv        (cabeçalho: draw_date,ticket_numbers,cost_eur)
warnings.json      (run_id, generated_at_utc, warnings)
manifest.json      (run_id, status, timestamps, arquivo → SHA-256)
```

Escrita atômica: temp file → fsync → os.replace. Nenhum run.json.

run_id: determinístico = SHA256(JSON_canonical(config))[:16] onde config inclui
strategy_name, start_date, end_date, training_window_days, tickets_per_draw,
random_seed, dataset_sha256, code_commit_sha, parameters com sort_keys=True.

Dataset SHA: rastreia qual snapshot foi usado (auditória)

### CLI

Subcomandos implementados:
```
bonoai backtest run --strategy uniform_random --start-date 2025-01-01 \
  --end-date 2025-12-31 --training-window 10 --seed 42
bonoai backtest list           # Lista todas as execuções
bonoai backtest show <run_id>  # Mostra resultado detalhado
bonoai backtest compare <id1> <id2>  # Compara dois runs
bonoai backtest verify <run_id>      # Verifica integridade SHA-256
```

Exit codes: 0=sucesso, 1=validação falhou, 2=erro operacional

### Dashboard (MVP)

Streamlit app (read-only):
- Listagem de execuções
- Seletor de run
- Métricas (avg hits, taxa 2+/3+/4+/6)
- Gráfico de distribuição
- Config display (período, seed)

Sem manipulação de dados, sem download de runs.

## Alternativas

- Usar MLflow ou Weights & Biases: complexidade, dependencies, requer credenciais
- Banco de dados SQL: overkill para MVP; JSON + filesystem suficiente
- Começo imediato com ML: violaria AGENTS.md; baseline first é científicamente correto

## Consequências

- Backtesting é reproduzível e auditável
- Nenhum vazamento temporal possível (validação em runtime)
- Baseline sem overfitting (não vê target)
- Integridade temporal verificável (invariantes em walk-forward)
- Dashboard permite exploração sem modificação
- Preparação para Marco 4-6 (modelos, otimizador, validação)

## Notas de Implementação

- Determinismo: mesmo RNG seed + data = mesmos resultados
- Sem cálculo de ROI (AGENTS.md: proibido sem dividendos oficiais)
- Sem previsão enganosa: backtesting ≠ capacidade preditiva real
- Não alterar Marco 2 contracts sem necessidade
- Atomicidade: falhas não deixam estado parcial
