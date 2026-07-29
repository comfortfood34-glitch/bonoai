# Roadmap

## Marco 0 — Fundação

- contratos, arquitetura, CLI e CI;
- entidades `Draw`, `Ticket` e `Portfolio`;
- baseline uniforme reproduzível;
- testes de orçamento, domínio e corte temporal.

## Marco 1 — Dados

- bootstrap histórico versionado;
- atualização incremental SELAE;
- reconciliação entre fontes, hashes e relatórios de conflito;
- esquema canônico e testes de qualidade.

## Marco 2 — Motor estatístico

- frequências nas janelas 10, 20, 50, 100 e 300;
- atraso, intervalos, tendência e dispersão;
- features de concurso separadas de features disponíveis antes do sorteio.

## Marco 3 — Backtesting antes de ML

- walk-forward com janela expansiva;
- baselines uniforme e frequência;
- métricas pareadas e controles negativos.

## Marco 4 — Modelos candidatos

- Random Forest, XGBoost, LightGBM e CatBoost como hipóteses;
- calibração, seleção interna e registro de experimentos;
- modelo reprovado nunca entra automaticamente no ensemble.

## Marco 5 — Otimizador

- geração eficiente e com limite de memória;
- filtros documentados como organização, não vantagem matemática;
- diversidade com garantia de dez apostas ou falha explícita;
- perfis smoke, research e certification.

## Marco 6 — Produto

- relatórios e dashboard;
- execução agendada somente após validação;
- monitoramento de dados, drift e reprodutibilidade.
