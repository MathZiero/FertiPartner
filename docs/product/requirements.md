# 1. Usuários

## 1.1. Usuário visitante

Usuário interessado em consultar informações públicas sobre o mercado de fertilizantes.

Poderá:

* navegar pelos fertilizantes disponíveis;
* consultar indicadores;
* visualizar gráficos;
* comparar períodos;
* consultar informações sobre países;
* explorar dados históricos.

---

## 1.2. Usuário analista

Usuário interessado em realizar análises mais detalhadas.

Poderá utilizar recursos como:

* filtros avançados;
* comparação entre fertilizantes;
* comparação entre países;
* seleção de períodos;
* visualização de múltiplos indicadores;
* exploração de relações entre dados.

---

## 1.3. Administrador

Responsável pela manutenção do sistema.

Poderá:

* gerenciar fontes de dados;
* acompanhar execuções de coleta;
* verificar erros;
* atualizar mapeamentos de produtos;
* gerenciar indicadores;
* administrar usuários, caso autenticação seja implementada;
* revisar a qualidade dos dados.

---

# 2. Organização da plataforma

A plataforma deverá ser organizada em módulos principais.

```text
FertiPartner
│
├── Visão Geral do Mercado
│
├── Fertilizantes
│   ├── Ureia
│   ├── Amônia
│   ├── MAP
│   ├── DAP
│   ├── KCl
│   └── Outros
│
├── Produção Global
│
├── Comércio Internacional
│   ├── Exportações
│   ├── Importações
│   └── Fluxos Comerciais
│
├── Preços
│
├── Oferta e Demanda
│
├── Sazonalidade
│
├── Brasil
│
└── Análises
```

---

# 3. Requisitos Funcionais

## RF01 — Consulta de fertilizantes

O sistema deverá permitir a visualização de uma lista de fertilizantes disponíveis.

Cada fertilizante deverá possuir uma página própria contendo seus principais indicadores.

---

## RF02 — Perfil do fertilizante

O sistema deverá apresentar uma página de perfil para cada fertilizante.

A página deverá conter, quando houver disponibilidade de dados:

* descrição do produto;
* categoria;
* composição;
* produção global;
* principais países produtores;
* consumo;
* principais importadores;
* principais exportadores;
* preços;
* histórico;
* sazonalidade;
* informações relacionadas ao Brasil.

---

## RF03 — Consulta de produção global

O sistema deverá permitir visualizar dados históricos de produção.

A consulta deverá permitir filtros por:

* fertilizante;
* país;
* região;
* período.

O sistema deverá apresentar:

* produção total;
* evolução histórica;
* ranking de produtores;
* participação percentual dos países, quando aplicável.

---

## RF04 — Consulta de importações

O sistema deverá permitir consultar dados de importação de fertilizantes.

A consulta deverá permitir filtros por:

* fertilizante;
* país importador;
* país de origem;
* período.

O sistema deverá apresentar, quando disponível:

* quantidade importada;
* valor comercial;
* evolução histórica;
* participação por país fornecedor.

---

## RF05 — Consulta de exportações

O sistema deverá permitir consultar dados de exportação.

A consulta deverá permitir filtros por:

* fertilizante;
* país exportador;
* país de destino;
* período.

O sistema deverá apresentar:

* quantidade exportada;
* valor comercial;
* evolução histórica;
* participação no comércio global.

---

## RF06 — Visualização de fluxos comerciais

O sistema deverá permitir visualizar relações comerciais entre países.

A visualização deverá representar, quando possível:

* país de origem;
* país de destino;
* fertilizante;
* volume comercializado;
* valor comercial;
* período.

O sistema poderá utilizar visualizações como:

* mapas;
* fluxogramas;
* diagramas Sankey;
* tabelas interativas.

---

## RF07 — Consulta de preços

O sistema deverá permitir visualizar séries históricas de preços de fertilizantes.

Cada registro de preço deverá possuir, sempre que disponível:

* produto;
* data;
* região;
* preço;
* moeda;
* unidade;
* fonte.

O usuário deverá poder selecionar:

* fertilizante;
* região;
* período;
* fonte.

---

## RF08 — Conversão e padronização de unidades

O sistema deverá realizar a padronização das unidades utilizadas pelas diferentes fontes.

Sempre que possível, o sistema deverá converter dados para unidades de referência comuns.

Exemplos:

* quilogramas;
* toneladas métricas;
* dólares;
* reais;
* euros.

A aplicação deverá preservar a informação da unidade original.

---

