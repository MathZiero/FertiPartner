# 1. Visão Geral

## 1.1. Nome do projeto

**FertiPartner**
Nome provisório para uma plataforma de inteligência e visualização de dados sobre o mercado de fertilizantes.

## 1.2. Descrição do sistema

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

# 5. Evolução futura

Após a consolidação da base de dados e da plataforma de visualização, poderão ser desenvolvidos recursos analíticos adicionais.

## 5.1. Previsão

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

## 5.2. Análise de correlação

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

## 5.3. Índices compostos

Poderão ser desenvolvidos índices próprios da plataforma.

Exemplos:

* índice de pressão de oferta;
* índice de pressão de demanda;
* índice de dependência externa;
* índice de concentração de fornecedores;
* índice de volatilidade de preços.

Todo índice deverá possuir metodologia documentada.

---

## 5.4. Detecção de anomalias

O sistema poderá identificar comportamentos incomuns.

Exemplos:

* aumento abrupto de preço;
* queda incomum na exportação;
* crescimento atípico das importações;
* alteração significativa na participação de um país.

---

# 6. MVP

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

# 7. Critérios de sucesso

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

# 8. Visão futura

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
