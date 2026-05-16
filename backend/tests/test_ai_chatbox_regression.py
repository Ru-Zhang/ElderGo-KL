import sys
from pathlib import Path
from typing import Any

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.v1.endpoints import ai
from app.main import app
from app.services import gemini_client


def _set_guardrail(monkeypatch) -> None:
    gemini_client.GEMINI_KEY_POOL = gemini_client.GeminiKeyPool()
    ai.GEMINI_KEY_POOL = gemini_client.GEMINI_KEY_POOL
    monkeypatch.setattr(ai.settings, "ai_guardrail_enabled", True, raising=False)
    monkeypatch.setattr(ai.settings, "ai_guardrail_mode", "hybrid", raising=False)
    monkeypatch.setattr(ai.settings, "ai_guardrail_strict", False, raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_key_primary", "dummy-key", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_key_secondary", None, raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_keys", "", raising=False)


def _gemini_api_payload(text: str) -> dict[str, Any]:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def _mock_call_with_key_pool_text(monkeypatch, text: str) -> None:
    async def fake_call(_prompt: str, **kwargs: Any) -> tuple[dict[str, Any] | None, str | None]:
        return _gemini_api_payload(text), None

    monkeypatch.setattr(ai, "call_with_key_pool", fake_call)


def _mock_call_with_key_pool_unavailable(monkeypatch) -> None:
    async def fake_call(_prompt: str, **kwargs: Any) -> tuple[dict[str, Any] | None, str | None]:
        return None, "unavailable"

    monkeypatch.setattr(ai, "call_with_key_pool", fake_call)


def _mock_call_with_key_pool_quota(monkeypatch) -> None:
    async def fake_call(_prompt: str, **kwargs: Any) -> tuple[dict[str, Any] | None, str | None]:
        return None, "quota_exhausted"

    monkeypatch.setattr(ai, "call_with_key_pool", fake_call)


def _mock_call_with_key_pool_tracker(monkeypatch) -> list[bool]:
    calls: list[bool] = []

    async def fake_call(_prompt: str, **kwargs: Any) -> tuple[dict[str, Any] | None, str | None]:
        calls.append(True)
        return _gemini_api_payload("should not be used"), None

    monkeypatch.setattr(ai, "call_with_key_pool", fake_call)
    return calls


def _assert_no_rag_metadata(payload: dict) -> None:
    assert "grounded" not in payload
    assert "used_data_keys" not in payload


def _rate_limit_error() -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.test/gemini")
    response = httpx.Response(429, request=request)
    return httpx.HTTPStatusError("quota exhausted", request=request, response=response)


def test_chatbox_response_includes_natural_action_suggestion(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)
    _mock_call_with_key_pool_text(
        monkeypatch,
        "Summary: Use the Kelana Jaya line.\n"
        "- Start at KL Sentral.\n"
        "- Stop at Pasar Seni.",
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "What should elderly travellers prepare before taking the MRT in Kuala Lumpur?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["in_scope"] is True
    assert "You can tell me your start point and destination" in payload["answer"]
    assert "Next step:" not in payload["answer"]
    _assert_no_rag_metadata(payload)


def test_chatbox_gemini_prompt_includes_grounded_context(monkeypatch) -> None:
    from app.services.ai_grounding_service import GroundedContext

    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)
    prompts: list[str] = []

    monkeypatch.setattr(
        ai,
        "build_grounded_context",
        lambda **kwargs: GroundedContext(
            intent="help_static",
            grounded=True,
            response_source="static_help",
            used_data_keys=["station"],
            facts=["KL Sentral has step-free access."],
        ),
    )

    async def fake_call(prompt: str, **kwargs: Any) -> tuple[dict[str, Any] | None, str | None]:
        prompts.append(prompt)
        return _gemini_api_payload("Summary: I can help.\n- Tell me where you start."), None

    monkeypatch.setattr(ai, "call_with_key_pool", fake_call)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "What should elderly travellers prepare before taking the MRT in Kuala Lumpur?",
            "has_current_route": True,
            "selected_station_id": "legacy-station",
        },
    )

    assert response.status_code == 200
    assert prompts
    assert "Verified ElderGo data" in prompts[0]
    assert "KL Sentral has step-free access" in prompts[0]
    _assert_no_rag_metadata(response.json())


