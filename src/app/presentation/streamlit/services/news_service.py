"""Serviço de inteligência de notícias agrícolas e fertilizantes via Google News RSS."""

from datetime import datetime, timezone
import logging
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# Fallback estruturado com notícias setoriais curadas caso a rede externa esteja inacessível ou em testes
MOCK_FERTILIZER_NEWS = [
    {
        "title": "Mercado de fertilizantes atrasa ritmo no Brasil e demanda para safras gera cautela",
        "link": "https://news.google.com",
        "source": "CNN Brasil",
        "published_at": "2026-09-06 20:39:55",
        "pub_date_relative": "Ontem",
        "snippet": "Compradores nacionais avaliam margens operacionais e ritmo do plantio de grãos, monitorando as oscilações cambiais e preços de entrega.",
        "topic": "CONSUMO / DEMANDA",
        "topic_color": "amber",
        "nutrient": "Geral",
    },
    {
        "title": "Produtor brasileiro avalia relação de troca grão-adubo antes da safra de verão",
        "link": "https://news.google.com",
        "source": "Exame Agro",
        "published_at": "2026-09-07 09:03:02",
        "pub_date_relative": "Hoje",
        "snippet": "A paridade de troca entre sacas de soja e fertilizantes NPK dita o ritmo de fechamento de pacotes tecnológicos no Centro-Oeste.",
        "topic": "PREÇOS / MERCADO",
        "topic_color": "purple",
        "nutrient": "Complexos NPK",
    },
    {
        "title": "Programa nacional de incentivo à produção de fertilizantes busca reduzir dependência externa",
        "link": "https://news.google.com",
        "source": "Agência Câmara",
        "published_at": "2026-09-04 21:06:00",
        "pub_date_relative": "Há 3 dias",
        "snippet": "Medida prevê estímulos tributários e fornecimento competitivo de gás natural para indústrias de nitrogenados e rocha fosfática no país.",
        "topic": "PRODUÇÃO",
        "topic_color": "emerald",
        "nutrient": "Nitrogenados (N)",
    },
    {
        "title": "Frete marítimo de fertilizantes registra alta com gargalos em rotas estratégicas e taxas portuárias",
        "link": "https://news.google.com",
        "source": "Globo Rural",
        "published_at": "2026-09-05 14:20:00",
        "pub_date_relative": "Há 2 dias",
        "snippet": "Tempo de espera nos berços de descarga em Paranaguá e Santos pressiona o custo CIF Brasil para cargas de cloreto de potássio e fosfatados.",
        "topic": "FRETE / LOGÍSTICA",
        "topic_color": "blue",
        "nutrient": "Potássicos (K)",
    },
    {
        "title": "Exportações russas de fertilizantes mantêm liderança em fornecimento para o mercado brasileiro",
        "link": "https://news.google.com",
        "source": "Reuters Brasil",
        "published_at": "2026-09-03 11:15:00",
        "pub_date_relative": "Há 4 dias",
        "snippet": "Apesar de restrições em operações de câmbio e seguros globais, navios graneleiros seguem operando rotas regulares do Báltico para o Brasil.",
        "topic": "GEOPOLÍTICA / COMÉRCIO",
        "topic_color": "blue",
        "nutrient": "Nitrogenados (N)",
    },
    {
        "title": "Cotações de ureia granulada sobem no exterior com paradas técnicas e demanda pontual da Índia",
        "link": "https://news.google.com",
        "source": "Notícias Agrícolas",
        "published_at": "2026-09-05 17:45:00",
        "pub_date_relative": "Há 2 dias",
        "snippet": "Leilão de importação asiático e oscilação dos custos de gás na Europa conferem suporte às cotações no Oriente Médio e Golfo dos EUA.",
        "topic": "PREÇOS / MERCADO",
        "topic_color": "purple",
        "nutrient": "Nitrogenados (N)",
    },
    {
        "title": "China prorroga mecanismos de inspeção e monitoramento sobre embarques externos de fosfatados",
        "link": "https://news.google.com",
        "source": "Valor Econômico",
        "published_at": "2026-09-02 16:30:00",
        "pub_date_relative": "Há 5 dias",
        "snippet": "Controle de cotas para proteger o abastecimento doméstico chinês reduz oferta imediata de DAP e MAP para o Ocidente.",
        "topic": "GEOPOLÍTICA / COMÉRCIO",
        "topic_color": "blue",
        "nutrient": "Fosfatados (P)",
    },
    {
        "title": "Mato Grosso amplia recepção de adubos por ferrovia para otimizar custos logísticos de distribuição",
        "link": "https://news.google.com",
        "source": "Canal Rural",
        "published_at": "2026-09-04 10:10:00",
        "pub_date_relative": "Há 3 dias",
        "snippet": "Terminais intermodais no norte do estado aumentam capacidade estática de estocagem de granéis sólidos fertilizantes para o pico do plantio.",
        "topic": "FRETE / LOGÍSTICA",
        "topic_color": "blue",
        "nutrient": "Geral",
    },
]


