# Contrato de produto

## Escopo

O BonoAI trabalha apenas com os seis números principais da Bonoloto, no universo
inclusivo `1..49`.

## Entrada operacional

- orçamento em euros;
- preço unitário verificado ou explicitamente assumido;
- semente inteira;
- identificador e hash do conjunto de dados quando houver análise histórica.

## Saída operacional padrão

- dez apostas simples;
- seis números distintos e ordenados por aposta;
- nenhuma aposta duplicada;
- custo total de €5 com preço de referência de €0,50;
- semente, algoritmo e parâmetros registrados.

Se não for possível satisfazer todos os invariantes, a operação falha; nunca devolve
uma carteira parcial.

## Linguagem permitida

O projeto pode descrever cobertura, diversidade, frequência histórica e resultado de
backtesting. Não pode chamar combinações de “ruins”, prometer vantagem preditiva sem
evidência fora da amostra ou sugerir que balanceamento muda a chance matemática de uma
combinação individual.