def test_chatbox_switches_to_next_gemini_key_after_rate_limit(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai.settings, "gemini_api_key_primary", "key-one", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_key_secondary", "key-two", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_keys", "key-two,key-three", raising=False)
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)
    attempted_keys: list[str] = []

    def fake_generate(*, user_text: str, api_key: str, **kwargs: Any) -> dict[str, Any]:
        attempted_keys.append(api_key)
        if api_key == "key-one":
            raise _rate_limit_error()
        return _gemini_api_payload(
            "I can help with route planning.\nYou can enter your destination first."
        )

    monkeypatch.setattr(gemini_client, "generate_content", fake_generate)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "What should I prepare before taking the MRT?"},
    )

    assert response.status_code == 200
    assert attempted_keys == ["key-one", "key-two"]
    assert "route planning" in response.json()["answer"]


def test_chatbox_shows_friendly_message_when_all_gemini_keys_exhausted(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai.settings, "gemini_api_key_primary", "key-one", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_key_secondary", "key-two", raising=False)
    monkeypatch.setattr(ai.settings, "gemini_api_keys", "key-three", raising=False)
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)
    attempted_keys: list[str] = []

    def fake_generate(*, user_text: str, api_key: str, **kwargs: Any) -> dict[str, Any]:
        attempted_keys.append(api_key)
        raise _rate_limit_error()

    monkeypatch.setattr(gemini_client, "generate_content", fake_generate)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "What should elderly travellers know about MRT etiquette?"},
    )

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert attempted_keys == ["key-one", "key-two", "key-three"]
    assert "AI usage limit is temporarily used up" in answer
    assert "route planning" in answer

    attempted_keys.clear()
    second_response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "What should elderly travellers know about MRT etiquette?"},
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

    monkeypatch.setattr(gemini_client.httpx, "post", fake_post)

    gemini_client.generate_content(
        user_text=ai._build_gemini_user_prompt(
            "Can I buy ticket in ElderGo?",
            prompt_guardrail=True,
            use_maps_grounding=False,
            grounded_facts=[],
        ),
        api_key="dummy-key",
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
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)
    _mock_call_with_key_pool_text(
        monkeypatch,
        "Summary: You can buy tickets in this app.\n"
        "- Open ElderGo and pay for the ticket.\n"
        "Next step: purchase through ElderGo.",
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "MRT fare from KL Sentral to KLCC and can I buy tickets in this app?"},
    )

    assert response.status_code == 200
    payload = response.json()
    answer = payload["answer"]
    assert "cannot sell tickets" in answer.lower()
    assert "ticket guide" in answer.lower()
    assert payload.get("answer_blocks")
    assert "buy tickets in this app" not in answer.lower()
    assert "purchase through eldergo" not in answer.lower()
    assert "Next step:" not in answer


def test_chatbox_rewrites_chinese_app_ticket_purchase(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)
    _mock_call_with_key_pool_text(
        monkeypatch,
        "总结：你可以在 App 买票。\n- 在 ElderGo 里付款。\n下一步：打开 App 购买车票。",
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "我可以在 ElderGo App 里面直接买票和付款吗？请告诉我详细步骤。"},
    )

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert "ticket-buying information" in answer
    assert "cannot sell tickets" in answer
    assert "ticket guide" in answer.lower()
    assert "Next step:" not in answer
    assert "buy tickets in the app" not in answer.lower()


def test_chatbox_rewrites_unsupported_concession_application(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)
    _mock_call_with_key_pool_text(
        monkeypatch,
        "Summary: ElderGo lets you apply for senior concession in this app.\n"
        "- Submit the form in ElderGo.\n"
        "Next step: apply concession in this app.",
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Can I apply for concession?"},
    )

    assert response.status_code == 200
    payload = response.json()
    answer = payload["answer"]
    assert "concession" in answer.lower()
    assert "cannot" in answer.lower() and "app" in answer.lower()
    assert "concession guide" in answer.lower()
    assert payload.get("answer_blocks")
    assert "apply concession in this app" not in answer.lower()
    assert "Next step:" not in answer


