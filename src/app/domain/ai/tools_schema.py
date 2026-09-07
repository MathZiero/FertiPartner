"""Esquemas de declaração de ferramentas (Tools / Function Calling) para o Google Gemini."""

from typing import Any

GEMINI_TOOLS_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "get_fertilizer_technical_spec",
        "description": "Obtém a ficha técnica agronômica detalhada de um fertilizante: fórmula química, NCM, teores nutricionais de garantia (N%, P2O5%, K2O%, S%), recomendações de solo, ponto crítico de umidade relativa (PCUR) e cuidados de armazenagem.",
        "parameters": {
            "type": "object",
            "properties": {
                "fertilizer_name": {
                    "type": "string",
                    "description": "Nome do fertilizante (ex: 'Ureia', 'MAP', 'DAP', 'KCl', 'Sulfato de Amônio', 'Superfosfato Triplo').",
                },
            },
            "required": ["fertilizer_name"],
        },
    },
    {
        "name": "get_price_trends",
        "description": "Obtém as cotações históricas internacionais e nacionais (CFR Portos Brasileiros / Paranaguá, FOB Báltico, FOB Marrocos) de um fertilizante específico em USD por tonelada métrica.",
        "parameters": {
            "type": "object",
            "properties": {
                "fertilizer_name": {
                    "type": "string",
                    "description": "Nome do fertilizante a consultar (ex: 'Ureia', 'Fosfato Monoamônico (MAP)', 'Cloreto de Potássio (KCl / MOP)').",
                },
            },
            "required": ["fertilizer_name"],
        },
    },
    {
        "name": "get_trade_and_import_flows",
        "description": "Obtém os fluxos reais de comércio bilateral internacional (origens exportadoras para o Brasil, volumes em toneladas métricas e valores CIF/FOB em USD).",
        "parameters": {
            "type": "object",
            "properties": {
                "fertilizer_name": {
                    "type": "string",
                    "description": "Nome do fertilizante (ex: 'Cloreto de Potássio (KCl / MOP)', 'Ureia', 'Fosfato Monoamônico (MAP)').",
                },
                "flow_type": {
                    "type": "string",
                    "description": "Tipo de fluxo: 'IMPORT' (importações brasileiras) ou 'EXPORT' (exportações globais). Padrão é 'IMPORT'.",
                },
            },
            "required": ["fertilizer_name"],
        },
    },
    {
        "name": "get_brazil_supply_balance",
        "description": "Obtém o balanço físico nacional de abastecimento de fertilizantes no Brasil: consumo aparente anual, produção doméstica, importações totais e taxa percentual de dependência externa.",
        "parameters": {
            "type": "object",
            "properties": {
                "fertilizer_name": {
                    "type": "string",
                    "description": "Nome do fertilizante (ex: 'Ureia', 'MAP', 'DAP', 'Cloreto de Potássio', 'Sulfato de Amônio'). Deixe em branco para todos.",
                },
            },
        },
    },
    {
        "name": "get_recent_news_7d",
        "description": "Obtém as notícias setoriais coletadas em tempo real nos últimos 7 dias (168 horas) com título, fonte jornalística, data relativa, resumo e categorização de mercado.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Filtro por tópico: 'FRETE / LOGÍSTICA', 'PRODUÇÃO', 'CONSUMO / DEMANDA', 'PREÇOS / MERCADO', 'GEOPOLÍTICA / COMÉRCIO' ou 'TODOS'.",
                },
                "nutrient": {
                    "type": "string",
                    "description": "Filtro por nutriente: 'Nitrogenados (N)', 'Fosfatados (P)', 'Potássicos (K)' ou 'TODOS'.",
                },
            },
        },
    },
    {
        "name": "get_market_sentiment_barometers",
        "description": "Obtém o diagnóstico quantitativo dos 5 barômetros de análise de sentimento setorial dos últimos 7 dias (pontuação de -10.0 a +10.0 pts, classificação 'Melhorando'/'Estável'/'Piorando' e drivers de mercado).",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]
