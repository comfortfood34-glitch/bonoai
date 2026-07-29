# Contrato temporal

Para qualquer concurso-alvo `T`, o estado de informação permitido é:

```text
features(T) = função(concursos estritamente anteriores a T)
```

É proibido:

- calcular estatísticas de `T` usando o próprio resultado de `T`;
- normalizar com parâmetros ajustados no período futuro;
- escolher modelos ou pesos usando o holdout final;
- reutilizar como “próximo concurso” uma linha supervisionada que representa o instante
  anterior ao último concurso conhecido.

Cada artefato de previsão registra `target_contest`, `cutoff`, `dataset_sha256`,
`code_version` e `seed`.
