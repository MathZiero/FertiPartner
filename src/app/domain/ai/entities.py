"""Entidades de domínio para o FertiPartner.AI."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ChatRole(str, Enum):
    """Papel de cada interlocutor na conversa."""
    USER = "user"
    MODEL = "model"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class ToolCall:
    """Intenção de chamada de função emitida pela LLM."""
    name: str
    args: dict[str, Any]
    id: str | None = None


@dataclass
class ToolResult:
    """Resultado da execução de uma ferramenta retornado para a LLM."""
    name: str
    content: dict[str, Any] | list[Any] | str
    id: str | None = None


@dataclass
class ChatMessage:
    """Mensagem individual no histórico da sessão."""
    role: ChatRole
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AIResponse:
    """Resposta estruturada gerada pelo cliente de IA."""
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    is_success: bool = True
    error_message: str | None = None
    finish_reason: str | None = None
    tools_used: list[str] = field(default_factory=list)
