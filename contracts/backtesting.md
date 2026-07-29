# Contrato de backtesting

## Protocolo mínimo

O backtest usa janela expansiva. Para cada alvo `T`:

1. congela o histórico até `T-1`;
2. ajusta qualquer transformação e modelo apenas nesse histórico;
3. gera exatamente dez apostas com custo total de €5;
4. congela a carteira e sua proveniência;
5. revela o resultado de `T`;
6. registra as métricas.

## Comparadores obrigatórios

1. dez apostas uniformes distintas;
2. scorer uniforme usando o mesmo otimizador do candidato;
3. frequência histórica usando o mesmo otimizador;
4. ensemble candidato;
5. rótulos embaralhados como controle negativo.

Orçamento, relógio, sementes e conjuntos de candidatos devem ser equivalentes entre
métodos sempre que tecnicamente possível.

## Métricas

- Brier score e log loss por número;
- distribuição de acertos `0..6` por aposta;
- melhor número de acertos por carteira;
- contagens de carteiras com pelo menos `3`, `4`, `5` e `6` acertos;
- cobertura e sobreposição entre apostas;
- comparação pareada, intervalo bootstrap e correção para múltiplas hipóteses.

ROI só pode ser calculado quando prêmios/dividendos oficiais por concurso estiverem
versionados e validados.