## RF09 — Visualização histórica

O sistema deverá permitir a visualização da evolução temporal dos indicadores.

O usuário deverá poder selecionar diferentes períodos.

Exemplos:

* último ano;
* últimos cinco anos;
* últimos dez anos;
* período personalizado;
* todo o histórico disponível.

---

## RF10 — Sazonalidade

O sistema deverá apresentar indicadores de sazonalidade quando houver dados suficientes.

A análise poderá considerar:

* produção;
* importações;
* exportações;
* consumo;
* preços.

O sistema deverá permitir identificar padrões recorrentes ao longo dos meses ou períodos agrícolas.

---

## RF11 — Comparação entre países

O sistema deverá permitir comparar indicadores entre múltiplos países.

Exemplos:

```text
Ureia

Brasil × Índia × China
```

A comparação poderá envolver:

* produção;
* consumo;
* importações;
* exportações;
* participação de mercado.

---

## RF12 — Comparação entre fertilizantes

O sistema deverá permitir comparar determinados indicadores entre fertilizantes.

Exemplo:

```text
Preço

Ureia
MAP
DAP
KCl
```

A comparação deverá considerar diferenças de:

* unidade;
* composição;
* disponibilidade dos dados.

---

## RF13 — Página específica para o Brasil

O sistema deverá possuir uma área dedicada ao mercado brasileiro.

A área deverá apresentar, quando disponível:

* produção nacional;
* importações;
* exportações;
* principais países fornecedores;
* evolução histórica;
* participação no mercado global;
* preços;
* indicadores de dependência externa.

---

## RF14 — Indicadores de dependência comercial

O sistema deverá permitir calcular ou apresentar indicadores relacionados à dependência de importações.

Exemplo conceitual:

```text
Dependência externa
=
Importações
────────────
Consumo total
```

O indicador somente deverá ser calculado quando os dados necessários estiverem disponíveis e metodologicamente compatíveis.

---

## RF15 — Indicadores de participação de mercado

O sistema deverá permitir apresentar indicadores como:

* participação na produção global;
* participação nas exportações globais;
* participação nas importações globais;
* participação por país.

---

## RF16 — Filtros globais

A interface deverá disponibilizar filtros para facilitar a exploração dos dados.

Os principais filtros deverão incluir:

* fertilizante;
* país;
* região;
* período;
* indicador;
* fonte, quando necessário.

---

## RF17 — Exibição da fonte dos dados

Todo indicador apresentado deverá possuir informações sobre sua origem.

O sistema deverá permitir identificar:

* organização responsável;
* dataset;
* período de referência;
* data da coleta;
* frequência de atualização, quando disponível.

---

## RF18 — Atualização automática de dados

O sistema deverá possuir mecanismos automatizados para atualização das fontes.

A frequência de atualização deverá depender da disponibilidade de cada fonte.

Exemplos:

* diária;
* semanal;
* mensal;
* trimestral;
* anual.

---

## RF19 — Registro de execução das coletas

O sistema deverá registrar informações sobre os processos de coleta.

Cada execução deverá armazenar, quando aplicável:

* fonte;
* data e horário;
* status;
* quantidade de registros;
* mensagem de erro;
* data de referência dos dados.

---

## RF20 — Armazenamento de dados brutos

O sistema deverá preservar os dados recebidos originalmente antes das transformações.

Os dados brutos deverão permitir:

* auditoria;
* reprocessamento;
* correção de regras;
* identificação de alterações nas fontes.

---

## RF21 — Padronização de fertilizantes

O sistema deverá possuir uma camada de mapeamento entre as classificações utilizadas pelas diferentes fontes.

Exemplo conceitual:

```text
Fonte A: Urea
Fonte B: Ureia
Fonte C: Nitrogen Fertilizer
```

Quando metodologicamente possível, os dados deverão ser associados a uma entidade padronizada.

O sistema não deverá realizar associações automáticas que possam comprometer a precisão dos dados.

---

## RF22 — Dashboard global

O sistema deverá possuir uma página inicial contendo indicadores gerais do setor.

Exemplos:

* fertilizantes monitorados;
* maiores produtores;
* maiores exportadores;
* maiores importadores;
* tendências recentes de preços;
* principais alterações identificadas.

---

## RF23 — Sistema de insights

Em versões posteriores, o sistema poderá gerar insights automáticos a partir dos dados.

Exemplos:

* aumento significativo das importações;
* redução da produção;
* mudança na participação de determinado país;
* alteração incomum nos preços;
* divergência entre preço e tendência histórica.

