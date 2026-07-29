# Contrato de dados

## Registro canônico de concurso

Campos mínimos:

| Campo | Regra |
|---|---|
| `contest_id` | Identificador não vazio e único |
| `held_on` | Data oficial do sorteio |
| `n1..n6` | Inteiros distintos de 1 a 49, em ordem crescente |
| `complementary` | Inteiro de 1 a 49, fora dos seis números, quando disponível |
| `reintegro` | Inteiro de 0 a 9, quando disponível |
| `source_url` | Endereço exato da origem |
| `retrieved_at_utc` | Instante de coleta em UTC |
| `source_sha256` | Hash do conteúdo bruto |

## Autoridade e reconciliação

1. SELAE é a fonte canônica.
2. Lotoideas pode servir como bootstrap histórico, identificado como fonte auxiliar.
3. Um valor divergente para o mesmo concurso gera erro de conflito e relatório.
4. Duplicatas idênticas podem ser consolidadas sem perda de proveniência.
5. Arquivos brutos são somente leitura depois da ingestão.

## Identidade e atualização oficial

- Identidade estável: `bonoloto:AAAA-MM-DD`.
- A Bonoloto possui no máximo um resultado por data; uma segunda combinação para a mesma
  identidade é conflito.
- O RSS oficial
  `https://www.loteriasyapuestas.es/es/bonoloto/resultados/.formatoRSS` é usado para
  atualização incremental.
- O RSS contém resultados recentes e não substitui o bootstrap histórico.
- Cada resposta RSS é arquivada byte a byte antes da reconciliação canônica.

## Qualidade

A ingestão é atômica: ou todo lote validado é promovido, ou nenhum registro é
incorporado. Linhas rejeitadas ficam em relatório, nunca somem silenciosamente.
