import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.v1.endpoints import ai
from app.main import app
from app.services.ai_grounding_service import GroundedContext


def _set_guardrail(monkeypatch) -> None:
    monkeypatch.setattr(ai.settings, "ai_guardrail_enabled", True, raising=False)
    monkeypatch.setattr(ai.settings, "ai_guardrail_mode", "hybrid", raising=False)
    monkeypatch.setattr(ai.settings, "ai_guardrail_strict", False, raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_key_primary", "dummy-key", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_key_secondary", None, raising=False)


def test_chatbox_response_includes_next_step(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail, grounded_context=None: (
            "Summary: Use the Kelana Jaya line.\n"
            "- Start at KL Sentral.\n"
            "- Stop at Pasar Seni."
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "How to go to Pasar Seni?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["in_scope"] is True
    assert "Next step:" in payload["answer"]
    assert payload["response_source"] in {"database", "static_help", "fallback"}
    assert "grounded" in payload


def test_chatbox_long_paragraph_is_normalized(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail, grounded_context=None: (
            "Take the train from KL Sentral to Pasar Seni and follow station signs carefully because the station may be crowded. "
            "Please prepare your card first and avoid rushing when changing platforms. "
            "If you need help, ask station staff near the gate."
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Give me detailed route guidance"},
    )

    assert response.status_code == 200
    answer = response.json()["answer"]
    lines = [line for line in answer.splitlines() if line.strip()]
    assert len(lines) >= 3
    assert any(line.startswith("- ") for line in lines)
    assert "Next step:" in answer


def test_chatbox_out_of_scope_reject_has_guidance(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai.settings, "ai_guardrail_mode", "rules_only", raising=False)
    monkeypatch.setattr(ai.settings, "ai_guardrail_strict", True, raising=False)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: False)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Give me crypto tips"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["in_scope"] is False
    assert "Next step:" in payload["answer"]


def test_chatbox_fallback_message_when_ai_unavailable(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)

    def raise_network_error(message: str, api_key: str, prompt_guardrail: bool, grounded_context=None) -> str:
        raise RuntimeError("network down")

    monkeypatch.setattr(ai, "_call_gemini", raise_network_error)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Is train running now?"},
    )

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert "temporarily unavailable" in answer
    assert "Next step:" in answer


def test_chatbox_fallback_language_matches_user(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail, grounded_context=None: (_ for _ in ()).throw(RuntimeError("timeout")),
    )

    client = TestClient(app)

    zh = client.post("/ai/conversations/conv_test/messages", json={"message": "现在可以去医院吗？"})
    ms = client.post("/ai/conversations/conv_test/messages", json={"message": "bagaimana pergi ke stesen"})
    en = client.post("/ai/conversations/conv_test/messages", json={"message": "How to buy ticket?"})

    assert "下一步：" in zh.json()["answer"]
    assert "Langkah seterusnya:" in ms.json()["answer"]
    assert "Next step:" in en.json()["answer"]


def test_chatbox_help_intent_marks_static_help_source(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "build_grounded_context",
        lambda **kwargs: GroundedContext(
            intent="help_static",
            grounded=True,
            response_source="static_help",
            used_data_keys=["help.buy_ticket"],
            facts=["Use Touch 'n Go card for faster travel."],
        ),
    )
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail, grounded_context=None: (
            "Summary: Use Touch 'n Go card.\n- Tap in and tap out.\nNext step: Ask staff if you need help."
        ),
    )

    client = TestClient(app)
    response = client.post("/ai/conversations/conv_test/messages", json={"message": "How to buy ticket?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["grounded"] is True
    assert payload["response_source"] == "static_help"
    assert payload["used_data_keys"] == ["help.buy_ticket"]


def test_chatbox_unknown_intent_falls_back_source(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "build_grounded_context",
        lambda **kwargs: GroundedContext(
            intent="unknown",
            grounded=False,
            response_source="fallback",
            used_data_keys=[],
            facts=[],
        ),
    )
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail, grounded_context=None: (
            "Summary: I can give general help.\n- Local data is unavailable for this detail."
        ),
    )

    client = TestClient(app)
    response = client.post("/ai/conversations/conv_test/messages", json={"message": "Tell me market news"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["grounded"] is False
    assert payload["response_source"] == "fallback"


def test_chatbox_geographic_query_appends_maps_disclaimer(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(ai.settings, "gemini_maps_grounding_enabled", True, raising=False)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail, grounded_context=None: (
            "Summary: The nearest station is KL Sentral.\n"
            "- Walk about 8 minutes.\n"
            "Next step: follow the station signs."
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "附近有什么地铁站？"},
    )

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert "数据来源于地图服务，可能有变动" in answer


def test_chatbox_nongeographic_query_skips_maps_disclaimer(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(ai.settings, "gemini_maps_grounding_enabled", True, raising=False)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail, grounded_context=None: (
            "Summary: Use Touch 'n Go card.\n"
            "- Keep your card ready.\n"
            "Next step: ask staff if you need help."
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "如何买票？"},
    )

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert "数据来源于地图服务，可能有变动" not in answer

