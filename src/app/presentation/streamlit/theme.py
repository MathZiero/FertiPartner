"""Configurações, paletas e temas visuais do Plotly para o FertiPartner."""

from typing import Any
import plotly.graph_objects as go
import plotly.io as pio

# Paleta de cores AgTech vibrante e profissional
FERTI_COLORS = [
    "#10B981",  # Emerald (Verde N - Nitrogênio / Principal)
    "#3B82F6",  # Blue (Azul P - Fósforo / Comércio)
    "#F59E0B",  # Amber (Âmbar K - Potássio / Preços)
    "#8B5CF6",  # Purple (Misturas NPK)
    "#06B6D4",  # Cyan (Amônia / Gás)
    "#EC4899",  # Pink (Micronutrientes)
    "#F97316",  # Orange (Exportações)
    "#14B8A6",  # Teal (Importações)
    "#64748B",  # Slate (Neutro / Comparativos)
]

NUTRIENT_COLORS = {
    "N": "#10B981",
    "P2O5": "#3B82F6",
    "K2O": "#F59E0B",
    "S": "#EAB308",
    "OUTROS": "#64748B",
}

CATEGORY_COLORS = {
    "Fertilizantes Nitrogenados": "#10B981",
    "Fertilizantes Fosfatados": "#3B82F6",
    "Fertilizantes Potássicos": "#F59E0B",
    "Misturas e Complexos NPK": "#8B5CF6",
    "Micronutrientes": "#EC4899",
}


def apply_ferti_theme(
    fig: go.Figure,
    title: str | None = None,
    height: int = 420,
    show_legend: bool = True,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """Aplica o design system AgTech do FertiPartner a uma figura Plotly."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, -apple-system, sans-serif",
            color="#E2E8F0",
            size=12,
        ),
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Outfit, sans-serif", size=17, color="#FFFFFF"),
            x=0.01,
            y=0.96,
        ) if title else None,
        height=height,
        margin=dict(l=45, r=25, t=55 if title else 25, b=45),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#94A3B8"),
            bgcolor="rgba(0,0,0,0)",
        ) if show_legend else dict(visible=False),
        colorway=FERTI_COLORS,
        hoverlabel=dict(
            bgcolor="#1E293B",
            font_size=12,
            font_family="Inter, sans-serif",
            bordercolor="rgba(255,255,255,0.15)",
        ),
    )

    fig.update_xaxes(
        title=dict(text=x_title, font=dict(size=12, color="#94A3B8")) if x_title else None,
        gridcolor="rgba(255, 255, 255, 0.06)",
        zerolinecolor="rgba(255, 255, 255, 0.12)",
        tickfont=dict(color="#94A3B8", size=11),
        showline=True,
        linecolor="rgba(255, 255, 255, 0.1)",
    )

    fig.update_yaxes(
        title=dict(text=y_title, font=dict(size=12, color="#94A3B8")) if y_title else None,
        gridcolor="rgba(255, 255, 255, 0.06)",
        zerolinecolor="rgba(255, 255, 255, 0.12)",
        tickfont=dict(color="#94A3B8", size=11),
        showline=True,
        linecolor="rgba(255, 255, 255, 0.1)",
    )

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
