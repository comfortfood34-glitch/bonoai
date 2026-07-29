# ADR 0001 — Baselines antes de machine learning

- Status: aceito
- Data: 2026-07-29

## Contexto

Sorteios são desenhados para serem aleatórios. Um modelo complexo pode parecer melhor
por vazamento temporal, seleção oportunista ou variância.

## Decisão

Nenhum modelo de ML será tratado como componente operacional antes de existir backtest
walk-forward contra baselines uniformes e de frequência, com controle negativo e
avaliação fora da amostra.

## Consequências

- A primeira geração implementada é uniforme e reproduzível.
- Pesos fixos de ensemble são hipóteses, não configuração aprovada.
- Resultados negativos são resultados válidos e devem ser publicados no relatório.
