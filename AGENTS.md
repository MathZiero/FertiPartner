# Agent Guide

## Context

Antes de iniciar uma tarefa:

1. Leia este arquivo.
2. Leia o README.
3. Identifique os documentos relevantes em `docs/`.
4. Verifique `plans/active/` para trabalhos relacionados.

## Planning

Para tarefas pequenas, um plano pode permanecer apenas no contexto
da sessão.

Para tarefas que:
- envolvam múltiplos componentes;
- exijam várias etapas;
- possam durar mais de uma sessão;
- envolvam decisões arquiteturais;

crie um plano em `plans/active/`.

## Plan lifecycle

Um plano deve registrar:

- objetivo;
- escopo;
- abordagem;
- etapas;
- decisões;
- progresso;
- problemas encontrados.

Atualize o plano durante a execução.

Quando a tarefa estiver concluída, mova o plano para
`plans/completed/`.

## TDD

Antes de implementar:

1. Identifique os critérios de aceitação.
2. Crie ou atualize os testes.
3. Execute os testes.
4. Implemente.
5. Execute novamente.
6. Refatore.
7. Execute a suíte completa.



## Skills

Skills são instruções especializadas que orientam o agente em tarefas ou domínios específicos. Antes de executar uma tarefa, verifique se existe uma skill relevante disponível no diretório de skills do projeto.

### Como utilizar

1. Identifique quais skills são relevantes para a tarefa atual.
2. Leia o `skill.md` da skill antes de executar a tarefa.
3. Siga as instruções, convenções e restrições definidas pela skill.
4. Se a tarefa envolver múltiplos domínios, utilize todas as skills relevantes e respeite as relações entre elas.
5. Skills relacionadas devem ser tratadas como complementares, não como instruções isoladas. Quando uma skill referenciar outra, consulte a skill referenciada para preservar o fluxo definido entre elas.
6. Não invente procedimentos quando uma skill existente já define o procedimento apropriado.
7. Se nenhuma skill existente for aplicável, siga as instruções gerais deste `AGENTS.md` e as convenções do projeto.

### Localização

As skills do projeto ficam em:

```text
skills/
├── <skill>/
│   └── skill.md
└── ...
```

Ao procurar uma skill, examine primeiro os nomes e descrições dos diretórios disponíveis. Para uma tarefa relacionada a uma área específica, leia o `skill.md` correspondente antes de agir.

Exemplo:

```text
skills/
├── tdd/
│   └── skill.md
├── ci-cd/
│   └── skill.md
└── ...
```

Para uma tarefa de desenvolvimento orientado a testes, consulte `skills/tdd/skill.md`. Se a tarefa também envolver integração contínua ou deploy, consulte `skills/ci-cd/skill.md`.

### Regra de precedência

As skills complementam este `AGENTS.md`. Em caso de conflito, as instruções de maior prioridade definidas pelo sistema do projeto prevalecem. Uma skill não deve substituir regras gerais do projeto sem que isso esteja explicitamente definido.

### Mantendo Skills Atualizadas
Se você perceber que uma skill está desatualizada ou precisa de melhorias, sinta-se à vontade para atualizá-la. No entanto, sempre que fizer alterações, execute o comando `check.sh <skill_name>` para garantir que a skill ainda esteja alinhada com as expectativas do projeto. Isso ajuda a manter a qualidade e consistência das diretrizes.


# Source Architecture

## domain/

Contém regras de negócio.
Não pode depender de infrastructure ou presentation.

## application/

Contém casos de uso.
Coordena domain e abstrações de infraestrutura.

## infrastructure/

Contém implementações de dependências externas:
banco, APIs, filesystem etc.

## presentation/

Contém interfaces externas:
API, UI e CLI.

## Dependency Rules

domain → não depende de outras camadas externas

application → depende de domain

infrastructure → implementa interfaces usadas por application

presentation → chama application

## Before modifying code

Determine primeiro qual camada é responsável pela mudança.
Não coloque lógica de negócio em presentation ou infrastructure.


## Git e Controle de Alterações

O agente pode utilizar Git para inspecionar e versionar alterações.

### Permitido sem confirmação

- `git status`
- `git diff`
- `git log`
- `git show`
- `git branch`
- `git switch`
- `git checkout`
- `git add`
- `git commit`
- comandos de teste, lint e type checking

### Requer confirmação explícita

- `git push`
- `git merge`
- `git rebase`
- `git cherry-pick`
- criação de tags

### Nunca executar automaticamente

- `git push --force`
- `git push --force-with-lease`
- `git reset --hard`
- `git clean -fd`
- comandos que descartem alterações do usuário sem confirmação

### Regras de segurança

- Nunca modificar diretamente a branch `main`.
- Preferir branches específicas para cada tarefa.
- Nunca acessar, imprimir ou expor secrets.
- Nunca utilizar credenciais de produção durante testes locais.
- Antes de uma operação potencialmente destrutiva, solicitar confirmação.
- Antes de commit, executar os testes definidos pela skill de TDD.
- Alterações devem passar pela CI definida pela skill de CI/CD antes de serem consideradas prontas para integração.