Os insights deverão ser acompanhados pelos indicadores que justificam sua geração.

---

## RF24 — Exportação de dados

O sistema poderá permitir a exportação dos dados consultados.

Formatos inicialmente considerados:

* CSV;
* XLSX;
* JSON.

Esse requisito poderá ser priorizado após a implementação do núcleo da plataforma.

---

# 4. Indicadores iniciais

A primeira versão deverá priorizar os seguintes indicadores.

## Produção

* produção global;
* produção por país;
* crescimento da produção;
* participação global.

## Comércio

* importações;
* exportações;
* volume comercializado;
* valor comercial;
* principais parceiros comerciais;
* participação no comércio global.

## Preços

* preço histórico;
* variação;
* médias móveis;
* comparação entre regiões.

## Mercado brasileiro

* importações;
* principais países fornecedores;
* participação no comércio global;
* evolução histórica.

## Sazonalidade

* comportamento mensal ou periódico;
* padrões históricos;
* períodos de maior atividade.

---

# 5. Requisitos Não Funcionais

## RNF01 — Qualidade dos dados

O sistema deverá validar os dados antes de sua disponibilização.

As validações poderão incluir:

* valores ausentes;
* unidades inválidas;
* duplicidade;
* valores negativos incompatíveis;
* datas inválidas;
* países não reconhecidos;
* fertilizantes não mapeados.

---

## RNF02 — Rastreabilidade

Todo dado processado deverá possuir relação com sua fonte original.

Deverá ser possível identificar:

```text
Indicador
→ Dataset
→ Fonte
→ Data de coleta
→ Processo de transformação
```

---

## RNF03 — Reprodutibilidade

Os processos de transformação deverão ser reproduzíveis.

Alterações nas regras de processamento deverão permitir o reprocessamento dos dados históricos quando necessário.

---

## RNF04 — Extensibilidade

A arquitetura deverá permitir a inclusão futura de:

* novos fertilizantes;
* novas fontes;
* novos indicadores;
* novos países;
* novos modelos analíticos.

A adição de uma nova fonte não deverá exigir alterações significativas no restante da aplicação.

---

## RNF05 — Desempenho

A interface deverá responder adequadamente às consultas mais frequentes.

Indicadores utilizados repetidamente poderão ser:

* pré-calculados;
* agregados;
* armazenados em tabelas analíticas;
* armazenados em views materializadas.

---

## RNF06 — Usabilidade

A interface deverá priorizar a exploração dos dados.

O usuário deverá conseguir navegar seguindo diferentes perspectivas:

```text
Fertilizante
→ Ureia
→ Produção
→ Comércio
→ Preços
```

ou:

```text
País
→ Brasil
→ Importações
→ Fertilizantes
```

ou:

```text
Indicador
→ Exportação
→ Países
→ Fertilizante
```

---

## RNF07 — Integridade histórica

Dados históricos não deverão ser sobrescritos sem registro.

Caso uma fonte publique revisões, o sistema deverá permitir identificar:

* versão anterior;
* versão atual;
* data da atualização.

---

## RNF08 — Segurança

Caso o sistema possua autenticação futuramente, deverão ser aplicados mecanismos de:

* autenticação;
* autorização;
* controle de acesso;
* proteção de credenciais;
* armazenamento seguro de chaves de APIs.

---

# 6. Regras de Negócio

## RN01 — Fonte obrigatória

Nenhum indicador deverá ser apresentado sem identificação da fonte, exceto métricas internas explicitamente calculadas pelo próprio sistema.

---

## RN02 — Preservação da unidade original

Mesmo após conversão ou padronização, a unidade original deverá ser preservada quando possível.

---

## RN03 — Comparabilidade

O sistema não deverá comparar diretamente dados incompatíveis.

Exemplos de possíveis incompatibilidades:

* produtos diferentes tratados como equivalentes;
* toneladas métricas e outras unidades sem conversão;
* períodos temporais diferentes;
* metodologias incompatíveis.

---

## RN04 — Dados ausentes

A ausência de dados não deverá ser interpretada automaticamente como valor zero.

O sistema deverá diferenciar:

```text
0
```

de:

```text
sem dado disponível
```

---

## RN05 — Dados estimados

Quando um dado for estimado, calculado ou derivado, essa condição deverá ser identificada.

---

## RN06 — Cálculos derivados

Indicadores derivados deverão armazenar ou documentar:

* fórmula;
* variáveis utilizadas;
* período;
* metodologia.
