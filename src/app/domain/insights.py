"""Motor determinístico de geração de insights e detecção de anomalias (RF23)."""

from typing import Any
from app.domain.entities import ExternalDependencyEntity, MarketInsightEntity, InsightSeverity


class MarketInsightsEngine:
    """Motor analítico que avalia séries de dados e produz alertas e oportunidades."""

    def evaluate_dependency_risks(
        self,
        dependencies: list[ExternalDependencyEntity],
    ) -> list[MarketInsightEntity]:
        """Avalia riscos geopolíticos e estratégicos de dependência externa (RF13, RF14)."""
        insights: list[MarketInsightEntity] = []

        for dep in dependencies:
            rate = dep.external_dependency_pct
            if rate >= 85.0:
                insights.append(
                    MarketInsightEntity(
                        id=f"DEP-CRIT-{dep.fertilizer_name[:4].upper()}",
                        title=f"🚨 Dependência Crítica: {dep.fertilizer_name}",
                        category="Segurança de Suprimento",
                        severity=InsightSeverity.CRITICAL,
                        message=(
                            f"O Brasil depende de importações para {rate:.1f}% da sua demanda de {dep.fertilizer_name}. "
                            "Volume altamente exposto a volatilidades cambiais, fretes marítimos e restrições de exportação globais."
                        ),
                        metric_name="Taxa de Dependência",
                        metric_value=f"{rate:.1f}%",
                        baseline_value="Meta Plano Nac. Fertilizantes: < 50%",
                        recommended_action=(
                            "Incentivar contratos de longo prazo, diversificar origens geográficas "
                            "e priorizar investimentos em síntese/extração nacional."
                        ),
                    )
                )
            elif rate >= 70.0:
                insights.append(
                    MarketInsightEntity(
                        id=f"DEP-WARN-{dep.fertilizer_name[:4].upper()}",
                        title=f"⚠️ Alta Dependência Externa: {dep.fertilizer_name}",
                        category="Segurança de Suprimento",
                        severity=InsightSeverity.WARNING,
                        message=(
                            f"A taxa de importação de {dep.fertilizer_name} situa-se em {rate:.1f}%. "
                            "Exige monitoramento contínuo de capacidade dos portos brasileiros e janelas aduaneiras."
                        ),
                        metric_name="Taxa de Dependência",
                        metric_value=f"{rate:.1f}%",
                        baseline_value="Faixa de Alerta: > 70%",
                        recommended_action="Manter estoques reguladores estratégicos e monitorar line-up portuário.",
                    )
                )

        return insights

    def evaluate_price_volatility(
        self,
        price_records: list[dict[str, Any]],
    ) -> list[MarketInsightEntity]:
        """Identifica picos anormais de preços ou quedas bruscas de cotação (RF07, RF23)."""
        insights: list[MarketInsightEntity] = []

        for idx, rec in enumerate(price_records):
            fert = rec.get("fertilizer", "Fertilizante")
            mom_pct = rec.get("mom_pct", 0.0)
            price = rec.get("price", 0.0)

            if mom_pct >= 8.0:
                insights.append(
                    MarketInsightEntity(
                        id=f"PRC-SPIKE-{idx}",
                        title=f"📈 Alta Acentuada no Preço de {fert}",
                        category="Volatilidade de Mercado",
                        severity=InsightSeverity.WARNING,
                        message=(
                            f"A cotação de {fert} disparou {mom_pct:+.1f}% no último mês, "
                            f"atingindo $ {price:,.2f}/MT. Movimento decorrente de aumento de custos de gás ou restrições de oferta."
                        ),
                        metric_name="Variação Mensal (MoM)",
                        metric_value=f"{mom_pct:+.1f}%",
                        baseline_value="Média de flutuação regular: ±3.0%",
                        recommended_action="Avaliar travas de preço (hedge) e antecipação de compras antes de novos aumentos.",
                    )
                )
            elif mom_pct <= -5.0:
                insights.append(
                    MarketInsightEntity(
                        id=f"PRC-DROP-{idx}",
                        title=f"📉 Queda Expressiva no Preço de {fert}",
                        category="Oportunidade de Compra",
                        severity=InsightSeverity.INFO,
                        message=(
                            f"Preço de {fert} recuou {mom_pct:.1f}% no mês, situando-se em $ {price:,.2f}/MT. "
                            "Cenário favorável para formação de estoques e melhora na relação de troca (barter)."
                        ),
                        metric_name="Variação Mensal (MoM)",
                        metric_value=f"{mom_pct:.1f}%",
                        baseline_value="Janela de Baixa de Preço",
                        recommended_action="Aproveitar a janela de oportunidade para fixação de insumos agrícolas.",
                    )
                )

        return insights

    def evaluate_crop_calendar_window(
        self,
        current_month: int,
    ) -> list[MarketInsightEntity]:
        """Identifica a fase do calendário agrícola brasileiro e seus reflexos na demanda (RF10, RF23)."""
        insights: list[MarketInsightEntity] = []

        month_names = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
        }
        m_name = month_names.get(current_month, f"Mês {current_month}")

        if current_month in (7, 8, 9, 10):
            insights.append(
                MarketInsightEntity(
                    id="CAL-SAFRA-VERAO",
                    title="🚜 Janela Crítica: Safra de Verão em Andamento",
                    category="Calendário Agrícola",
                    severity=InsightSeverity.INFO,
                    message=(
                        f"Em {m_name}, o agronegócio brasileiro vive o pico de movimentação de fertilizantes para o plantio da Safra de Verão (Soja e Milho 1ª Safra). "
                        "Portos de Santos e Paranaguá operam com fluxo máximo e os custos de frete rodoviário atingem o topo anual."
                    ),
                    metric_name="Índice Sazonal de Demanda",
                    metric_value="145% da média anual",
                    baseline_value="Pico Sazonal Típico (Q3)",
                    recommended_action="Garantir agendamento de entregas nas fábricas de mistura para evitar gargalos logísticos no plantio.",
                )
            )
        elif current_month in (11, 12, 1, 2):
            insights.append(
                MarketInsightEntity(
                    id="CAL-SAFRINHA",
                    title="🌱 Janela de Suprimento: Safrinha (Milho 2ª Safra)",
                    category="Calendário Agrícola",
                    severity=InsightSeverity.INFO,
                    message=(
                        f"{m_name} marca o início das compras e adubações nitrogenadas de cobertura para o Milho Safrinha. "
                        "Forte pressão na demanda por Ureia e Nitrato de Amônio."
                    ),
                    metric_name="Índice Sazonal de Demanda",
                    metric_value="115% da média anual",
                    baseline_value="Demanda Focada em Nitrogenados",
                    recommended_action="Monitorar disponibilidade de cargas spot de Ureia e preços CFR Brasil.",
                )
            )
        else:
            insights.append(
                MarketInsightEntity(
                    id="CAL-PLANEJAMENTO",
                    title="💡 Janela de Oportunidade: Planejamento e Antecipação",
                    category="Calendário Agrícola",
                    severity=InsightSeverity.INFO,
                    message=(
                        f"O período de {m_name} é tipicamente a entressafra de compras nos portos brasileiros. "
                        "Geralmente oferece as melhores oportunidades de negociação de preços internacionais e fretes marítimos."
                    ),
                    metric_name="Índice Sazonal de Demanda",
                    metric_value="75% da média anual",
                    baseline_value="Janela de Calmaria Portuária",
                    recommended_action="Antecipar compras anuais de NPK para capturar descontos e fretes reduzidos.",
                )
            )

        return insights
