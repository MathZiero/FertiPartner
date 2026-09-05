"""Validadores de consistência e regras de negócio da camada de domínio (RNF01, RN03, RN04)."""


class DomainValidationError(ValueError):
    """Exceção levantada quando uma regra de negócio ou validação de domínio falha."""
    pass


def validate_non_negative_number(value: float, field_name: str) -> float:
    """Garante que um valor quantitativo ou monetário não é negativo."""
    if value < 0.0:
        raise DomainValidationError(f"O campo '{field_name}' não pode ser negativo: {value}")
    return value


def validate_date_range(start_year: int, end_year: int) -> None:
    """Valida coerência de intervalo de anos históricos."""
    if start_year > end_year:
        raise DomainValidationError(f"Ano inicial ({start_year}) não pode ser maior que o ano final ({end_year}).")
