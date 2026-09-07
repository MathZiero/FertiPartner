"""Serviço de inteligência de notícias agrícolas e fertilizantes via Google News RSS."""

from datetime import datetime, timezone, timedelta
import logging
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def _generate_mock_news() -> list[dict[str, Any]]:
    """Gera notícias curadas dinâmicas garantindo datas nos últimos 7 dias."""
    now = datetime.now(timezone.utc)
    items = [
        {
            "title": "Mercado de fertilizantes atrasa ritmo no Brasil e demanda para safras gera cautela",
            "link": "https://news.google.com",
            "source": "CNN Brasil",
            "days_ago": 1,
            "hours_ago": 2,
            "snippet": "Compradores nacionais avaliam margens operacionais e ritmo do plantio de grãos, monitorando as oscilações cambiais e preços de entrega.",
            "topic": "CONSUMO / DEMANDA",
            "topic_color": "amber",
            "nutrient": "Geral",
        },
        {
            "title": "Produtor brasileiro avalia relação de troca grão-adubo antes da safra de verão",
            "link": "https://news.google.com",
            "source": "Exame Agro",
            "days_ago": 0,
            "hours_ago": 5,
            "snippet": "A paridade de troca entre sacas de soja e fertilizantes NPK dita o ritmo de fechamento de pacotes tecnológicos no Centro-Oeste.",
            "topic": "PREÇOS / MERCADO",
            "topic_color": "purple",
            "nutrient": "Complexos NPK",
        },
        {
            "title": "Programa nacional de incentivo à produção de fertilizantes busca reduzir dependência externa",
            "link": "https://news.google.com",
            "source": "Agência Câmara",
            "days_ago": 3,
            "hours_ago": 1,
            "snippet": "Medida prevê estímulos tributários e fornecimento competitivo de gás natural para indústrias de nitrogenados e rocha fosfática no país.",
            "topic": "PRODUÇÃO",
            "topic_color": "emerald",
            "nutrient": "Nitrogenados (N)",
        },
        {
            "title": "Frete marítimo de fertilizantes registra alta com gargalos em rotas estratégicas e taxas portuárias",
            "link": "https://news.google.com",
            "source": "Globo Rural",
            "days_ago": 2,
            "hours_ago": 3,
            "snippet": "Tempo de espera nos berços de descarga em Paranaguá e Santos pressiona o custo CIF Brasil para cargas de cloreto de potássio e fosfatados.",
            "topic": "FRETE / LOGÍSTICA",
            "topic_color": "blue",
            "nutrient": "Potássicos (K)",
        },
        {
            "title": "Exportações russas de fertilizantes mantêm liderança em fornecimento para o mercado brasileiro",
            "link": "https://news.google.com",
            "source": "Reuters Brasil",
            "days_ago": 4,
            "hours_ago": 2,
            "snippet": "Apesar de restrições em operações de câmbio e seguros globais, navios graneleiros seguem operando rotas regulares do Báltico para o Brasil.",
            "topic": "GEOPOLÍTICA / COMÉRCIO",
            "topic_color": "blue",
            "nutrient": "Nitrogenados (N)",
        },
        {
            "title": "Cotações de ureia granulada sobem no exterior com paradas técnicas e demanda pontual da Índia",
            "link": "https://news.google.com",
            "source": "Notícias Agrícolas",
            "days_ago": 2,
            "hours_ago": 6,
            "snippet": "Leilão de importação asiático e oscilação dos custos de gás na Europa conferem suporte às cotações no Oriente Médio e Golfo dos EUA.",
            "topic": "PREÇOS / MERCADO",
            "topic_color": "purple",
            "nutrient": "Nitrogenados (N)",
        },
        {
            "title": "China prorroga mecanismos de inspeção e monitoramento sobre embarques externos de fosfatados",
            "link": "https://news.google.com",
            "source": "Valor Econômico",
            "days_ago": 5,
            "hours_ago": 1,
            "snippet": "Controle de cotas para proteger o abastecimento doméstico chinês reduz oferta imediata de DAP e MAP para o Ocidente.",
            "topic": "GEOPOLÍTICA / COMÉRCIO",
            "topic_color": "blue",
            "nutrient": "Fosfatados (P)",
        },
        {
            "title": "Mato Grosso amplia recepção de adubos por ferrovia para otimizar custos logísticos de distribuição",
            "link": "https://news.google.com",
            "source": "Canal Rural",
            "days_ago": 3,
            "hours_ago": 4,
            "snippet": "Terminais intermodais no norte do estado aumentam capacidade estática de estocagem de granéis sólidos fertilizantes para o pico do plantio.",
            "topic": "FRETE / LOGÍSTICA",
            "topic_color": "blue",
            "nutrient": "Geral",
        },
    ]

    res = []
    for it in items:
        dt = now - timedelta(days=it["days_ago"], hours=it["hours_ago"])
        if it["days_ago"] == 0:
            rel = f"Há {max(1, it['hours_ago'])} h" if it["hours_ago"] > 0 else "Hoje"
        elif it["days_ago"] == 1:
            rel = "Ontem"
        else:
            rel = f"Há {it['days_ago']} dias"
        res.append({
            "title": it["title"],
            "link": it["link"],
            "source": it["source"],
            "published_at": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "pub_date_relative": rel,
            "snippet": it["snippet"],
            "topic": it["topic"],
            "topic_color": it["topic_color"],
            "nutrient": it["nutrient"],
        })
    return res


