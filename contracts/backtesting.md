# Contrato de backtesting

## Marco 3: Walk-Forward sem Vazamento Temporal

O backtest em Marco 3 implementa validação walk-forward com verificação rigorosa de integridade temporal.

### Invariantes de Integridade Temporal

Para cada data alvo `T`:

1. **Congela histórico até `T-1`**: Dados de treinamento são estritamente `held_on < T`
2. **Detecta vazamento**: Levanta `TemporalLeakageDetected` se:
   - `T` não existe no conjunto de dados
   - Histórico insuficiente para janela de treinamento
   - Estratégia recebe dados de `T` ou posteriores
3. **Processa alvo**: Aplica estratégia com seed fixo
4. **Congela carteira**: 10 apostas de €0,50 (total €5,00) com números previstos
5. **Revela resultado**: Compara contra números reais de `T`
6. **Registra métricas**: Distribuição de acertos, taxas, intervalos de confiança

### Estratégias Determinísticas

Marco 3 inclui quatro estratégias de baseline **sem ML**:

1. **uniform_random**: Amostra aleatória de 1-49 com seed fixo
2. **frequency_only**: Favorece números históricos mais frequentes
3. **delay_only**: Favorece números ausentes em draws recentes
4. **mixed_frequency_delay**: Combina ambos sinais

Todas devem ser determinísticas: `seed + training_draws → números identicamente`

**Exclusão ML obrigatória**: Sem XGBoost, LightGBM, CatBoost, RandomForest, ensemble, otimizador.

### Contratos de Dados

#### BacktestConfig
Especifica configuração do backtest. Campos obrigatórios:
- `strategy_name`: um de {uniform_random, frequency_only, delay_only, mixed_frequency_delay}
- `start_date`, `end_date`: formato YYYY-MM-DD, start ≤ end
- `training_window_days`: dias de histórico (>0)
- `tickets_per_draw`: apostas por concurso (>0, padrão 10)
- `random_seed`: seed para determinismo
- `dataset_sha256`, `code_commit_sha`: SHA-256 para rastreabilidade

#### BacktestRun
Captura resultado completo. Campos obrigatórios:
- `run_id`: identificador canônico (16 chars hex, derivado deterministicamente)
- `config`: BacktestConfig
- `started_at_utc`, `completed_at_utc`: timestamps UTC
- `status`: "success" ou "failed"
- `metrics`: BacktestMetrics (não None se success)

run_id é derivado canonicamente via `SHA256(JSON_canonical(config))[:16]` onde config inclui:
strategy_name, start_date, end_date, training_window_days, tickets_per_draw, random_seed,
dataset_sha256, code_commit_sha, parameters (tudo serializado com sort_keys=True, separators=(",", ":"))

#### BacktestMetrics
Contém métricas computadas. Campos obrigatórios:
- `average_hits`: média de acertos por concurso (0-6)
- `hit_distribution`: mapa {acertos → frequência}
- `hit_rate_2_plus`, `hit_rate_3_plus`, `hit_rate_4_plus`, `hit_rate_5_plus`, `hit_rate_6`: proporções
- `probability_score`: `average_hits / 6`
- `confidence_intervals`: dicionário de intervalos para métricas

### Contratos de Comportamento

#### WalkForwardValidator
- **Sem vazamento**: Dados de treinamento estritamente `< target_date`
- **Determinismo**: Mesma seed + dados = mesmo resultado
- **Atomicidade**: Cada concurso processado isoladamente
- **Levanta TemporalLeakageDetected** para integridade inviolável

#### AtomicArtifactWriter
- **Atomicidade de arquivo**: temp → fsync → os.replace
- **Crash-safe**: Interrupção não deixa artefatos parciais
- **Idempotência**: Reescrever com mesmo run_id é seguro
- **Rastreabilidade**: Manifesto com SHA-256 de cada arquivo

### Estrutura de Artefatos

Seis arquivos canônicos criados atomicamente:

```
backtests/runs/<run_id>/
├── config.json        # BacktestConfig com todos os 9 campos
├── metrics.json       # BacktestMetrics com hit_distribution, rates, intervalos
├── draw_results.csv   # Cabeçalho: target_date,predicted_numbers,actual_numbers,hits
├── tickets.csv        # Cabeçalho: draw_date,ticket_numbers,cost_eur
├── warnings.json      # run_id, generated_at_utc, warnings list
└── manifest.json      # Inventário: run_id, timestamps, status, files{nome→SHA-256}
```

**Nenhum run.json criado** (contrato: arquivo único não permitido). Manifesto lista SHA-256 dos 5 arquivos restantes.

### Contratos de CLI

Subcomandos obrigatórios:
- `bonoai backtest run`: Executar walk-forward
- `bonoai backtest list`: Listar execuções
- `bonoai backtest show`: Exibir resultado
- `bonoai backtest compare`: Comparar dois runs
- `bonoai backtest verify`: Verificar integridade

Todos suportam `--json` para saída estruturada.

### Reprodutibilidade

Cada run registra:
- `dataset_sha256`: Hash do conjunto canônico em tempo de execução
- `code_commit_sha`: Commit SHA do código executado
- `random_seed`: Exato seed utilizado
- `config` completo com todos hiperparâmetros

Reexecução com dataset + código + seed idênticos deve produzir métricas iguais (exceto imprecisão flutuante).

## Protocolo Original (Referência)

Backtest geral usa janela expansiva com comparadores obrigatórios:

1. dez apostas uniformes distintas;
2. scorer uniforme usando o mesmo otimizador do candidato;
3. frequência histórica usando o mesmo otimizador;
4. ensemble candidato;
5. rótulos embaralhados como controle negativo.

Métricas incluem Brier score, log loss, distribuição de acertos, cobertura de apostas.

**ROI**: Só pode ser calculado quando prêmios/dividendos oficiais por concurso estiverem
versionados e validados.