def test_chatbox_long_paragraph_is_normalized(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)
    _mock_call_with_key_pool_text(
        monkeypatch,
        "Take the train from KL Sentral to Pasar Seni and follow station signs carefully "
        "because the station may be crowded. Please prepare your card first and avoid "
        "rushing when changing platforms. If you need help, ask station staff near the gate.",
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
    monkeypatch.setattr(ai, "is_travel_related", lambda message: False)

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
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)

    _mock_call_with_key_pool_unavailable(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Is the MRT train running on time right now at KL Sentral?"},
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
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)
    _mock_call_with_key_pool_unavailable(monkeypatch)

    client = TestClient(app)

    zh = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "在巴生谷搭地铁时，长者应该注意哪些安全事项？请给我一些实用建议。",
            "ui_language": "EN",
        },
    )
    ms = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "Bagaimana saya boleh merancang perjalanan MRT yang selamat untuk warga emas ke stesen?",
            "ui_language": "BM",
        },
    )
    en = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "Is the MRT train running on time right now at KL Sentral?",
            "ui_language": "EN",
        },
    )

    assert "Please try again in 1 minute" in zh.json()["answer"]
    assert "Cuba semula dalam 1 minit" in ms.json()["answer"]
    assert "Please try again in 1 minute" in en.json()["answer"]
    _assert_no_rag_metadata(zh.json())
    _assert_no_rag_metadata(ms.json())
    _assert_no_rag_metadata(en.json())


