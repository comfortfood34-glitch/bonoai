# BonoAI — Regras de Governança e Merge

Estas regras protegem a qualidade, a rastreabilidade e a revisão do BonoAI.
Devem ser referenciadas por `AGENTS.md` e `CLAUDE.md`.

## 1. Limite de 300 linhas

- Arquivos de texto rastreados não devem exceder 300 linhas.
- A regra roda localmente no pre-commit e remotamente no GitHub Actions.
- Arquivos gerados só podem ser isentos por nome ou diretório explícito.
- Uma nova exceção exige PR separado e justificativa objetiva.
- Ultrapassar o limite exige decomposição por responsabilidade, não divisão
  artificial para contornar o verificador.

Instalação opcional do hook local:

```bash
git config core.hooksPath scripts/git-hooks
```

O hook local pode ser ignorado com `--no-verify`; a CI continua obrigatória.

## 2. CI verde antes do merge

Nenhum PR pode ser mergeado com check falhando, pendente ou ausente. Em
`Settings → Branches`, a proteção da `main` deve exigir:

- checks do workflow principal;
- check `file-length-guard`;
- branch atualizada antes do merge;
- bloqueio de push direto para `main`, quando disponível.

Um PR em modo Draft nunca está pronto para merge.

Antes de retirar o Draft:

1. todos os checks devem estar em `Success`;
2. o diff completo deve ser revisado por uma pessoa;
3. a branch deve estar atualizada com `main`;
4. resultados declarados no PR devem corresponder aos logs da CI.

## 3. Autorizações reservadas a humanos

Agentes podem criar branch, executar validações, fazer commit, push e abrir
PR quando houver autorização para essas ações. Um agente não deve:

- retirar um PR do modo Draft;
- fazer merge;
- fazer push direto em `main`;
- usar force-push;
- alterar proteção de branch.

Cada ação acima exige instrução humana explícita e específica. Aprovação
genérica de uma etapa anterior não autoriza etapas posteriores.

## 4. Proveniência do código

Commits produzidos materialmente por agentes devem declarar os agentes
participantes por trailers `Co-Authored-By`, quando a plataforma oferecer
uma identidade válida para isso.

Quando mais de um agente participar materialmente, os participantes devem
ser declarados. A identidade Git do ambiente não substitui essa informação.

Não se deve reescrever um commit já publicado apenas para acrescentar um
trailer ausente. Nesse caso:

1. registrar a autoria real na descrição do PR;
2. aplicar a regra corretamente nos commits seguintes;
3. nunca usar force-push apenas para corrigir metadados históricos.

Ferramentas que apenas revisaram ou executaram testes não precisam ser
declaradas como coautoras, mas podem ser mencionadas na descrição do PR.

## 5. Revisão do conteúdo

Resumo, cobertura e quantidade de testes declarados por um agente são
alegações até serem confirmados pela CI e pela revisão.

Antes do merge:

- revisar arquivos de domínio, contratos, persistência e segurança;
- confirmar testes, lint, tipagem e cobertura nos logs reais;
- verificar que não há segredos, `.env`, tokens ou arquivos temporários;
- confirmar que o escopo corresponde ao título e à descrição do PR;
- confirmar que nenhuma validação foi relaxada para fazer a CI passar.

Busca textual de segredos é apenas triagem e não substitui revisão:

```bash
git diff main...HEAD | grep -iE \
  "api[_-]?key|secret|token|password"
```

## 6. Separação de escopo

Mudanças de governança, produto e infraestrutura devem permanecer em PRs
separados quando não forem necessárias entre si. Alterar uma regra para
acomodar o mesmo PR que viola essa regra é proibido.

## Checklist de saída do Draft

- [ ] Todos os checks estão em `Success`
- [ ] `file-length-guard` está em `Success`
- [ ] Branch atualizada com `main` e sem conflitos
- [ ] Diff completo revisado por uma pessoa
- [ ] Métricas do PR confirmadas nos logs reais
- [ ] Nenhum segredo ou arquivo temporário
- [ ] Escopo do PR está correto
- [ ] Proveniência do código está documentada