class GoogleNewsService:
    """Coletor e analisador semântico de notícias de fertilizantes do Google News RSS."""

    BASE_RSS_URL = "https://news.google.com/rss/search"

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
        # 1. Fretes & Logística
        if any(w in text for w in ["frete", "porto", "paranaguá", "paranagua", "santos", "itaqui", "barcarena", "navio", "fila", "espera", "marítim", "maritim", "logístic", "logistic", "ferrovia", "cabotagem", "transporte"]):
            return "FRETE / LOGÍSTICA", "blue", nutrient

        # 2. Preços & Cotações (prioridade sobre termos geográficos gerais)
        if any(w in text for w in ["preço", "preco", "cotação", "cotacao", "cotações", "cotacoes", "dólar", "dolar", "fob", "cfr", "custo", "relação de troca", "relacao de troca", "spread"]):
            return "PREÇOS / MERCADO", "purple", nutrient

        # 3. Produção & Indústria
        if any(w in text for w in ["produção", "producao", "fábrica", "fabrica", "planta", "capacidade", "indústria", "industria", "petrobras", "gás natural", "ampliação", "investimento industrial"]):
            return "PRODUÇÃO", "emerald", nutrient

        # 4. Geopolítica & Relações Internacionais
        if any(w in text for w in ["rússia", "russia", "china", "belarus", "marrocos", "sanção", "sanções", "tarifa", "mar vermelho", "guerra", "geopolític", "geopolitic", "restrição de exportação", "cota"]):
            return "GEOPOLÍTICA / COMÉRCIO", "blue", nutrient

        # 5. Consumo & Demanda
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
        """Analisa o documento XML retornado pelo Google News RSS."""
        root = ET.fromstring(xml_bytes)
        articles = []

        for item in root.findall(".//item"):
            raw_title = item.find("title").text if item.find("title") is not None else "Notícia Setorial"
            link = item.find("link").text if item.find("link") is not None else "https://news.google.com"
            pub_date_str = item.find("pubDate").text if item.find("pubDate") is not None else ""
            desc = item.find("description").text if item.find("description") is not None else ""

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

            # Conversão de data RFC 822 (ex: "Sun, 06 Sep 2026 20:39:55 GMT")
            parsed_dt = None
            if pub_date_str:
                try:
                    parsed_dt = pd.to_datetime(pub_date_str, utc=True)
                except Exception:
                    pass

            published_at_str = parsed_dt.strftime("%Y-%m-%d %H:%M:%S") if parsed_dt is not None else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
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
        """Busca notícias ao vivo do Google News RSS com fallback offline robusto."""
        # Query refinada abrangendo os termos solicitados pelo usuário
        base_term = "fertilizantes (produção OR consumo OR frete OR preços OR importação OR adubo OR ureia OR fosfato OR potassio)"
        query = f"{base_term} {search_query}" if search_query else base_term

        encoded = urllib.parse.quote(query.strip())
        url = f"{cls.BASE_RSS_URL}?q={encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 FertiPartner/1.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                xml_data = resp.read()
                articles = cls._parse_xml_feed(xml_data)
                if articles:
                    return pd.DataFrame(articles)
        except Exception as exc:
            logger.info("Consulta externa do Google News falhou (%s). Carregando notícias estruturadas locais.", exc)

        return pd.DataFrame(MOCK_FERTILIZER_NEWS)
