# Changelog

Todas as mudanças relevantes serão registradas neste arquivo.

## [Marco 3] - 2026-07-30

### Adicionado

- Backtesting walk-forward com integridade temporal (TemporalLeakageDetected).
- run_id canônico: derivação determinística de SHA-256 sobre todos os parâmetros de config.
- Estrutura de artefatos: 6 arquivos + manifesto (config, metrics, draw_results, tickets, warnings, manifest).
- Escrita atômica de artefatos com fsync + os.replace para crash-safety.
- CLI `bonoai backtest` com subcomandos: run, list, show, compare, verify.
- Estratégias determinísticas puras (sem ML): uniform_random, frequency_only, delay_only, mixed_frequency_delay.
- Intervalo de confiança normalizado a [0,1] com suporte a múltiplas métricas.
- Exit codes padronizados: 0=sucesso, 1=validação falhou, 2=erro operacional.

### Corrigido

- Nenhum vazamento temporal em walk-forward: validação rigorosa de datas e janelas.
- Determinismo completo: idempotência de artefatos para mesma configuração.
- Sem ML components: XGBoost, LightGBM, RandomForest, ensemble explicitamente excluídos.

## [Marco 2] - 2026-07-30

### Adicionado

- Comando `data-migrate`: migração atômica de schema v1 → v2 com validação e backup.
- Auditoria completa: coleta de todos os achados e conflitos sem interrupção.
- Validação de proveniância: rejeição de duplicatas e ordenação determinística por fingerprint.
- CanonicalDrawRecord com validação obrigatória de proveniância mínima.
- Distribuição de fonte por tipo (official/auxiliary/manual) na auditoria.
- Primeira data e última data do período auditado.

### Corrigido

- Exit codes: 0=ok (com avisos), 1=erro nos dados, 2=erro operacional.
- Reconciliação não mais lança SourceConflictError; coleta conflitos em audit.conflicts.
- Auditoria ordena findings e conflicts deterministicamente.
- Details em AuditFinding como dict estruturado, não string.

## [0.2.0] - 2026-07-29

### Adicionado

- Esquema canônico de concursos com proveniência e versão.
- Parser fail-closed do RSS oficial da SELAE.
- Arquivo bruto imutável com manifesto e SHA-256.
- Repositório CSV com escrita atômica e detecção de conflitos.
- Casos de uso e comandos `data-update` e `data-status`.
- ADR sobre o papel incremental do RSS oficial.

## [0.1.0] - 2026-07-29

### Adicionado

- Fundação do domínio Bonoloto e invariantes de aposta.
- Baseline uniforme reproduzível para carteiras.
- CLI `info` e `generate`.
- Contratos de produto, dados, tempo e backtesting.
- Governança para agentes, ADRs e integração contínua.
- Testes de domínio, orçamento, reprodutibilidade e corte temporal.
