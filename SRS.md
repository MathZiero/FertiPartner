# Documento de Requisitos de Software — FertiPartner

## 1. Visão Geral

### 1.1. Nome do projeto

**FertiPartner**
Nome provisório para uma plataforma de inteligência e visualização de dados sobre o mercado de fertilizantes.

### 1.2. Descrição do sistema

O FertiPartner será uma plataforma web destinada à centralização, organização, integração e visualização de informações relacionadas ao setor global de fertilizantes.

O sistema reunirá dados provenientes de diferentes fontes públicas e especializadas, permitindo a consulta integrada de indicadores relacionados a:

* produção global;
* consumo e demanda;
* importação e exportação;
* fluxos comerciais internacionais;
* preços;
* oferta;
* sazonalidade;
* capacidade produtiva;
* participação de países no mercado;
* dependência comercial;
* mercado brasileiro;
* tendências e indicadores históricos.

A principal característica do sistema será a organização das informações **por fertilizante**.

Por exemplo, ao acessar a página da ureia, o usuário deverá encontrar, em uma única interface, informações históricas e atuais sobre a produção global do produto, principais países produtores, exportadores e importadores, evolução dos preços, comércio internacional, indicadores relacionados à oferta e demanda, sazonalidade e participação do Brasil nesse mercado.

O sistema não terá como objetivo inicial realizar operações de compra, venda ou negociação de fertilizantes. Seu propósito será atuar como uma **plataforma de inteligência de mercado baseada em dados**.

---

# 2. Problema

As informações sobre o mercado de fertilizantes encontram-se distribuídas entre diferentes organizações, bases de dados, relatórios e fontes estatísticas.

Um usuário interessado em analisar determinado fertilizante pode precisar consultar separadamente dados sobre:

* produção em uma fonte;
* comércio internacional em outra;
* preços em outra;
* importações brasileiras em outra;
* sazonalidade em diferentes bases agrícolas;
* fatores econômicos em fontes externas.

Essa fragmentação dificulta a análise integrada do mercado.

Além disso, dados provenientes de diferentes fontes podem possuir:

* unidades diferentes;
* frequências temporais diferentes;
* classificações distintas para produtos;
* granularidades geográficas diferentes;
* períodos históricos distintos.

O problema central que o sistema pretende resolver é:

> Centralizar e integrar informações dispersas sobre o mercado de fertilizantes, permitindo a exploração dos dados a partir de uma visão orientada por produto, país, período e indicador.

---

# 3. Objetivo do sistema

O objetivo principal do FertiPartner é fornecer uma plataforma centralizada para consulta e análise de informações relacionadas ao mercado de fertilizantes.

O sistema deverá permitir que o usuário responda perguntas como:

* Quais são os maiores produtores mundiais de ureia?
* Como a produção global de determinado fertilizante evoluiu ao longo do tempo?
* Quais países são os maiores exportadores?
* Quais países são mais dependentes da importação?
* Quais são os principais fluxos comerciais entre países?
* Como o preço de determinado fertilizante evoluiu?
* Quais períodos apresentam maior sazonalidade?
* Qual é a participação do Brasil no mercado global?
* De quais países o Brasil importa determinado fertilizante?
* Como produção, comércio e preços evoluíram ao longo do tempo?
* Existem tendências ou mudanças relevantes no comportamento do mercado?

Em versões futuras, o sistema poderá incluir análises mais avançadas, como:

* previsão de preços;
* previsão de demanda;
* detecção de anomalias;
* indicadores compostos de oferta e demanda;
* análise de correlação entre variáveis;
* geração automática de insights.

---

# 4. Escopo do sistema

## 4.1. Escopo inicial

A primeira versão do sistema deverá contemplar a coleta, armazenamento, integração e visualização de dados relacionados aos principais fertilizantes e nutrientes agrícolas.

Inicialmente, o sistema deverá priorizar produtos como:

* Ureia;
* Amônia;
* MAP;
* DAP;
* Cloreto de Potássio — KCl/MOP;
* fertilizantes nitrogenados;
* fertilizantes fosfatados;
* fertilizantes potássicos;
* formulações NPK, quando houver disponibilidade de dados adequados.

O sistema deverá ser desenvolvido de forma extensível, permitindo a inclusão futura de novos produtos.

---

## 4.2. Fora do escopo inicial

Os seguintes recursos não fazem parte obrigatoriamente da primeira versão:

* compra e venda de fertilizantes;
* marketplace;
* processamento de pagamentos;
* negociação entre fornecedores e compradores;
* gestão de estoque de empresas;
* gestão logística;
* rastreamento de entregas;
* sistema ERP;
* previsão baseada em Machine Learning como requisito obrigatório.

Essas funcionalidades poderão ser avaliadas futuramente, mas não fazem parte do núcleo inicial do projeto.

---

# 5. Usuários

## 5.1. Usuário visitante

Usuário interessado em consultar informações públicas sobre o mercado de fertilizantes.

Poderá:

* navegar pelos fertilizantes disponíveis;
* consultar indicadores;
* visualizar gráficos;
* comparar períodos;
* consultar informações sobre países;
* explorar dados históricos.

---

## 5.2. Usuário analista

Usuário interessado em realizar análises mais detalhadas.

Poderá utilizar recursos como:

* filtros avançados;
* comparação entre fertilizantes;
* comparação entre países;
* seleção de períodos;
* visualização de múltiplos indicadores;
* exploração de relações entre dados.

---

## 5.3. Administrador

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

# 6. Organização da plataforma

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

# 7. Requisitos Funcionais

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

# 8. Requisitos de Dados

## RD01 — Entidade Fertilizante

O sistema deverá possuir uma entidade central para representar fertilizantes.

Campos iniciais:

```text
id
name
category
description
nitrogen_percentage
phosphorus_percentage
potassium_percentage
```

Os campos de composição deverão ser opcionais, pois nem todos os produtos serão representados da mesma forma.

---

## RD02 — Entidade País

O sistema deverá possuir uma entidade para representar países.

Campos sugeridos:

```text
id
name
iso_code
region
subregion
```

A utilização de códigos padronizados deverá ser priorizada para facilitar a integração entre datasets.

---

## RD03 — Produção

Os registros de produção deverão conter:

```text
fertilizer_id
country_id
date
quantity
unit
source_id
```

---

## RD04 — Comércio internacional

Os registros de comércio deverão conter:

```text
fertilizer_id
exporter_country_id
importer_country_id
date
quantity
quantity_unit
trade_value
currency
source_id
```

---

## RD05 — Preços

Os registros de preço deverão conter:

```text
fertilizer_id
date
region
price
currency
unit
source_id
```

---

## RD06 — Consumo e demanda

Os registros relacionados ao consumo deverão armazenar, quando disponíveis:

```text
fertilizer_id
country_id
date
quantity
unit
source_id
```

Indicadores indiretos de demanda poderão ser armazenados separadamente.

---

## RD07 — Fontes

O sistema deverá manter um catálogo de fontes.

Campos sugeridos:

```text
id
name
organization
dataset
url
update_frequency
collection_method
```

---

## RD08 — Dados brutos

Os dados coletados deverão poder ser armazenados sem transformação.

Estrutura conceitual:

```text
id
source_id
collected_at
reference_date
raw_payload
status
```

---

# 9. Requisitos Não Funcionais

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

# 10. Regras de Negócio

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

---

# 11. Arquitetura conceitual

A arquitetura geral será baseada no seguinte fluxo:

```text
FONTES DE DADOS
        │
        ▼
COLETA
        │
        ▼
CAMADA RAW
Dados originais
        │
        ▼
VALIDAÇÃO
        │
        ▼
PADRONIZAÇÃO
        │
        ▼
BANCO DE DADOS
        │
        ├── Dados operacionais
        │
        ├── Dados históricos
        │
        └── Dados analíticos
                │
                ▼
           CAMADA ANALÍTICA
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
    Indicadores Gráficos Insights
                │
                ▼
             INTERFACE
```

---

# 12. Arquitetura de dados conceitual

O sistema deverá utilizar o fertilizante como uma das entidades centrais.

```text
                 FERTILIZER
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
      PRODUCTION    TRADE       PRICES
          │           │           │
          ▼           ▼           ▼
       COUNTRY     COUNTRY      REGION
          │           │           │
          └───────────┼───────────┘
                      │
                     DATE
                      │
                      ▼
                    SOURCE
```

A estrutura deverá permitir relacionar informações utilizando dimensões comuns:

* fertilizante;
* país;
* região;
* data;
* fonte.

---

# 13. Possíveis fontes de dados

A plataforma deverá ser desenvolvida de forma independente das fontes específicas.

Inicialmente, poderão ser avaliadas fontes relacionadas a:

* produção agrícola e de fertilizantes;
* comércio internacional;
* importação e exportação;
* preços;
* consumo;
* dados brasileiros;
* indicadores econômicos.

