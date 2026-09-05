"""Configurações, paletas e temas visuais do Plotly para o FertiPartner (Light Mode)."""

from typing import Any
import plotly.graph_objects as go
import plotly.io as pio

# Paleta de cores AgTech vibrante e profissional para fundo claro
FERTI_COLORS = [
    "#2D6A4F",  # Forest Green (N - Nitrogênio / Principal)
    "#2563EB",  # Royal Blue (P - Fósforo / Comércio)
    "#D97706",  # Amber/Ochre (K - Potássio / Preços)
    "#7C3AED",  # Violet (Misturas NPK)
    "#0891B2",  # Cyan (Amônia / Gás)
    "#DB2777",  # Pink (Micronutrientes)
    "#EA580C",  # Orange (Exportações)
    "#059669",  # Emerald (Importações)
    "#64748B",  # Slate (Neutro / Comparativos)
]

NUTRIENT_COLORS = {
    "N": "#2D6A4F",
    "P2O5": "#2563EB",
    "K2O": "#D97706",
    "S": "#CA8A04",
    "OUTROS": "#6B7280",
}

CATEGORY_COLORS = {
    "Fertilizantes Nitrogenados": "#2D6A4F",
    "Fertilizantes Fosfatados": "#2563EB",
    "Fertilizantes Potássicos": "#D97706",
    "Misturas e Complexos NPK": "#7C3AED",
    "Micronutrientes": "#DB2777",
}


def apply_ferti_theme(
    fig: go.Figure,
    title: str | None = None,
    height: int = 420,
    show_legend: bool = True,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """Aplica o design system AgTech (Modo Claro) a uma figura Plotly sem rótulos 'undefined'."""
    layout_updates: dict[str, Any] = {
        "template": "plotly_white",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": dict(
            family="Inter, -apple-system, sans-serif",
            color="#1F2937",
            size=12,
        ),
        "height": height,
        "margin": dict(l=45, r=25, t=50 if title else 25, b=45),
        "colorway": FERTI_COLORS,
        "hoverlabel": dict(
            bgcolor="#FFFFFF",
            font_size=12,
            font_family="Inter, sans-serif",
            font_color="#1F2937",
            bordercolor="#CBD5E1",
        ),
    }

    # Evita categoricamente qualquer renderização de string 'undefined' no layout.title
    if title and str(title).strip():
        layout_updates["title"] = dict(
            text=f"<b>{title}</b>",
            font=dict(family="Outfit, sans-serif", size=16, color="#1B4332"),
            x=0.01,
            y=0.96,
        )
    else:
        layout_updates["title"] = dict(text="")

    # Configuração de legenda sem 'undefined'
    if show_legend:
        layout_updates["legend"] = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#4B5563"),
            bgcolor="rgba(255,255,255,0.8)",
            title=dict(text=""),
        )
    else:
        layout_updates["legend"] = dict(visible=False)

    fig.update_layout(**layout_updates)

    # Configuração explícita do eixo X sem 'undefined'
    x_updates: dict[str, Any] = {
        "gridcolor": "#E5E7EB",
        "zerolinecolor": "#CBD5E1",
        "tickfont": dict(color="#4B5563", size=11),
        "showline": True,
        "linecolor": "#CBD5E1",
    }
    if x_title and str(x_title).strip():
        x_updates["title"] = dict(text=x_title, font=dict(size=12, color="#4B5563"))
    else:
        x_updates["title"] = dict(text="")
    fig.update_xaxes(**x_updates)

    # Configuração explícita do eixo Y sem 'undefined'
    y_updates: dict[str, Any] = {
        "gridcolor": "#E5E7EB",
        "zerolinecolor": "#CBD5E1",
        "tickfont": dict(color="#4B5563", size=11),
        "showline": True,
        "linecolor": "#CBD5E1",
    }
    if y_title and str(y_title).strip():
        y_updates["title"] = dict(text=y_title, font=dict(size=12, color="#4B5563"))
    else:
        y_updates["title"] = dict(text="")
    fig.update_yaxes(**y_updates)

    return fig


def get_default_plotly_config() -> dict[str, Any]:
    """Retorna configuração otimizada e minimalista para interações Plotly."""
    return {
        "displayModeBar": "hover",
        "displaylogo": False,
        "modeBarButtonsToRemove": [
            "lasso2d",
            "select2d",
            "toggleSpikelines",
            "hoverCompareCartesian",
        ],
        "responsive": True,
    }


def format_metric_tons(val: float | None) -> str:
    """Formata valor numérico em toneladas métricas com sufixo amigável (k, M, MT)."""
    if val is None or val == 0:
        return "0 MT"
    abs_val = abs(val)
    if abs_val >= 1_000_000:
        return f"{val / 1_000_000:,.2f} M MT"
    if abs_val >= 1_000:
        return f"{val / 1_000:,.1f} k MT"
    return f"{val:,.1f} MT"


def format_currency_usd(val: float | None) -> str:
    """Formata valor numérico em dólares com sufixo amigável."""
    if val is None or val == 0:
        return "$ 0,00"
    abs_val = abs(val)
    if abs_val >= 1_000_000_000:
        return f"$ {val / 1_000_000_000:,.2f} B"
    if abs_val >= 1_000_000:
        return f"$ {val / 1_000_000:,.2f} M"
    if abs_val >= 1_000:
        return f"$ {val / 1_000:,.1f} k"
    return f"$ {val:,.2f}"
