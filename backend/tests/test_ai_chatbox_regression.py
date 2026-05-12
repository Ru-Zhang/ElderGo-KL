import sys
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.v1.endpoints import ai
from app.main import app


def _set_guardrail(monkeypatch) -> None:
    ai.GEMINI_KEY_POOL = ai.GeminiKeyPool()
    monkeypatch.setattr(ai.settings, "ai_guardrail_enabled", True, raising=False)
    monkeypatch.setattr(ai.settings, "ai_guardrail_mode", "hybrid", raising=False)
    monkeypatch.setattr(ai.settings, "ai_guardrail_strict", False, raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_key_primary", "dummy-key", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_key_secondary", None, raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_keys", "", raising=False)


def _assert_no_rag_metadata(payload: dict) -> None:
    assert "response_source" not in payload
    assert "grounded" not in payload
    assert "used_data_keys" not in payload


def _rate_limit_error() -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.test/gemini")
    response = httpx.Response(429, request=request)
    return httpx.HTTPStatusError("quota exhausted", request=request, response=response)


def test_chatbox_response_includes_natural_action_suggestion(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail: (
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
    assert "You can tell me your start point and destination" in payload["answer"]
    assert "Next step:" not in payload["answer"]
    _assert_no_rag_metadata(payload)


def test_chatbox_gemini_call_has_no_grounded_context(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    calls = []

    def fake_call_gemini(*args, **kwargs) -> str:
        calls.append({"args": args, "kwargs": kwargs})
        return "Summary: I can help.\n- Tell me where you start."

    monkeypatch.setattr(ai, "_call_gemini", fake_call_gemini)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "How to go to Pasar Seni?",
            "current_route_id": "legacy-route",
            "selected_location_id": "legacy-station",
            "anonymous_user_id": "legacy-user",
        },
    )

    assert response.status_code == 200
    assert calls
    assert "grounded_context" not in calls[0]["kwargs"]
    _assert_no_rag_metadata(response.json())


def test_chatbox_switches_to_next_gemini_key_after_rate_limit(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai.settings, "gemini_api_key_primary", "key-one", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_key_secondary", "key-two", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_keys", "key-two,key-three", raising=False)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    attempted_keys = []

    def fake_call_gemini(message: str, api_key: str, prompt_guardrail: bool) -> str:
        attempted_keys.append(api_key)
        if api_key == "key-one":
            raise _rate_limit_error()
        return "I can help with route planning.\nYou can enter your destination first."

    monkeypatch.setattr(ai, "_call_gemini", fake_call_gemini)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Plan route to KLCC"},
    )

    assert response.status_code == 200
    assert attempted_keys == ["key-one", "key-two"]
    assert "route planning" in response.json()["answer"]


def test_chatbox_shows_friendly_message_when_all_gemini_keys_exhausted(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai.settings, "gemini_api_key_primary", "key-one", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_key_secondary", "key-two", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_keys", "key-three", raising=False)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    attempted_keys = []

    def fake_call_gemini(message: str, api_key: str, prompt_guardrail: bool) -> str:
        attempted_keys.append(api_key)
        raise _rate_limit_error()

    monkeypatch.setattr(ai, "_call_gemini", fake_call_gemini)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Can you help me plan a route?"},
    )

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert attempted_keys == ["key-one", "key-two", "key-three"]
    assert "AI usage limit is temporarily used up" in answer
    assert "route planning" in answer

    attempted_keys.clear()
    second_response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Can you help me plan a route?"},
    )
    assert second_response.status_code == 200
    assert attempted_keys == []
    assert "AI usage limit is temporarily used up" in second_response.json()["answer"]


def test_gemini_prompt_includes_project_capability_boundary(monkeypatch) -> None:
    captured_payload = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "I can help.\n- Plan a route.\nYou can enter your destination first."}
                            ]
                        }
                    }
                ]
            }

    def fake_post(url: str, json: dict, timeout: float) -> FakeResponse:
        captured_payload["json"] = json
        return FakeResponse()

    monkeypatch.setattr(ai.httpx, "post", fake_post)

    ai._call_gemini(
        message="Can I buy ticket in ElderGo?",
        api_key="dummy-key",
        prompt_guardrail=True,
    )

    prompt = captured_payload["json"]["contents"][0]["parts"][0]["text"]
    assert "Project capability boundary for ElderGo KL" in prompt
    assert "do not force labels like Summary, Steps, or Next step" in prompt
    assert "Implemented in the app" in prompt
    assert "Not implemented in the app" in prompt
    assert "buying tickets" in prompt
    assert "view a ticket-buying guide" in prompt


