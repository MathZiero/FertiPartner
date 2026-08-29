# Definition of Done (DoD) — FertiPartner

A **Definition of Done** estabelece os critérios mínimos de qualidade e integridade que devem ser atendidos antes que qualquer tarefa, funcionalidade ou correção seja considerada concluída.

---

## 1. Código e Implementação

- [ ] A solução atende a todos os requisitos funcionais e não funcionais descritos na especificação/tarefa.
- [ ] O código respeita os padrões arquiteturais de Clean Architecture e DDD em `src/app/`.
- [ ] Tipagem estática (Type Hints) completa em todas as novas funções e métodos.
- [ ] Nenhuma dependência externa desnecessária foi introduzida.
- [ ] Ausência de "code smells", código duplicado ou comentários temporários esquecidos (ex: `# TODO`).

---

## 2. Testes e Qualidade

- [ ] Testes unitários cobrindo as regras de negócio e casos de borda em `tests/unit/`.
- [ ] Testes de integração implementados quando há interação com I/O, banco ou fontes de dados em `tests/integration/`.
- [ ] Todos os testes da suíte passam com sucesso (`pytest`).
- [ ] Não há regressão de funcionalidades existentes.

---

## 3. Documentação e Rastreabilidade

- [ ] Se a mudança introduzir novas decisões arquiteturais relevantes, um ADR foi registrado em `docs/architecture/decisions/`.
- [ ] Documentação técnica ou de requisitos (`docs/`) atualizada, se aplicável.
- [ ] Código devidamente documentado com docstrings em funções públicas e contratos.

---

## 4. Revisão e Integração

- [ ] Revisão de código concluída.
- [ ] Pipelines de CI/CD executados e aprovados sem alertas ou falhas.
