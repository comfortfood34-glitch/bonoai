# ADR 0004 — Schema v2 canônico com múltiplas proveniências e fail-closed source_type

- Status: aceito
- Data: 2026-07-29

## Contexto

Schema v1 serializa um record com um único SourceProvenance. Após Marco 2, precisamos:

1. Rastrear múltiplas provenâncias para o mesmo Draw (mesma identidade, mesmos números, sources diferentes)
2. Rejeitar fail-closed: source_type desconhecido, vazio ou padrão silencioso não é aceitável
3. Preservar atomicidade: mudança de schema não compromete integridade do arquivo
4. Suportar migração determinística e idempotente de v1 → v2

## Decisão

Schema v2 normaliza o CSV para uma linha por (contest_id, source_name) — dados do Draw podem se repetir se múltiplas fontes confirmam o mesmo resultado.

### Estrutura v2

```
contest_id,held_on,n1,n2,n3,n4,n5,n6,complementary,reintegro,
source_name,source_url,retrieved_at_utc,source_sha256,source_type,schema_version
```

Mesmo cabeçalho de v1, mas semântica alterada: uma linha por proveniência.

### Carregamento v2

1. Ler CSV
2. Agrupar por contest_id
3. Validar: todas as linhas do mesmo contest_id têm Draw idêntico
4. Se divergência detectada: SourceConflictError
5. Construir CanonicalDrawRecord com `provenances: tuple[SourceProvenance, ...]`
6. Ordenação determinística: por (held_on, contest_id, source_name)

### Fail-closed source_type

- source_type obrigatório no CSV (sem .get() com default)
- Valores válidos: "official", "auxiliary", "manual"
- Vazio ou desconhecido: DataContractError
- Migração v1 → v2:
  - SELAE + URL oficial SELAE → "official"
  - Fontes em allowlist (Lotoideas, etc) → "auxiliary"
  - Outras: erro, rejeitado

### Migração v1 → v2

1. Detectar schema pelo cabeçalho
2. Se v1 (sem source_type): criar backup v1 com SHA-256
3. Aplicar regras de classificação
4. Escrever v2 temporário
5. Validar v2 (load e reconcile)
6. Renomear atômico: temp → oficial
7. Idempotência: re-executar produz mesmo resultado
8. Erro não altera v1: backup preservado

### CanonicalDrawRecord

```python
@dataclass(frozen=True)
class CanonicalDrawRecord:
    draw: Draw
    provenances: tuple[SourceProvenance, ...]

    @property
    def provenance(self) -> SourceProvenance:
        """Proveniência primária (primeira, geralmente official)."""
        return self.provenances[0]
```

## Alternativas

- Usar sidecar JSON (`draws_provenances.json`): risco de inconsistência entre dois arquivos
- Colunas fixas `provenance_0`, `provenance_1`, ... com limite: inflexível, ineficiente
- Manter v1, adicionar feature flag: complexidade, estado múltiplo

## Consequências

- Integração histórica pode rastrear múltiplas confirmações
- Conflitos detectados fail-closed, sem substituição silenciosa
- Migração v1 → v2 é determinística, testada, reversível via backup
- source_type sempre explícito, nunca silenciosamente defaultado
- Idempotência garantida: múltiplas execuções produzem estado estável
