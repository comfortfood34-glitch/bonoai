# ADR 0003 — RSS oficial SELAE para atualização incremental

- Status: aceito
- Data: 2026-07-29

## Contexto

A SELAE publica um RSS oficial da Bonoloto com os resultados recentes. O documento
inclui data, seis números, Complementario e Reintegro, mas não representa todo o
histórico desde 1988.

## Decisão

Usar o RSS oficial exclusivamente como fonte incremental. Cada resposta é arquivada
integralmente com instante UTC e SHA-256; só depois todos os itens são analisados e a
base canônica é atualizada de forma atômica.

A identidade canônica será `bonoloto:AAAA-MM-DD`. Um resultado diferente para a mesma
identidade causa `SourceConflictError`; nenhum valor substitui outro silenciosamente.

## Alternativas

- Raspar páginas HTML: mais frágil e desnecessário enquanto o RSS estiver disponível.
- Tratar o RSS como histórico completo: rejeitado porque o feed é limitado a resultados
  recentes.
- Usar apenas uma fonte auxiliar: rejeitado porque SELAE é a autoridade canônica.

## Consequências

- Atualizações diárias não precisam baixar novamente todo o histórico.
- O bootstrap histórico permanece um trabalho separado e reconciliável.
- Mudanças no layout XML falham fechadas e exigem fixture/teste atualizado.