def test_chatbox_ticket_chip_message_returns_action_without_gemini(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "How do I buy train tickets?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert gemini_called == []
    assert payload["in_scope"] is True
    assert any(action["type"] == "open_ticket_guide" for action in payload["actions"])


def test_chatbox_ticket_guide_returns_action_without_gemini(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "How to buy ticket?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert gemini_called == []
    assert payload["in_scope"] is True
    assert any(action["type"] == "open_ticket_guide" for action in payload["actions"])
    assert "cannot sell tickets" in payload["answer"].lower()
    assert payload.get("answer_blocks")
    assert any(block["type"] == "sources" for block in payload["answer_blocks"])


def test_chatbox_out_of_scope_skips_gemini_in_hybrid_mode(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Give me crypto investment tips"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["in_scope"] is False
    assert gemini_called == []
    assert "Ask about one of these topics" in payload["answer"]


def test_chatbox_weather_chip_asks_location_skips_gemini(monkeypatch) -> None:
    from app.schemas.weather import WeatherForecastResponse
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)

    async def fake_weather(payload):
        return WeatherForecastResponse(
            destination_name=payload.destination_name,
            forecast_time="2026-05-15 12:00:00",
            period_label="now",
            temperature_c=30.0,
            feels_like_c=31.0,
            humidity_percent=60,
            rain_mm=0.0,
            precipitation_probability_percent=5,
            wind_kmh=6.0,
            weather_main="Clouds",
            weather_description="partly cloudy",
            weather_icon="02d",
            risk_level="clear",
            senior_advice=["Comfortable for travel."],
        )

    monkeypatch.setattr(ai_flow_service, "get_weather_forecast", fake_weather)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Check the weather"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert gemini_called == []
    assert payload["in_scope"] is True
    assert payload["chat_flow"] == "weather"
    assert "Kuala Lumpur" in payload["answer"] or "Lembah Klang" in payload["answer"] or "巴生谷" in payload["answer"]
    answer_lower = payload["answer"].lower()
    assert any(
        token in answer_lower
        for token in ("where", "which", "place", "area", "kawasan")
    )


def test_chatbox_weather_intent_with_location_skips_gemini(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.schemas.weather import WeatherForecastResponse
    from app.services import ai_flow_service, ai_intent_service

    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)

    async def fake_places(_query, limit=5):
        return [
            PlaceDetail(
                display_name="KLCC, Kuala Lumpur",
                google_place_id="place_klcc",
                lat=3.157,
                lon=101.712,
                name="KLCC",
            )
        ]

    async def fake_weather(payload):
        name = payload.destination_name
        return WeatherForecastResponse(
            destination_name=name,
            forecast_time="2026-05-15 12:00:00",
            period_label="now",
            temperature_c=32.0,
            feels_like_c=34.0,
            humidity_percent=70,
            rain_mm=0.0,
            precipitation_probability_percent=10,
            wind_kmh=8.0,
            weather_main="Clouds",
            weather_description="partly cloudy",
            weather_icon="02d",
            risk_level="hot",
            senior_advice=["Bring water.", "Walk slowly."],
        )

    monkeypatch.setattr(ai_flow_service, "search_places_kv", fake_places)
    monkeypatch.setattr(ai_flow_service, "get_weather_forecast", fake_weather)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "What is the weather at KLCC?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert gemini_called == []
    assert payload["in_scope"] is True
    assert "Kuala Lumpur" in payload["answer"] or "Klang Valley" in payload["answer"]
    assert "KLCC" in payload["answer"]
    assert "Bring water" in payload["answer"] or "Travel tip" in payload["answer"]


def test_chatbox_route_planning_prefill_skips_gemini(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.services import ai_intent_service

    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)

    async def fake_places(query, limit=5):
        return [
            PlaceDetail(
                display_name=query,
                google_place_id=f"place_{query[:8]}",
                lat=3.13,
                lon=101.68,
                name=query,
            )
        ]

    monkeypatch.setattr(ai_intent_service, "search_places_kv", fake_places)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "from Monash University to KL Sentral"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert gemini_called == []
    assert payload["in_scope"] is True
    assert len(payload["actions"]) == 1
    action = payload["actions"][0]
    assert action["type"] == "compute_route"
    assert action["origin_name"]
    assert action["destination_name"]
    assert action.get("origin_lat") is not None
    assert "Your route is ready" in payload["answer"]
    assert "Monash University Malaysia" in payload["answer"]
    assert "KL Sentral" in payload["answer"]
    assert "Tap the button below" in payload["answer"]


def test_chatbox_route_planning_missing_destination_has_no_actions(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "from Monash University"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert gemini_called == []
    assert payload["in_scope"] is True
    assert payload["actions"] == []
    assert "Monash University" in payload["answer"]
    assert "where" in payload["answer"].lower()


def test_chatbox_from_to_route_uses_flow_not_gemini_even_if_classified_general(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.services import ai_flow_service, ai_intent_service

    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)

    async def fake_places(query, limit=5):
        return [
            PlaceDetail(
                display_name=query,
                google_place_id=f"place_{query[:8]}",
                lat=3.13,
                lon=101.68,
                name=query,
            )
        ]

    monkeypatch.setattr(ai_intent_service, "classify_intent", lambda message, request: "general")
    monkeypatch.setattr(ai_flow_service, "search_places_kv", fake_places)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "from Monash University to KL Sentral please help"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert gemini_called == []
    assert len(payload["actions"]) == 1
    assert payload["actions"][0]["type"] == "compute_route"


def test_chatbox_station_flow_asks_then_answers(monkeypatch) -> None:
    from app.schemas.locations import LocationDetail, LocationSummary
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)
    monkeypatch.setattr(
        ai_flow_service,
        "search_station_locations",
        lambda query, limit=20: [
            LocationSummary(
                id="station:kl_sentral",
                name="KL Sentral",
                type="rail_station",
                accessibility_status="supported",
                routes=["KJL"],
            )
        ],
    )
    monkeypatch.setattr(
        ai_flow_service,
        "get_location_detail_by_id",
        lambda location_id: LocationDetail(
            id=location_id,
            name="KL Sentral",
            type="rail_station",
            accessibility_status="supported",
            routes=["KJL"],
            known_facilities=["Wheelchair access"],
            station_hours_summary="5am - midnight",
        ),
    )

    client = TestClient(app)
    ask = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Tell me about a station"},
    )
    assert ask.status_code == 200
    ask_payload = ask.json()
    assert ask_payload["chat_flow"] == "station_info"
    assert gemini_called == []

    answer = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "KL Sentral",
            "chat_flow": "station_info",
            "flow_slots": ask_payload.get("flow_slots", {}),
        },
    )
    assert answer.status_code == 200
    answer_payload = answer.json()
    assert answer_payload["chat_flow"] is None
    assert any(action["type"] == "open_station_detail" for action in answer_payload["actions"])
    station_action = next(
        action for action in answer_payload["actions"] if action["type"] == "open_station_detail"
    )
    assert station_action.get("station_name") == "KL Sentral"
    assert "KL Sentral" in answer_payload["answer"]


