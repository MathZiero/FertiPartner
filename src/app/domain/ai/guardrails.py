"""Módulo de GuardRails e Segurança para o FertiPartner.AI.

Implementa defesas contra Prompt Injection, tentativas de Jailbreak,
exfiltração de diretrizes internas e contenção estrita de escopo ao setor
de fertilizantes, nutrição de plantas e mercado agrícola.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class GuardrailResult:
    """Resultado da validação de segurança de uma entrada do usuário."""
    is_safe: bool
    rejection_reason: str | None = None
    user_message: str | None = None


class AIGuardrails:
    """GuardRails para proteção e contenção de escopo do FertiPartner.AI."""

    # Padrões clássicos de Prompt Injection, Jailbreak e Exfiltração
    INJECTION_PATTERNS = [
        # Sobrescrita de instruções / Role overrides
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"desconsidere\s+(todas\s+)?as\s+(instrucoes|regras|diretrizes)",
        r"esque[cç]a\s+(todas\s+)?as\s+(instrucoes|regras|diretrizes)",
        r"disregard\s+(all\s+)?(prior|previous|initial)\s+guidelines",
        r"now\s+you\s+are\s+(dan|an\s+unrestricted|unfiltered)",
        r"voce\s+agora\s+e\s+(um\s+assistente\s+sem\s+regras|dan|infiltrado)",
        r"pretend\s+(you\s+are|to\s+be)\s+(unrestricted|without\s+rules)",
        r"finja\s+que\s+(voce\s+e|nao\s+tem\s+regras)",
        r"act\s+as\s+an\s+unrestricted",
        r"developer\s+mode\s+output",
        r"modo\s+desenvolvedor\s+ativar",
        r"jailbreak",

        # Exfiltração de System Prompt
        r"(show|repeat|reveal|print|display)\s+(me\s+)?(the\s+)?system\s+prompt",
        r"(mostre|repita|revele|imprima|exiba)\s+(o\s+)?(system\s+prompt|instrucoes\s+do\s+sistema)",
        r"what\s+(are\s+)?your\s+(original|initial|system)\s+instructions",
        r"quais\s+sao\s+suas\s+instrucoes\s+(iniciais|de\s+sistema)",
        r"print\s+everything\s+above",
        r"imprima\s+tudo\s+acima",

        # Delimitadores e injeção de papéis falsos
        r"<\s*system\s*>",
        r"\[\s*system\s*\]",
        r"###\s*system:",
        r"role\s*:\s*system",

        # Tentativa de injeção de código executável
        r"\b(exec|eval|__import__|os\.system|subprocess)\b",
        r"(drop\s+table|truncate\s+table|delete\s+from\s+[a-z_]+)",
    ]

    # Palavras-chave do domínio agrícola/fertilizantes para validação de escopo
    DOMAIN_KEYWORDS = {
        # Fertilizantes e macronutrientes
        "fertilizante", "fertilizantes", "adubo", "adubos", "npk", "nitrogenio", "nitrogenados",
        "fosforo", "fosfatados", "potassio", "potassicos", "enxofre", "micronutriente",
        "micronutrientes", "ureia", "amonia", "nitrato", "sulfato", "map", "dap", "ssp",
        "tsp", "kcl", "sop", "mop", "rocha", "fosfatica", "boro", "zinco", "cobre",
        "manganes", "molibdenio", "cobalto", "calcio", "magnesio", "calcareo", "gesso",

        # Agronomia e lavoura
        "solo", "solos", "acidez", "ph", "nutricao", "plantio", "semeadura", "safra",
        "safrinha", "lavoura", "lavouras", "cultura", "culturas", "soja", "milho", "trigo",
        "cana", "algodao", "cafe", "arroz", "feijao", "adubacao", "produtividade",
        "higroscopicidade", "pcur", "granulometria", "foliar", "fertirrigacao",

        # Economia, mercado e logística
        "cotacao", "cotacoes", "preco", "precos", "mercado", "balanco", "importacao",
        "importacoes", "exportacao", "exportacoes", "frete", "fretes", "porto", "portos",
        "paranagua", "santos", "itaqui", "rio grande", "comex", "comtrade", "faostat",
        "relacao de troca", "barter", "spread", "cif", "fob", "cfr", "dolar", "cambio",
        "dependencia", "abastecimento", "industria", "fabrica", "sintese", "mineracao",
        "russia", "china", "marrocos", "canada", "belarus", "egito", "qatar", "omã",
        "conab", "anda", "ifa", "consumo", "demanda", "oferta", "entrega", "estoque",

        # Saudações e interações operacionais comuns
        "ola", "oi", "bom dia", "boa tarde", "boa noite", "ajuda", "socorro", "quem e voce",
        "o que voce faz", "como funciona", "obrigado", "obrigada", "valeu", "menu", "comandos",
    }

    REJECTION_INJECTION = (
        "Solicitação bloqueada pelas diretrizes de segurança do FertiPartner.AI. "
        "Não é permitido instruir alterações de regras internas, comandos de sistema "
        "ou desvio das funções do assistente."
    )

    REJECTION_OUT_OF_SCOPE = (
        "O FertiPartner.AI é um assistente exclusivamente especializado em fertilizantes, "
        "nutrição vegetal, logística de suprimentos e inteligência de mercado agrícola. "
        "Por favor, formule perguntas relacionadas a cotações, rotas de importação, balanço "
        "de nutrientes ou características agronômicas de adubos."
    )

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Normaliza o texto removendo acentos e convertendo para minúsculas."""
        text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
        return text.lower().strip()

    @classmethod
    def check_prompt_injection(cls, prompt: str) -> Tuple[bool, str | None]:
        """Verifica se o texto contém padrões de injeção de prompt ou jailbreak."""
        normalized = cls._normalize_text(prompt)
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                return False, cls.REJECTION_INJECTION
        return True, None

    @classmethod
    def check_domain_scope(cls, prompt: str) -> Tuple[bool, str | None]:
        """Verifica se a consulta possui relevância com o domínio do FertiPartner."""
        normalized = cls._normalize_text(prompt)

        # Tokens do texto
        tokens = set(re.findall(r"\b\w+\b", normalized))
        if not tokens:
            return False, cls.REJECTION_OUT_OF_SCOPE

        # Saudações simples curtas
        if len(tokens) <= 3 and any(t in {"ola", "oi", "ajuda", "menu", "socorro", "bom", "dia", "tarde", "noite"} for t in tokens):
            return True, None

        # Verifica palavras-chave isoladas com limites de palavra
        for kw in cls.DOMAIN_KEYWORDS:
            if " " in kw:
                # Expressões compostas (ex: "relacao de troca", "rio grande", "quem e voce")
                if re.search(rf"\b{re.escape(kw)}\b", normalized):
                    return True, None
            else:
                if kw in tokens:
                    return True, None

        return False, cls.REJECTION_OUT_OF_SCOPE

    @classmethod
    def validate_input(cls, prompt: str) -> GuardrailResult:
        """Executa validação completa de entrada (injeção + contenção de escopo)."""
        if not prompt or not prompt.strip():
            return GuardrailResult(is_safe=False, rejection_reason="EMPTY_PROMPT", user_message="Por favor, digite sua pergunta.")

        # 1. Defesa contra Prompt Injection e Jailbreak
        safe_injection, msg_injection = cls.check_prompt_injection(prompt)
        if not safe_injection:
            return GuardrailResult(
                is_safe=False,
                rejection_reason="PROMPT_INJECTION_DETECTED",
                user_message=msg_injection,
            )

        # 2. Contenção estrita de escopo de domínio
        in_scope, msg_scope = cls.check_domain_scope(prompt)
        if not in_scope:
            return GuardrailResult(
                is_safe=False,
                rejection_reason="OUT_OF_SCOPE",
                user_message=msg_scope,
            )

        return GuardrailResult(is_safe=True)