def test_chatbox_rewrites_unsupported_app_ticket_purchase(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail: (
            "Summary: You can buy tickets in this app.\n"
            "- Open ElderGo and pay for the ticket.\n"
            "Next step: purchase through ElderGo."
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "How to buy ticket?"},
    )

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert "only provides ticket-buying information" in answer
    assert "cannot sell tickets" in answer
    assert "You can view the ticket guide before you travel" in answer
    assert "buy tickets in this app" not in answer.lower()
    assert "purchase through eldergo" not in answer.lower()
    assert "Next step:" not in answer


def test_chatbox_rewrites_chinese_app_ticket_purchase(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail: (
            "总结：你可以在 App 买票。\n"
            "- 在 ElderGo 里付款。\n"
            "下一步：打开 App 购买车票。"
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "怎么买票？"},
    )

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert "只提供买票指南" in answer
    assert "不能在 App 内买票" in answer
    assert "售票机" in answer or "柜台" in answer
    assert "建议先打开买票指南" in answer
    assert "下一步：" not in answer
    assert "在 App 买票" not in answer.replace("不能在 App 内买票", "")


def test_chatbox_rewrites_unsupported_concession_application(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail: (
            "Summary: ElderGo lets you apply for senior concession in this app.\n"
            "- Submit the form in ElderGo.\n"
            "Next step: apply concession in this app."
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Can I apply for concession?"},
    )

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert "only provides senior concession information" in answer
    assert "cannot submit an application in the app" in answer
    assert "You can view the concession guide first" in answer
    assert "apply concession in this app" not in answer.lower()
    assert "Next step:" not in answer


def test_chatbox_long_paragraph_is_normalized(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail: (
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
    payload = response.json()
    answer = payload["answer"]
    lines = [line for line in answer.splitlines() if line.strip()]
    assert len(lines) >= 3
    assert any(line.startswith("- ") for line in lines)
    assert "You can tell me your start point and destination" in answer
    assert "Next step:" not in answer
    _assert_no_rag_metadata(payload)


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
    assert "Ask about one of these topics" in payload["answer"]
    assert "Next step:" not in payload["answer"]
    _assert_no_rag_metadata(payload)


def test_chatbox_fallback_message_when_ai_unavailable(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)

    def raise_network_error(message: str, api_key: str, prompt_guardrail: bool) -> str:
        raise RuntimeError("network down")

    monkeypatch.setattr(ai, "_call_gemini", raise_network_error)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Is train running now?"},
    )

    assert response.status_code == 200
    payload = response.json()
    answer = payload["answer"]
    assert "temporarily unavailable" in answer
    assert "Please try again in 1 minute" in answer
    assert "Next step:" not in answer
    _assert_no_rag_metadata(payload)


def test_chatbox_fallback_language_matches_user(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_in_scope", lambda message: True)
    monkeypatch.setattr(
        ai,
        "_call_gemini",
        lambda message, api_key, prompt_guardrail: (_ for _ in ()).throw(RuntimeError("timeout")),
    )

    client = TestClient(app)

    zh = client.post("/ai/conversations/conv_test/messages", json={"message": "现在可以去医院吗？"})
    ms = client.post("/ai/conversations/conv_test/messages", json={"message": "bagaimana pergi ke stesen"})
    en = client.post("/ai/conversations/conv_test/messages", json={"message": "How to buy ticket?"})

    assert "请 1 分钟后再试" in zh.json()["answer"]
    assert "Cuba semula dalam 1 minit" in ms.json()["answer"]
    assert "Please try again in 1 minute" in en.json()["answer"]
    _assert_no_rag_metadata(zh.json())
    _assert_no_rag_metadata(ms.json())
    _assert_no_rag_metadata(en.json())