def test_chatbox_weather_flow_rejects_outside_kv(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.schemas.weather import WeatherForecastResponse
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)

    async def fake_places(_query, limit=5):
        return [
            PlaceDetail(
                display_name="Penang",
                google_place_id="place_penang",
                lat=5.41,
                lon=100.33,
                name="Penang",
            )
        ]

    async def fake_weather(payload):
        return WeatherForecastResponse(
            destination_name=payload.destination_name,
            forecast_time="2026-05-15 12:00:00",
            period_label="now",
            temperature_c=30.0,
            feels_like_c=31.0,
            humidity_percent=60,
            rain_mm=0.0,
            precipitation_probability_percent=5,
            wind_kmh=6.0,
            weather_main="Clouds",
            weather_description="partly cloudy",
            weather_icon="02d",
            risk_level="clear",
            senior_advice=["Comfortable for travel."],
        )

    monkeypatch.setattr(ai_flow_service, "search_places_kv", fake_places)
    monkeypatch.setattr(ai_flow_service, "get_weather_forecast", fake_weather)

    client = TestClient(app)
    overview = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Check the weather"},
    )
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "Penang",
            "chat_flow": "weather",
            "flow_slots": overview.json().get("flow_slots", {"kv_overview_shown": "1"}),
        },
    )
    payload = response.json()
    assert payload["chat_flow"] == "weather"
    assert "Klang Valley" in payload["answer"] or "Lembah Klang" in payload["answer"]


def test_chatbox_plan_route_flow_returns_compute_route(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)

    async def fake_places(query, limit=5):
        return [
            PlaceDetail(
                display_name=query,
                google_place_id=f"pid_{query[:6]}",
                lat=3.1,
                lon=101.7,
                name=query,
            )
        ]

    monkeypatch.setattr(ai_flow_service, "search_places_kv", fake_places)

    client = TestClient(app)
    client.post("/ai/conversations/conv_test/messages", json={"message": "I want to plan a route"})
    client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Monash University", "chat_flow": "plan_route", "flow_slots": {}},
    )
    client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "KL Sentral",
            "chat_flow": "plan_route",
            "flow_slots": {
                "origin_resolved": '{"name":"Monash University","lat":3.1,"lon":101.7,"google_place_id":"p1"}'
            },
        },
    )
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "morning",
            "chat_flow": "plan_route",
            "flow_slots": {
                "origin_resolved": '{"name":"Monash University","lat":3.1,"lon":101.7,"google_place_id":"p1"}',
                "destination_resolved": '{"name":"KL Sentral","lat":3.1,"lon":101.7,"google_place_id":"p2"}',
            },
        },
    )
    payload = response.json()
    assert payload["chat_flow"] is None
    assert any(action["type"] == "compute_route" for action in payload["actions"])


def test_chatbox_weather_chip_switches_away_from_station_flow(monkeypatch) -> None:
    from app.schemas.weather import WeatherForecastResponse
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)

    async def fake_weather(payload):
        return WeatherForecastResponse(
            destination_name=payload.destination_name,
            forecast_time="2026-05-15 12:00:00",
            period_label="now",
            temperature_c=30.0,
            feels_like_c=31.0,
            humidity_percent=60,
            rain_mm=0.0,
            precipitation_probability_percent=5,
            wind_kmh=6.0,
            weather_main="Clouds",
            weather_description="partly cloudy",
            weather_icon="02d",
            risk_level="clear",
            senior_advice=["Comfortable for travel."],
        )

    monkeypatch.setattr(ai_flow_service, "get_weather_forecast", fake_weather)

    client = TestClient(app)
    client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "USJ7",
            "chat_flow": "station_info",
            "flow_slots": {"station_query": "USJ7"},
        },
    )
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "Check the weather",
            "chat_flow": "station_info",
            "flow_slots": {"station_query": "USJ7"},
        },
    )
    payload = response.json()
    assert "could not find that station" not in payload["answer"]
    assert payload["chat_flow"] == "weather"
    assert "Kuala Lumpur" in payload["answer"] or "Klang Valley" in payload["answer"]


