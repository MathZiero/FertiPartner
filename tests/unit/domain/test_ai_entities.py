"""Testes unitários rigorosos para entidades de domínio do FertiPartner.AI."""

from datetime import datetime, timezone
import pytest

from app.domain.ai.entities import (
    AIResponse,
    ChatMessage,
    ChatRole,
    ToolCall,
    ToolResult,
)


class TestChatRole:
    """Validações de contrato e tipos do enum ChatRole."""

    def test_all_expected_roles_exist(self):
        expected = {"user", "model", "system", "tool"}
        actual = {role.value for role in ChatRole}
        assert actual == expected

    def test_role_str_inheritance(self):
        assert isinstance(ChatRole.USER, str)
        assert ChatRole.USER == "user"
        assert ChatRole.MODEL == "model"
        assert ChatRole.SYSTEM == "system"
        assert ChatRole.TOOL == "tool"

    def test_invalid_role_lookup_raises_value_error(self):
        with pytest.raises(ValueError):
            ChatRole("invalid_role")


class TestToolCall:
    """Validações da dataclass ToolCall."""

    def test_tool_call_initialization_with_minimal_fields(self):
        call = ToolCall(name="get_price_trends", args={"fertilizer": "ureia"})
        assert call.name == "get_price_trends"
        assert call.args == {"fertilizer": "ureia"}
        assert call.id is None
        assert call.thought_signature is None

    def test_tool_call_with_full_fields(self):
        call = ToolCall(
            name="get_supply_balance",
            args={"fertilizer": "map", "year": 2024},
            id="call_abc123",
            thought_signature="sig_xyz",
        )
        assert call.name == "get_supply_balance"
        assert call.args["year"] == 2024
        assert call.id == "call_abc123"
        assert call.thought_signature == "sig_xyz"

    def test_tool_call_equality(self):
        call1 = ToolCall(name="test", args={"x": 1}, id="1")
        call2 = ToolCall(name="test", args={"x": 1}, id="1")
        assert call1 == call2


class TestToolResult:
    """Validações da dataclass ToolResult."""

    def test_tool_result_with_dict_content(self):
        res = ToolResult(name="get_price_trends", content={"price": 350.0}, id="call_1")
        assert res.name == "get_price_trends"
        assert res.content == {"price": 350.0}
        assert res.id == "call_1"

    def test_tool_result_with_list_content(self):
        res = ToolResult(name="get_market_news", content=[{"title": "Safra Recorde"}])
        assert isinstance(res.content, list)
        assert len(res.content) == 1

    def test_tool_result_with_string_content(self):
        res = ToolResult(name="error_tool", content="Service unavailable")
        assert res.content == "Service unavailable"


class TestChatMessage:
    """Validações rigorosas para mensagens no histórico de chat."""

    def test_chat_message_defaults(self):
        msg = ChatMessage(role=ChatRole.USER, content="Olá!")
        assert msg.role == ChatRole.USER
        assert msg.content == "Olá!"
        assert msg.tool_calls == []
        assert msg.tool_results == []
        assert msg.raw_parts == []
        assert isinstance(msg.timestamp, datetime)
        assert msg.timestamp.tzinfo == timezone.utc

    def test_chat_message_independent_list_defaults(self):
        msg1 = ChatMessage(role=ChatRole.USER, content="M1")
        msg2 = ChatMessage(role=ChatRole.MODEL, content="M2")
        msg1.tool_calls.append(ToolCall(name="t1", args={}))
        assert len(msg2.tool_calls) == 0, "Default factory must not share list instances across messages"

    def test_chat_message_with_tools(self):
        tool_call = ToolCall(name="get_spec", args={"slug": "ureia"}, id="tc_1")
        tool_res = ToolResult(name="get_spec", content={"formula": "CO(NH2)2"}, id="tc_1")
        msg = ChatMessage(
            role=ChatRole.MODEL,
            content="",
            tool_calls=[tool_call],
            tool_results=[tool_res],
            raw_parts=[{"type": "function_call"}],
        )
        assert len(msg.tool_calls) == 1
        assert len(msg.tool_results) == 1
        assert len(msg.raw_parts) == 1
        assert msg.tool_calls[0].name == "get_spec"


class TestAIResponse:
    """Validações estruturais para respostas da IA."""

    def test_successful_text_response(self):
        resp = AIResponse(content="A cotação da Ureia é USD 350/t.", is_success=True)
        assert resp.is_success is True
        assert resp.content.startswith("A cotação")
        assert resp.error_message is None
        assert resp.tool_calls == []

    def test_failed_response_contracts(self):
        resp = AIResponse(
            content="Erro ao consultar Gemini.",
            is_success=False,
            error_message="503 Service Unavailable",
            finish_reason="ERROR",
        )
        assert resp.is_success is False
        assert resp.error_message == "503 Service Unavailable"
        assert resp.finish_reason == "ERROR"

    def test_response_with_tool_calls_and_signature(self):
        tc = ToolCall(name="get_price_trends", args={"fertilizer": "dap"}, id="call_99", thought_signature="sig_99")
        resp = AIResponse(
            content="",
            tool_calls=[tc],
            tools_used=["get_price_trends"],
            raw_parts=[{"thought": "Preciso checar preços"}],
        )
        assert len(resp.tool_calls) == 1
        assert resp.tools_used == ["get_price_trends"]
        assert resp.tool_calls[0].thought_signature == "sig_99"
