# 1. Arquitetura conceitual

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

# 2. Possíveis fontes de dados

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