def test_chatbox_plan_route_unclear_destination_reasks(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)

    async def fake_places(query, limit=5):
        return [
            PlaceDetail(
                display_name=query,
                google_place_id=f"pid_{query[:6]}",
                lat=3.1,
                lon=101.7,
                name=query,
            )
        ]

    monkeypatch.setattr(ai_flow_service, "search_places_kv", fake_places)

    client = TestClient(app)
    client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "?",
            "chat_flow": "plan_route",
            "flow_slots": {
                "origin_resolved": '{"name":"Monash University","lat":3.1,"lon":101.7,"google_place_id":"p1"}'
            },
        },
    )
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "?",
            "chat_flow": "plan_route",
            "flow_slots": {
                "origin_resolved": '{"name":"Monash University","lat":3.1,"lon":101.7,"google_place_id":"p1"}'
            },
        },
    )
    payload = response.json()
    assert payload["chat_flow"] == "plan_route"
    assert "too short" in payload["answer"].lower() or "pendek" in payload["answer"].lower()
    assert "Klang Valley only" not in payload["answer"]


def test_chatbox_plan_route_short_origin_gets_friendly_hint(monkeypatch) -> None:
    _set_guardrail(monkeypatch)

    client = TestClient(app)
    start = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "I want to plan a route"},
    )
    assert start.status_code == 200
    slots = start.json().get("flow_slots", {})

    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "d", "chat_flow": "plan_route", "flow_slots": slots},
    )
    payload = response.json()
    assert payload["chat_flow"] == "plan_route"
    assert "too short" in payload["answer"].lower()
    assert payload["answer"].count("Where will you start from?") == 0


def test_chatbox_station_subang_jaya_returns_detail_action(monkeypatch) -> None:
    """Regression: chatbot must use the same DB detail path as /locations/search."""
    from app.schemas.locations import LocationDetail, LocationSummary
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)
    monkeypatch.setattr(
        ai_flow_service,
        "search_station_locations",
        lambda query, limit=20: [
            LocationSummary(
                id="station:subang_jaya",
                name="SUBANG JAYA",
                type="rail_station",
                accessibility_status="supported",
                routes=["KJL"],
            )
        ],
    )
    monkeypatch.setattr(
        ai_flow_service,
        "get_location_detail_by_id",
        lambda location_id: LocationDetail(
            id=location_id,
            name="SUBANG JAYA",
            type="rail_station",
            accessibility_status="supported",
            routes=["KJL"],
            known_facilities=["Lift"],
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "subang jaya", "chat_flow": "station_info"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert gemini_called == []
    assert "SUBANG JAYA" in payload["answer"]
    assert any(action["type"] == "open_station_detail" for action in payload["actions"])


def test_chatbox_station_pick_exact_name_from_list(monkeypatch) -> None:
    from app.schemas.locations import LocationDetail, LocationSummary
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)

    def fake_search(query: str, limit: int = 20) -> list[LocationSummary]:
        return [
            LocationSummary(
                id="station:usj7",
                name="USJ 7",
                type="rail_station",
                accessibility_status="supported",
                routes=["KJL"],
            ),
            LocationSummary(
                id="station:usj7_dup",
                name="USJ 7",
                type="rail_station",
                accessibility_status="supported",
                routes=["KJL"],
            ),
            LocationSummary(
                id="station:kl_sentral",
                name="KL Sentral",
                type="rail_station",
                accessibility_status="supported",
                routes=["KJL"],
            ),
        ]

    monkeypatch.setattr(ai_flow_service, "search_station_locations", fake_search)
    monkeypatch.setattr(
        ai_flow_service,
        "get_location_detail_by_id",
        lambda location_id: LocationDetail(
            id=location_id,
            name="USJ 7" if "usj7" in location_id else "KL Sentral",
            type="rail_station",
            accessibility_status="supported",
            routes=["KJL"],
            known_facilities=["Lift"],
        ),
    )

    client = TestClient(app)
    pick = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "usj", "chat_flow": "station_info"},
    )
    pick_payload = pick.json()
    assert pick_payload["chat_flow"] == "station_info"
    assert "1." in pick_payload["answer"]
    assert pick_payload["answer"].count("USJ 7") == 1

    answer = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "USJ 7",
            "chat_flow": "station_info",
            "flow_slots": pick_payload["flow_slots"],
        },
    )
    answer_payload = answer.json()
    assert answer_payload["chat_flow"] is None
    assert "USJ 7" in answer_payload["answer"]
    assert any(action["type"] == "open_station_detail" for action in answer_payload["actions"])