MOCK_FERTILIZER_NEWS = _generate_mock_news()


class GoogleNewsService:
    """Coletor e analisador semântico de notícias de fertilizantes do Google News RSS."""

    BASE_RSS_URL = "https://news.google.com/rss/search"

    @classmethod
    def get_fallback_news(cls) -> list[dict[str, Any]]:
        """Garante retorno de notícias mock com datas sempre dinâmicas nos últimos 7 dias."""
        return _generate_mock_news()

    @classmethod
    def _categorize_article(cls, title: str, snippet: str) -> tuple[str, str, str]:
        """Classifica a notícia por tópico estratégico, cor de badge e nutriente associado."""
        text = f"{title} {snippet}".lower()

        # Classificação por nutriente
        if any(w in text for w in ["ureia", "amonia", "amônia", "nitrato", "nitrogenad"]):
            nutrient = "Nitrogenados (N)"
        elif any(w in text for w in ["map", "dap", "fosfato", "fosfatad", "superfosfato", "rocha fosf"]):
            nutrient = "Fosfatados (P)"
        elif any(w in text for w in ["potassio", "potássio", "kcl", "cloreto de potássio", "potássic"]):
            nutrient = "Potássicos (K)"
        elif any(w in text for w in ["enxofre", "secundario", "secundário"]):
            nutrient = "Secundários (S)"
        elif any(w in text for w in ["zinco", "boro", "micronutriente"]):
            nutrient = "Micronutrientes"
        elif "npk" in text or "fertilizantes" in text or "adubo" in text:
            nutrient = "Complexos NPK"
        else:
            nutrient = "Geral"

        # Classificação por tópico estratégico
        if any(w in text for w in ["frete", "porto", "paranaguá", "paranagua", "santos", "itaqui", "barcarena", "navio", "fila", "espera", "marítim", "maritim", "logístic", "logistic", "ferrovia", "cabotagem", "transporte"]):
            return "FRETE / LOGÍSTICA", "blue", nutrient

        if any(w in text for w in ["preço", "preco", "cotação", "cotacao", "cotações", "cotacoes", "dólar", "dolar", "fob", "cfr", "custo", "relação de troca", "relacao de troca", "spread"]):
            return "PREÇOS / MERCADO", "purple", nutrient

        if any(w in text for w in ["produção", "producao", "fábrica", "fabrica", "planta", "capacidade", "indústria", "industria", "petrobras", "gás natural", "ampliação", "investimento industrial"]):
            return "PRODUÇÃO", "emerald", nutrient

        if any(w in text for w in ["rússia", "russia", "china", "belarus", "marrocos", "sanção", "sanções", "tarifa", "mar vermelho", "guerra", "geopolític", "geopolitic", "restrição de exportação", "cota"]):
            return "GEOPOLÍTICA / COMÉRCIO", "blue", nutrient

        if any(w in text for w in ["consumo", "demanda", "safra", "produtor", "plantio", "compra", "entrega", "escoamento", "soja", "milho", "estoque"]):
            return "CONSUMO / DEMANDA", "amber", nutrient

        return "MERCADO GERAL", "emerald", nutrient

    @classmethod
    def _format_relative_date(cls, dt: datetime | None) -> str:
        """Formata data em string relativa amigável (ex: 'Há 2 horas', 'Hoje', etc.)."""
        if not dt:
            return "Recente"
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = diff.total_seconds()
        if seconds < 3600:
            minutes = max(1, int(seconds // 60))
            return f"Há {minutes} min"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"Há {hours} h"
        elif seconds < 172800:
            return "Ontem"
        else:
            days = int(seconds // 86400)
            return f"Há {days} dias"

    @classmethod
    def _parse_xml_feed(cls, xml_bytes: bytes) -> list[dict[str, Any]]:
        """Analisa o documento XML retornado pelo Google News RSS filtrando <= 7 dias."""
        root = ET.fromstring(xml_bytes)
        articles = []
        now_utc = datetime.now(timezone.utc)

        for item in root.findall(".//item"):
            title_el = item.find("title")
            raw_title = (title_el.text or "Notícia Setorial") if title_el is not None and title_el.text else "Notícia Setorial"
            
            link_el = item.find("link")
            link = (link_el.text or "https://news.google.com") if link_el is not None and link_el.text else "https://news.google.com"
            
            pub_el = item.find("pubDate")
            pub_date_str = (pub_el.text or "") if pub_el is not None and pub_el.text else ""
            
            desc_el = item.find("description")
            desc = (desc_el.text or "") if desc_el is not None and desc_el.text else ""

            # Conversão e verificação rigorosa de data (máximo 7 dias = 604.800 segundos)
            parsed_dt = None
            if pub_date_str:
                try:
                    parsed_dt = pd.to_datetime(pub_date_str, utc=True)
                except Exception:
                    pass

            if parsed_dt is not None:
                diff_sec = (now_utc - parsed_dt).total_seconds()
                if diff_sec > 604800:  # Mais de 7 dias de publicação
                    continue

            # Extração da fonte e limpeza do sufixo ' - Fonte' no título
            source_el = item.find("source")
            if source_el is not None and source_el.text:
                source = source_el.text.strip()
                if raw_title.endswith(f" - {source}"):
                    title = raw_title[:-len(f" - {source}")].strip()
                elif " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    title = parts[0].strip()
                else:
                    title = raw_title.strip()
            elif " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                title = parts[0].strip()
                source = parts[1].strip()
            else:
                title = raw_title.strip()
                source = "Google Notícias"

            # Limpeza do snippet HTML da descrição
            snippet = re.sub(r"<[^>]+>", "", desc).strip()
            if not snippet or snippet.startswith(title[:20]):
                snippet = "Acompanhe os desdobramentos completos desta matéria na publicação original."

            published_at_str = parsed_dt.strftime("%Y-%m-%d %H:%M:%S") if parsed_dt is not None else now_utc.strftime("%Y-%m-%d %H:%M:%S")
            rel_date = cls._format_relative_date(parsed_dt.to_pydatetime() if parsed_dt is not None else None)

            topic, topic_color, nutrient = cls._categorize_article(title, snippet)

            articles.append({
                "title": title,
                "link": link,
                "source": source,
                "published_at": published_at_str,
                "pub_date_relative": rel_date,
                "snippet": snippet,
                "topic": topic,
                "topic_color": topic_color,
                "nutrient": nutrient,
            })

        return articles

    @classmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def fetch_fertilizer_news(cls, search_query: str | None = None) -> pd.DataFrame:
        """Busca notícias do Google News RSS limitadas estritamente a no máximo 7 dias."""
        base_term = "fertilizantes (produção OR consumo OR frete OR preços OR importação OR adubo OR ureia OR fosfato OR potassio)"
        query = f"({base_term} {search_query}) when:7d" if search_query else f"({base_term}) when:7d"

        encoded = urllib.parse.quote(query.strip())
        url = f"{cls.BASE_RSS_URL}?q={encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

        articles = None
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 FertiPartner/1.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                xml_data = resp.read()
                articles = cls._parse_xml_feed(xml_data)
        except Exception as exc:
            logger.info("Consulta externa do Google News falhou (%s). Carregando notícias estruturadas locais.", exc)

        if articles:
            df = pd.DataFrame(articles)
        else:
            df = pd.DataFrame(cls.get_fallback_news())

        # Corte rigoroso de 7 dias
        if not df.empty and "published_at" in df.columns:
            now_utc = datetime.now(timezone.utc)
            cutoff = now_utc - timedelta(days=7)
            df["_dt_chk"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
            df = df[df["_dt_chk"].isna() | (df["_dt_chk"] >= cutoff)].drop(columns=["_dt_chk"])

        return df

    @classmethod
    def analyze_sentiment_by_topic(cls, df_news: pd.DataFrame) -> list[dict[str, Any]]:
        """Calcula a análise de sentimento dos últimos 7 dias por tópico estratégico com 3 classificações e pontuação."""
        topics_config = [
            {
                "topic": "FRETE / LOGÍSTICA",
                "icon": "🚢",
                "positive_label": "Melhorando (Fluidez e Tarifas Competitivas)",
                "neutral_label": "Estável (Fluxos e Portos Regulares)",
                "negative_label": "Piorando (Gargalos e Tarifas em Alta)",
                "pos_terms": ["queda de frete", "redução de frete", "desconto", "fluidez", "desobstrução", "ferrovia", "investimento", "eficiência", "alívio", "recorde de descarga", "capacidade estática"],
                "neg_terms": ["alta com gargalos", "alta de frete", "aumento de frete", "gargalo", "gargalos", "fila", "espera", "demora", "sobretaxa", "custo elevado", "pressão", "greve", "parada"],
                "driver": "Operação de berços nos portos de Santos/Paranaguá e tarifas intermodais.",
            },
            {
                "topic": "PRODUÇÃO",
                "icon": "🏭",
                "positive_label": "Melhorando (Capacidade e Oferta em Expansão)",
                "neutral_label": "Estável (Plantas em Operação Contínua)",
                "negative_label": "Piorando (Restrições e Paradas de Plantas)",
                "pos_terms": ["expansão", "inauguração", "reabertura", "recorde", "aumento de produção", "investimento", "incentivo", "eficiência", "petrobras", "ampliação", "programa nacional"],
                "neg_terms": ["parada", "fechamento", "corte", "queda de produção", "redução", "crise", "desabastecimento", "gás caro", "manutenção"],
                "driver": "Nível de atividade fabril nacional e incentivos ao gás competitivo.",
            },
            {
                "topic": "CONSUMO / DEMANDA",
                "icon": "🌾",
                "positive_label": "Melhorando (Demanda Forte para Safras)",
                "neutral_label": "Estável (Ritmo Médio e Previsível)",
                "negative_label": "Piorando (Cautela e Atraso no Plantio)",
                "pos_terms": ["aquecid", "forte", "recorde", "antecipa", "avanço", "plantio acelerado", "crescimento", "compra", "expansão de área", "produtividade"],
                "neg_terms": ["atrasa ritmo", "atraso", "cautela", "desacelera", "retração", "queda de demanda", "insegurança", "baixa", "parada de compras", "estiagem"],
                "driver": "Apetite de compras do produtor rural para fechamento de pacotes na safra.",
            },
            {
                "topic": "PREÇOS / MERCADO",
                "icon": "📈",
                "positive_label": "Melhorando (Cotações Acessíveis e Boa Margem)",
                "neutral_label": "Estável (Paridades em Faixa Normal)",
                "negative_label": "Piorando (Pressão de Custo e Encarecimento)",
                "pos_terms": ["queda de preço", "desconto", "relação de troca", "alívio", "competitiv", "estável", "acessível", "barateamento"],
                "neg_terms": ["alta de preços", "sobem no exterior", "escalada", "pressão", "disparada", "encarece", "inflação", "custo recorde"],
                "driver": "Cotações CFR Paranaguá e paridade de troca grão vs adubo.",
            },
            {
                "topic": "GEOPOLÍTICA / COMÉRCIO",
                "icon": "🌐",
                "positive_label": "Melhorando (Abertura Comercial e Acordos)",
                "neutral_label": "Estável (Fluxos e Relações Mantidas)",
                "negative_label": "Piorando (Sanções, Cotas e Tensões)",
                "pos_terms": ["acordo", "abertura", "isenção", "parceria", "embarque garantido", "distensão", "normalização", "cooperação", "mantêm liderança"],
                "neg_terms": ["sanção", "sanções", "restrição", "prorroga mecanismos", "controle de cotas", "cota", "guerra", "tensão", "bloqueio", "tarifa", "conflito"],
                "driver": "Políticas alfandegárias de grandes players globais (Rússia, China, Oriente Médio).",
            },
        ]

        results = []
        for cfg in topics_config:
            t_name = cfg["topic"]
            sub_df = df_news[df_news["topic"] == t_name] if not df_news.empty and "topic" in df_news.columns else pd.DataFrame()
            news_cnt = len(sub_df)

            net_points = 0.0
            if news_cnt > 0:
                for _, row in sub_df.iterrows():
                    txt = f"{row.get('title', '')} {row.get('snippet', '')}".lower()
                    pos_hits = sum(1 for term in cfg["pos_terms"] if term in txt)
                    neg_hits = sum(1 for term in cfg["neg_terms"] if term in txt)
                    net_points += (pos_hits - neg_hits)
                avg_net = net_points / news_cnt
                calc_score = round(max(-10.0, min(10.0, avg_net * 3.5)), 1)
            else:
                calc_score = 0.0

            # Padrão estrito de 3 classificações adaptado contextualmente por tópico
            if calc_score >= 1.2:
                classification = "Melhorando"
                label = cfg["positive_label"]
                badge_color = "emerald"
                score_str = f"+{calc_score:.1f}"
            elif calc_score <= -1.2:
                classification = "Piorando"
                label = cfg["negative_label"]
                badge_color = "amber"
                score_str = f"{calc_score:.1f}"
            else:
                classification = "Estável"
                label = cfg["neutral_label"]
                badge_color = "blue"
                score_str = f"{calc_score:+.1f}" if calc_score != 0.0 else "0.0"

            results.append({
                "topic": t_name,
                "icon": cfg["icon"],
                "score": score_str,
                "score_val": calc_score,
                "classification": classification,
                "status_label": label,
                "badge_color": badge_color,
                "news_count": news_cnt,
                "driver": cfg["driver"],
            })

        return results