Possíveis categorias de organizações incluem:

* organizações internacionais;
* governos;
* institutos estatísticos;
* organismos agrícolas;
* bases públicas de comércio internacional;
* instituições especializadas no mercado de fertilizantes.

Cada fonte deverá passar por avaliação quanto a:

* disponibilidade pública;
* licença de uso;
* frequência de atualização;
* granularidade;
* cobertura histórica;
* método de acesso;
* confiabilidade;
* compatibilidade com o modelo de dados.

---

# 14. Indicadores iniciais

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

# 15. Evolução futura

Após a consolidação da base de dados e da plataforma de visualização, poderão ser desenvolvidos recursos analíticos adicionais.

## 15.1. Previsão

Possíveis previsões:

* preços;
* importações;
* demanda;
* produção.

A implementação deverá começar por modelos de referência simples antes da utilização de modelos complexos.

Exemplo:

```text
Baseline
    ↓
Modelos estatísticos
    ↓
Avaliação
    ↓
Modelos multivariados
    ↓
Machine Learning, se justificável
```

---

## 15.2. Análise de correlação

O sistema poderá permitir investigar relações entre variáveis.

Exemplo:

```text
Preço da Ureia
        │
        ├── Produção global
        ├── Exportações
        ├── Importações brasileiras
        ├── Taxa de câmbio
        └── Outros indicadores relevantes
```

---

## 15.3. Índices compostos

Poderão ser desenvolvidos índices próprios da plataforma.

Exemplos:

* índice de pressão de oferta;
* índice de pressão de demanda;
* índice de dependência externa;
* índice de concentração de fornecedores;
* índice de volatilidade de preços.

Todo índice deverá possuir metodologia documentada.

---

## 15.4. Detecção de anomalias

O sistema poderá identificar comportamentos incomuns.

Exemplos:

* aumento abrupto de preço;
* queda incomum na exportação;
* crescimento atípico das importações;
* alteração significativa na participação de um país.

---

# 16. MVP

A primeira versão funcional deverá priorizar a construção da infraestrutura de dados.

## Funcionalidades do MVP

* catálogo de fertilizantes;
* seleção de fertilizante;
* página individual do fertilizante;
* produção histórica;
* importação;
* exportação;
* preços;
* principais países;
* filtros por período;
* filtros por país;
* identificação da fonte;
* gráficos históricos;
* atualização automatizada de pelo menos uma ou mais fontes;
* armazenamento de dados brutos;
* banco de dados estruturado.

O fluxo esperado será:

```text
Usuário
   │
   ▼
Seleciona "Ureia"
   │
   ▼
Visualiza visão geral
   │
   ├── Produção
   ├── Comércio
   ├── Preços
   ├── Brasil
   └── Histórico
```

---

# 17. Critérios de sucesso

O projeto poderá ser considerado funcionalmente bem-sucedido quando for capaz de:

1. Integrar dados provenientes de múltiplas fontes.
2. Organizar informações utilizando uma estrutura comum.
3. Permitir navegação por fertilizante.
4. Apresentar séries históricas de indicadores relevantes.
5. Permitir comparação entre países.
6. Apresentar dados de comércio internacional.
7. Manter a rastreabilidade das fontes.
8. Automatizar parte do processo de atualização.
9. Permitir a expansão futura para novos fertilizantes e indicadores.
10. Transformar dados dispersos em uma interface integrada de exploração e análise.

---

# 18. Visão futura

A evolução do projeto poderá seguir o seguinte caminho:

```text
FASE 1
Coleta e integração de dados
        │
        ▼
FASE 2
Visualização e exploração
        │
        ▼
FASE 3
Indicadores e análises
        │
        ▼
FASE 4
Correlação e inteligência de mercado
        │
        ▼
FASE 5
Previsões e modelos analíticos
```

A visão de longo prazo do projeto é criar uma plataforma especializada em inteligência de dados sobre fertilizantes, capaz de conectar diferentes dimensões do mercado em uma única interface.

O valor central do sistema estará na transformação de:

```text
Dados dispersos
        ↓
Coleta
        ↓
Padronização
        ↓
Integração
        ↓
Histórico
        ↓
Visualização
        ↓
Análise
        ↓
Inteligência de mercado
```

A plataforma deverá priorizar a qualidade, rastreabilidade e integração dos dados antes da implementação de funcionalidades avançadas de previsão ou Machine Learning. A camada analítica deverá ser construída sobre uma base histórica confiável e metodologicamente consistente.