def test_chatbox_plan_route_pick_by_number_after_disambiguation(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)

    async def fake_places(query, limit=5):
        return [
            PlaceDetail(
                display_name=(
                    "Kuala Lumpur Sentral, 50470 Kuala Lumpur, Federal Territory of Kuala Lumpur, Malaysia"
                ),
                google_place_id="pid_sentral_1",
                lat=3.13,
                lon=101.69,
                name="Kuala Lumpur Sentral",
            ),
            PlaceDetail(
                display_name=(
                    "LOT 1 & 2, LEVEL 1, Kuala Lumpur Sentral Station, Kuala Lumpur Sentral, "
                    "50470 Kuala Lumpur, Wilayah Persekutuan Kuala Lumpur"
                ),
                google_place_id="pid_sentral_shop",
                lat=3.13,
                lon=101.69,
                name="Kuala Lumpur Sentral Station",
            ),
            PlaceDetail(
                display_name="Kuala Lumpur City Centre, Kuala Lumpur, Malaysia",
                google_place_id="pid_klcc",
                lat=3.16,
                lon=101.71,
                name="Kuala Lumpur City Centre",
            ),
        ]

    monkeypatch.setattr(ai_flow_service, "search_places_kv", fake_places)
    monkeypatch.setattr(ai_flow_service, "lookup_known_kv_place", lambda _query: None)

    client = TestClient(app)
    start = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "I want to plan a route"},
    )
    slots = start.json().get("flow_slots", {})

    pick = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "kuala lumpur", "chat_flow": "plan_route", "flow_slots": slots},
    )
    pick_payload = pick.json()
    assert pick_payload["chat_flow"] == "plan_route"
    assert "origin_candidates" in pick_payload["flow_slots"]
    assert pick_payload["answer"].count("Kuala Lumpur Sentral") == 1
    assert "City Centre" in pick_payload["answer"] or "KLCC" in pick_payload["answer"]

    answer = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "1",
            "chat_flow": "plan_route",
            "flow_slots": pick_payload["flow_slots"],
        },
    )
    answer_payload = answer.json()
    assert "couldn't match" not in answer_payload["answer"].lower()
    assert "destination" in answer_payload["answer"].lower() or "Destinasi" in answer_payload["answer"]
    assert answer_payload["flow_slots"].get("origin_resolved")


def test_chatbox_plan_route_monash_uni_to_klcc_friendly_labels(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)

    async def fake_places(query, limit=5):
        q = query.lower()
        if "monash" in q:
            return [
                PlaceDetail(
                    display_name="Jalan Lagoon Selatan, Bandar Sunway, 47500 Subang Jaya, Selangor",
                    google_place_id="p1",
                    lat=3.07,
                    lon=101.6,
                    name="Monash University Malaysia",
                )
            ]
        return [
            PlaceDetail(
                display_name="Kuala Lumpur City Centre, Kuala Lumpur, Federal Territory of Kuala Lumpur, Malaysia",
                google_place_id="p2",
                lat=3.16,
                lon=101.71,
                name="Kuala Lumpur City Centre",
            )
        ]

    monkeypatch.setattr(ai_flow_service, "search_places_kv", fake_places)

    client = TestClient(app)
    client.post("/ai/conversations/conv_test/messages", json={"message": "I want to plan a route"})
    r1 = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "monash uni", "chat_flow": "plan_route"},
    )
    r2 = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "klcc",
            "chat_flow": "plan_route",
            "flow_slots": r1.json()["flow_slots"],
        },
    )
    r3 = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "now",
            "chat_flow": "plan_route",
            "flow_slots": r2.json()["flow_slots"],
        },
    )
    payload = r3.json()
    assert "Monash University Malaysia" in payload["answer"]
    assert "KLCC" in payload["answer"]
    assert "Jalan Lagoon" not in payload["answer"]
    action = next(a for a in payload["actions"] if a["type"] == "compute_route")
    assert action["origin_name"] == "Monash University Malaysia"
    assert action["destination_name"] == "KLCC"


