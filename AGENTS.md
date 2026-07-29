# AGENTS.md

Estas regras são obrigatórias para qualquer agente ou contribuidor que altere o BonoAI.

## Missão

Construir um pipeline científico, auditável e reproduzível para a Bonoloto. O sistema
analisa, compara e organiza carteiras; não promete prever um processo aleatório.

## Invariantes de produto

1. O escopo é exclusivamente a Bonoloto: seis números distintos entre 1 e 49.
2. A operação padrão usa orçamento de €5 e produz dez apostas simples de €0,50.
3. Uma execução operacional deve produzir exatamente dez apostas distintas ou falhar.
4. Reintegro e Complementario não são alvos nem atributos dos seis números principais.
5. Nenhum texto pode afirmar que filtros alteram a probabilidade intrínseca de uma combinação.

## Invariantes de dados

1. SELAE é a autoridade canônica. Fontes auxiliares precisam de origem e hash.
2. Dados brutos são imutáveis; transformações geram novos artefatos.
3. Conflitos entre fontes falham de forma explícita. Nunca usar “último valor vence”.
4. Cada ingestão registra URL, instante UTC, SHA-256, esquema e intervalo de concursos.
5. Linhas inválidas não podem ser descartadas silenciosamente.

## Invariantes temporais

1. Para prever ou avaliar o concurso `T`, somente dados anteriores a `T` são visíveis.
2. Ajuste de hiperparâmetros e pesos usa apenas janelas internas ao passado.
3. O concurso-alvo só é revelado depois de congelados modelo, ranking e carteira.
4. Toda feature nova exige teste automático contra vazamento temporal.

## Arquitetura

- `domain`: entidades e regras puras, sem I/O.
- `application`: casos de uso e orquestração.
- `ports`: contratos para fontes, armazenamento, modelos e relógio.
- `infrastructure`: implementações externas e formatos.
- `cli`: adaptação de entrada/saída; sem regra de negócio.

Dependências apontam para dentro. Domínio não importa bibliotecas de infraestrutura ou ML.

## Fluxo de mudança

1. Ler o contrato relacionado antes de editar.
2. Registrar decisão arquitetural quando houver novo limite, fonte ou hipótese.
3. Implementar a menor fatia vertical verificável.
4. Adicionar testes, inclusive casos de falha.
5. Executar `make check`; em ambiente de desenvolvimento completo, também `make lint`
   e `make typecheck`.
6. Atualizar documentação e changelog quando o comportamento observável mudar.

## Definition of Done

Uma mudança só está pronta quando:

- respeita todos os contratos;
- possui teste de comportamento e de falha relevante;
- é determinística quando recebe a mesma semente e os mesmos dados;
- preserva proveniência e corte temporal;
- não reduz silenciosamente a carteira de dez apostas;
- passa em CI;
- não contém segredos, dados pessoais ou artefatos grandes versionados.
