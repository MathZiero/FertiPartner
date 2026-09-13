"""Testes unitários para o serviço de notícias do Google News RSS."""

import pandas as pd
import pytest

from app.presentation.streamlit.services.news_service import GoogleNewsService, MOCK_FERTILIZER_NEWS


def test_fetch_fertilizer_news_returns_valid_dataframe():
    """Garante que a busca de notícias retorna um DataFrame populado com as colunas necessárias."""
    df = GoogleNewsService.fetch_fertilizer_news()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty

    required_cols = [
        "title",
        "link",
        "source",
        "published_at",
        "pub_date_relative",
        "snippet",
        "topic",
        "topic_color",
        "nutrient",
    ]
    for col in required_cols:
        assert col in df.columns, f"Coluna {col} ausente no DataFrame de notícias"


def test_categorize_article_topics():
    """Valida a categorização semântica por palavras-chave em tópicos de impacto."""
    # Frete / Logística
    topic_frete, color, nut = GoogleNewsService._categorize_article(
        "Frete marítimo de fertilizantes sobe e gera filas no porto de Paranaguá",
        "Navios enfrentam espera para descarregar cloreto de potássio.",
    )
    assert topic_frete == "FRETE / LOGÍSTICA"
    assert color == "blue"
    assert "Potássicos" in nut

    # Produção
    topic_prod, color, nut = GoogleNewsService._categorize_article(
        "Petrobras estuda reabertura de fábrica de fertilizantes para elevar produção",
        "Planta de ureia e amônia visa diminuir dependência de importações.",
    )
    assert topic_prod == "PRODUÇÃO"
    assert color == "emerald"
    assert "Nitrogenados" in nut

    # Geopolítica
    topic_geo, color, nut = GoogleNewsService._categorize_article(
        "Restrição de exportação da China e sanções afetam fornecimento de MAP",
        "Tensões geopolíticas e cotas pressionam mercado internacional.",
    )
    assert topic_geo == "GEOPOLÍTICA / COMÉRCIO"
    assert "Fosfatados" in nut

    # Preços / Cotações
    topic_price, color, nut = GoogleNewsService._categorize_article(
        "Cotações internacionais de fertilizantes registram alta no CFR Brasil",
        "Preço médio por tonelada e relação de troca com a saca de soja.",
    )
    assert topic_price == "PREÇOS / MERCADO"
    assert color == "purple"

    # Consumo / Demanda
    topic_cons, color, nut = GoogleNewsService._categorize_article(
        "Ritmo de compras do produtor rural para a safra de verão dita consumo",
        "Demanda interna de fertilizantes avança com o início do plantio do milho.",
    )
    assert topic_cons == "CONSUMO / DEMANDA"
    assert color == "amber"


