# Contrato de dados

## Registro canônico de concurso

Um concurso canonical é imutável e requer:

- Um `Draw` único com contest_id, held_on, números (n1-n6), complementary, reintegro.
- Pelo menos uma `SourceProvenance` documentando origem, URL, coleta em UTC, SHA-256.

Campos:

| Campo | Regra |
|---|---|
| `contest_id` | Identificador não vazio e único |
| `held_on` | Data oficial do sorteio |
| `n1..n6` | Inteiros distintos de 1 a 49, em ordem crescente |
| `complementary` | Inteiro de 1 a 49, fora dos seis números, quando disponível |
| `reintegro` | Inteiro de 0 a 9, quando disponível |
| `source_name` | Nome normativo da fonte (selae, lotoideas, manual) |
| `source_url` | Endereço exato absoluto da origem (HTTP/HTTPS) |
| `retrieved_at_utc` | Instante de coleta em UTC com timezone |
| `source_sha256` | Hash SHA-256 do conteúdo bruto (64 hex) |
| `source_type` | Classificação: official, auxiliary ou manual |
| `schema_version` | Versão canônica de schema (currently 2) |

## Identidade de proveniância

Cada proveniância é identificada pelo fingerprint determinístico:
`(source_type, source_name, source_url, source_sha256)`.

Duplicatas idênticas por fingerprint são rejeitadas na CSV. Múltiplas provenâncias
para o mesmo concurso são ordenadas determinísticamente pelo fingerprint.

Um registro de concurso não pode ter provenâncias duplicadas por fingerprint.

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

## Auditoria

Auditoria coleta todos os achados e conflitos sem interrupção:

- **Duplicatas**: proveniâncias idênticas por fingerprint (info).
- **Conflitos**: concursos com resultados diferentes de fontes diferentes (error).
- **Vazios**: repositório sem registros em nenhuma fonte (warning).
- **Distribuição**: contagem de provenâncias por source_type.
- **Período**: primeira e última data no repositório.

Exit codes:
- `0`: auditoria aprovada (warnings informativos permitidos).
- `1`: conflitos encontrados ou error findings.
- `2`: erro operacional (I/O, validação, etc).

## Qualidade

A ingestão é atômica: ou todo lote validado é promovido, ou nenhum registro é
incorporado. Linhas rejeitadas ficam em relatório, nunca somem silenciosamente.

A migração de schema (v1 → v2) é idempotente: múltiplas execuções não alteram
o resultado. Backup do arquivo original é preservado.

Validação completa acontece antes de qualquer modificação do armazenamento:
dados inválidos são rejeitados sem deixar temporários.