def test_chatbox_plan_route_one_shot_from_to(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)

    async def fake_places(query, limit=5):
        return [
            PlaceDetail(
                display_name=query,
                google_place_id=f"pid_{query[:6]}",
                lat=3.1,
                lon=101.7,
                name=query,
            )
        ]

    monkeypatch.setattr(ai_flow_service, "search_places_kv", fake_places)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "from Monash University to KLCC"},
    )
    payload = response.json()
    assert any(action["type"] == "compute_route" for action in payload["actions"])
    assert payload["actions"][0]["origin_name"]
    assert payload["actions"][0]["destination_name"]


def test_chatbox_ticket_guide_returns_answer_blocks(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "How do I buy train tickets?"},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["answer_blocks"]
    assert any(block["type"] == "heading" for block in payload["answer_blocks"])
    assert any(block["type"] == "sources" for block in payload["answer_blocks"])


def test_chatbox_discount_question_returns_concession_guide(monkeypatch) -> None:
    _set_guardrail(monkeypatch)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "i wanna know the discount"},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["in_scope"] is True
    assert "Klang Valley travel only" not in payload["answer"]
    assert "senior" in payload["answer"].lower() or "warga emas" in payload["answer"].lower() or "长者" in payload["answer"]
    assert any(action["type"] == "open_concession_guide" for action in payload["actions"])
    assert gemini_called == []


def test_chatbox_plan_route_flow_returns_structured_blocks(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.services import ai_flow_service

    _set_guardrail(monkeypatch)

    async def fake_places(query, limit=5):
        q = query.lower()
        if "monash" in q:
            return [
                PlaceDetail(
                    display_name="Jalan Lagoon, Subang Jaya",
                    google_place_id="p1",
                    lat=3.07,
                    lon=101.6,
                    name="Monash University Malaysia",
                )
            ]
        return [
            PlaceDetail(
                display_name="Kuala Lumpur City Centre",
                google_place_id="p2",
                lat=3.16,
                lon=101.71,
                name="Kuala Lumpur City Centre",
            )
        ]

    monkeypatch.setattr(ai_flow_service, "search_places_kv", fake_places)

    client = TestClient(app)
    client.post("/ai/conversations/conv_test/messages", json={"message": "I want to plan a route"})
    r1 = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "monash uni", "chat_flow": "plan_route"},
    )
    r2 = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "klcc",
            "chat_flow": "plan_route",
            "flow_slots": r1.json()["flow_slots"],
        },
    )
    r3 = client.post(
        "/ai/conversations/conv_test/messages",
        json={
            "message": "now",
            "chat_flow": "plan_route",
            "flow_slots": r2.json()["flow_slots"],
        },
    )
    payload = r3.json()
    assert payload["answer_blocks"]
    assert any(block["type"] == "key_values" for block in payload["answer_blocks"])
    assert not any(block["type"] == "sources" for block in payload["answer_blocks"])


def test_chatbox_exploratory_poi_uses_places_not_gemini(monkeypatch) -> None:
    from app.schemas.places import PlaceDetail
    from app.services import ai_exploratory_poi_service, places_service

    _set_guardrail(monkeypatch)
    monkeypatch.setattr(ai, "is_travel_related", lambda message: True)
    gemini_called = _mock_call_with_key_pool_tracker(monkeypatch)

    async def fake_search(_query: str, limit: int = 5):
        return [
            PlaceDetail(
                display_name="Quiet Cafe, KLCC",
                google_place_id="cafe_q",
                lat=3.157,
                lon=101.712,
                name="Quiet Cafe",
            )
        ]

    monkeypatch.setattr(places_service, "search_places_kv", fake_search)
    monkeypatch.setattr(ai_exploratory_poi_service, "search_places_kv", fake_search)

    client = TestClient(app)
    response = client.post(
        "/ai/conversations/conv_test/messages",
        json={"message": "Any quiet cafes with shade near KLCC for a rest stop?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert gemini_called == []
    assert payload.get("response_source") == "api"
    assert any(block["type"] == "numbered" for block in payload.get("answer_blocks") or [])