def test_parse_xml_feed_parses_sample_xml():
    """Valida a extração e limpeza de elementos XML do feed RSS do Google News."""
    sample_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Google News</title>
        <item>
          <title>Producao de Ureia no Brasil tem recorde - Globo Rural</title>
          <link>https://globorural.globo.com/noticia/123</link>
          <pubDate>Mon, 07 Sep 2026 12:00:00 GMT</pubDate>
          <description>&lt;p&gt;Industria amplia fornecimento domestico de nitrogenados.&lt;/p&gt;</description>
          <source url="https://globorural.globo.com">Globo Rural</source>
        </item>
      </channel>
    </rss>
    """
    articles = GoogleNewsService._parse_xml_feed(sample_xml)
    assert len(articles) == 1
    art = articles[0]
    assert art["title"] == "Producao de Ureia no Brasil tem recorde"
    assert art["source"] == "Globo Rural"
    assert art["link"] == "https://globorural.globo.com/noticia/123"
    assert art["topic"] == "PRODUÇÃO"
    assert art["nutrient"] == "Nitrogenados (N)"
    assert "<p>" not in art["snippet"]


def test_fetch_fertilizer_news_strictly_under_180_days():
    """Garante que todas as notícias retornadas foram publicadas a no máximo 180 dias."""
    from datetime import datetime, timezone, timedelta
    df = GoogleNewsService.fetch_fertilizer_news()
    assert not df.empty
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=180)

    for _, row in df.iterrows():
        pub_str = row.get("published_at")
        assert pub_str is not None
        dt = pd.to_datetime(pub_str, utc=True)
        # Tolerância de 5 segundos para execução
        assert dt >= (cutoff - timedelta(seconds=5)), f"Notícia com data {dt} excede limite de 180 dias (cutoff: {cutoff})"


def test_analyze_sentiment_by_topic_returns_structured_metrics():
    """Garante que o barômetro de sentimento calcula os 5 tópicos com 3 classificações e pontuações."""
    df = GoogleNewsService.fetch_fertilizer_news()
    sentiments = GoogleNewsService.analyze_sentiment_by_topic(df)

    assert len(sentiments) == 5
    expected_topics = [
        "FRETE / LOGÍSTICA",
        "PRODUÇÃO",
        "CONSUMO / DEMANDA",
        "PREÇOS / MERCADO",
        "GEOPOLÍTICA / COMÉRCIO",
    ]
    for s in sentiments:
        assert s["topic"] in expected_topics
        assert s["classification"] in ["Melhorando", "Estável", "Piorando"]
        assert -10.0 <= s["score_val"] <= 10.0
        assert s["badge_color"] in ["emerald", "blue", "amber"]
        assert len(s["status_label"]) > 0
        assert "notícias" in s["status_label"] or len(s["driver"]) > 0


def test_analyze_sentiment_sensitivity_to_market_trends():
    """Valida que o algoritmo de sentimento é sensível a tendências positivas e negativas sem travar em 'Estável'."""
    test_articles = [
        # Produção altamente positiva
        {
            "title": "Governo sanciona programa de incentivo e amplia produção nacional de fertilizantes",
            "snippet": "Medida prevê estímulos e investimento recorde na expansão de fábricas e reabertura de plantas.",
            "topic": "PRODUÇÃO",
            "published_at": "2026-09-10 10:00:00",
        },
        {
            "title": "Petrobras aprova reabertura de fábrica de fertilizantes nitrogenados",
            "snippet": "Retomada industrial eleva capacidade produtiva e alivia dependência com eficiência.",
            "topic": "PRODUÇÃO",
            "published_at": "2026-09-08 12:00:00",
        },
        # Geopolítica negativa (sanções, embargos e cotas)
        {
            "title": "Sanções internacionais e controle de cotas geram risco geopolítico no abastecimento",
            "snippet": "Restrição de exportação da China e tensão no Mar Vermelho reduzem embarques de fosfatados.",
            "topic": "GEOPOLÍTICA / COMÉRCIO",
            "published_at": "2026-09-09 14:00:00",
        },
        {
            "title": "Guerra e bloqueio portuário causam prejuízo e encarecem suprimentos globais",
            "snippet": "Embargo e restrições alfandegárias afetam comércio de fertilizantes.",
            "topic": "GEOPOLÍTICA / COMÉRCIO",
            "published_at": "2026-09-07 09:00:00",
        },
        # Frete neutro/sem viés
        {
            "title": "Movimentação portuária de granéis no Porto de Santos",
            "snippet": "Dados gerais sobre navios e logística de cargas no porto.",
            "topic": "FRETE / LOGÍSTICA",
            "published_at": "2026-09-06 15:00:00",
        },
        # Preços com sinal positivo predominante (3 matérias de alívio/queda de custos) diluídas em matérias neutras
        {
            "title": "Poder de compra de fertilizantes melhorou 7% com queda de preços",
            "snippet": "Relação de troca mais favorável traz alívio aos custos de insumos do produtor.",
            "topic": "PREÇOS / MERCADO",
            "published_at": "2026-09-10 09:00:00",
        },
        {
            "title": "Cotações em queda aliviam custos na aquisição de nitrogenados",
            "snippet": "Preços mais acessíveis no porto de Paranaguá beneficiam compras da safra.",
            "topic": "PREÇOS / MERCADO",
            "published_at": "2026-09-09 11:00:00",
        },
        {
            "title": "Desconto nas cotações e barateamento de insumos agrícolas",
            "snippet": "Mercado registra alívio nas cotações internacionais de adubos.",
            "topic": "PREÇOS / MERCADO",
            "published_at": "2026-09-08 14:00:00",
        },
        {
            "title": "Relatório semanal de cotações de fertilizantes",
            "snippet": "Resumo dos valores de mercado sem oscilações expressivas.",
            "topic": "PREÇOS / MERCADO",
            "published_at": "2026-09-07 10:00:00",
        },
        {
            "title": "Acompanhamento de preços de fertilizantes em reais por tonelada",
            "snippet": "Tabela de referência das transações comerciais registradas.",
            "topic": "PREÇOS / MERCADO",
            "published_at": "2026-09-06 12:00:00",
        },
        {
            "title": "Divulgação dos índices de preços de insumos",
            "snippet": "Indicadores econômicos para planejamento agrícola.",
            "topic": "PREÇOS / MERCADO",
            "published_at": "2026-09-05 08:00:00",
        },
    ]
    df_synthetic = pd.DataFrame(test_articles)
    sentiments = GoogleNewsService.analyze_sentiment_by_topic(df_synthetic)
    sent_dict = {s["topic"]: s for s in sentiments}

    # Produção deve ser claramente positiva
    assert sent_dict["PRODUÇÃO"]["classification"] == "Melhorando"
    assert sent_dict["PRODUÇÃO"]["score_val"] > 1.5

    # Geopolítica deve ser claramente negativa
    assert sent_dict["GEOPOLÍTICA / COMÉRCIO"]["classification"] == "Piorando"
    assert sent_dict["GEOPOLÍTICA / COMÉRCIO"]["score_val"] < -1.5

    # Preços deve ser Melhorando mesmo com presença de notícias neutras no tema
    assert sent_dict["PREÇOS / MERCADO"]["classification"] == "Melhorando"
    assert sent_dict["PREÇOS / MERCADO"]["score_val"] > 1.5

    # Frete deve ser neutro / estável
    assert sent_dict["FRETE / LOGÍSTICA"]["classification"] == "Estável"


def test_fetch_fertilizer_news_is_sorted_by_recency():
    """Garante que as notícias são ordenadas decrescentemente (mais recentes no topo)."""
    df = GoogleNewsService.fetch_fertilizer_news()
    assert not df.empty
    dates = pd.to_datetime(df["published_at"], utc=True)
    assert dates.is_monotonic_decreasing, "Notícias devem estar ordenadas das mais recentes para as mais antigas"


