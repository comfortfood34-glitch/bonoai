# ADR 0002 — Limites hexagonais

- Status: aceito
- Data: 2026-07-29

## Contexto

Fontes web, formatos de arquivo e bibliotecas de ML mudam com frequência. As regras da
Bonoloto e de avaliação temporal precisam continuar testáveis sem essas dependências.

## Decisão

Entidades e invariantes ficam em `domain`; casos de uso em `application`; integrações
dependem de protocolos em `ports`; adaptadores externos ficam em `infrastructure`.

## Consequências

- Testes do núcleo não acessam rede nem disco.
- Um downloader novo não altera o domínio.
- Treinamento e inferência podem compartilhar contratos sem acoplamento a um framework.
