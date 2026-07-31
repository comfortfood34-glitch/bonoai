# Roadmap

## Marco 0 — Fundação

- contratos, arquitetura, CLI e CI;
- entidades `Draw`, `Ticket` e `Portfolio`;
- baseline uniforme reproduzível;
- testes de orçamento, domínio e corte temporal.

## Marco 1 — Dados (Canonical Ingestion)

- [x] atualização incremental SELAE pelo RSS oficial;
- [x] reconciliação, hashes e erro explícito de conflito;
- [x] esquema canônico CSV versionado (v1 e v2);
- [x] arquivo bruto imutável com manifesto e SHA-256;
- [x] escrita atômica, validação completa antes de modificar;
- [ ] bootstrap histórico com conflito explícito;
- [ ] reconciliação de múltiplas fontes auxiliares;
- [ ] relatório persistente de conflitos.

## Marco 2 — Auditoria e Validação (Data Quality)

- [x] comando `data-migrate`: migração idempotente de v1 → v2;
- [x] validação de proveniância: unicidade, rejeição de duplicatas;
- [x] auditoria completa: coleta todas as falhas sem interrupção;
- [x] exit codes: 0=ok, 1=erro dados, 2=erro operacional;
- [x] distribuição de fontes por tipo (official/auxiliary/manual);
- [x] período e datas extremas no relatório;
- [ ] lacunas suspeitas na série temporal;
- [ ] histórico de migração com rollback.

## Marco 3 — Backtesting científico com walk-forward

- [x] walk-forward determinístico sem vazamento temporal;
- [x] run_id canônico derivado de todos os parâmetros de config;
- [x] artefatos reproduzíveis: 6 arquivos + manifesto com SHA-256;
- [x] estratégias puras sem ML (uniform_random, frequency_only, delay_only);
- [x] CLI: `bonoai backtest run/list/show/compare/verify`;
- [x] intervalo de confiança normalizado a [0,1];
- [ ] read-only para históricos precedentes;
- [ ] exportação de resultados para análise externa.

## Marco 4 — Motor estatístico

- frequências nas janelas 10, 20, 50, 100 e 300;
- atraso, intervalos, tendência e dispersão;
- features de concurso separadas de features disponíveis antes do sorteio.

## Marco 5 — Modelos candidatos

- Random Forest, XGBoost, LightGBM e CatBoost como hipóteses;
- calibração, seleção interna e registro de experimentos;
- modelo reprovado nunca entra automaticamente no ensemble.

## Marco 6 — Otimizador

- geração eficiente e com limite de memória;
- filtros documentados como organização, não vantagem matemática;
- diversidade com garantia de dez apostas ou falha explícita;
- perfis smoke, research e certification.

## Marco 7 — Produto

- relatórios e dashboard;
- execução agendada somente após validação;
- monitoramento de dados, drift e reprodutibilidade.
