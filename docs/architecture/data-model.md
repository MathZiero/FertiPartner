# 1. Requisitos de Dados

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

# 2. Arquitetura de dados conceitual

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
