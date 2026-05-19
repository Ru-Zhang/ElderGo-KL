import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.places import PlaceDetail
from app.services.ai_exploratory_poi_service import (
    is_exploratory_poi_message,
    resolve_exploratory_poi,
)


def test_exploratory_poi_resolves_places(monkeypatch) -> None:
    async def fake_search(_query: str, limit: int = 5):
        return [
            PlaceDetail(
                display_name="Wheelchair Friendly Cafe, KLCC",
                google_place_id="cafe_1",
                lat=3.157,
                lon=101.712,
                name="Wheelchair Friendly Cafe",
            )
        ]

    monkeypatch.setattr("app.services.places_service.search_places_kv", fake_search)
    monkeypatch.setattr("app.services.ai_exploratory_poi_service.search_places_kv", fake_search)

    message = "Are there wheelchair friendly cafes near KLCC?"
    assert is_exploratory_poi_message(message)
    result = asyncio.run(resolve_exploratory_poi(message, "en"))
    assert result is not None
    assert result.response_source == "api"
    assert any(block.type == "numbered" for block in (result.answer_blocks or []))


def test_build_places_search_query_chinese_klcc_cafe() -> None:
    from app.services.ai_exploratory_poi_service import build_places_search_query

    query = build_places_search_query("KLCC 附近有没有遮阳、步行少的咖啡馆？")
    assert query == "cafe near Kuala Lumpur City Centre"


def test_exploratory_poi_skips_short_messages() -> None:
    assert not is_exploratory_poi_message("hi")
    result = asyncio.run(resolve_exploratory_poi("hi", "en"))
    assert result is None


def test_clinic_in_sunway_area_is_exploratory() -> None:
    from app.services.ai_exploratory_poi_service import (
        build_places_search_query,
        is_area_poi_query,
        is_exploratory_poi_message,
    )

    message = "clinic in sunway area"
    assert is_area_poi_query(message)
    assert is_exploratory_poi_message(message)
    query = build_places_search_query(message)
    assert "clinic" in query.lower()
    assert "sunway" in query.lower()


def test_short_cafe_near_klcc() -> None:
    from app.services.ai_exploratory_poi_service import is_exploratory_poi_message

    assert is_exploratory_poi_message("cafe near KLCC")


def test_enroute_rest_not_plan_route_pair() -> None:
    from app.services.ai_exploratory_poi_service import (
        build_enroute_places_search,
        is_enroute_rest_exploratory,
        parse_enroute_endpoints,
    )
    from app.services.ai_route_parse_service import try_rule_route_pair

    message = "从 Monash 到 Sunway 中途有没有适合休息的地方？"
    assert parse_enroute_endpoints(message) == ("Monash", "Sunway")
    assert try_rule_route_pair(message) == ("Monash", "Sunway")
    assert is_enroute_rest_exploratory(message)
    assert "Sunway" in build_enroute_places_search(message, "Monash", "Sunway")


def test_route_sentence_not_unclear_place() -> None:
    from app.services.ai_intent_service import extract_route_endpoints
    from app.services.ai_route_parse_service import is_unclear_place_reply

    message = (
        "i want to go from monash university malaysia to kuala lumpur airport 1 "
        "at the evening, could you please recommend a route for me? thank you"
    )
    origin, dest = extract_route_endpoints(message)
    assert origin == "monash university malaysia"
    assert dest == "kuala lumpur airport 1"
    assert not is_unclear_place_reply(message)


def test_senior_common_poi_defers_to_gemini() -> None:
    from app.services.ai_exploratory_poi_service import (
        build_places_search_query,
        is_senior_common_poi_message,
        should_prefer_gemini_recommendation,
    )

    message = "please tell me which hospital is close to monash uni"
    assert is_senior_common_poi_message(message)
    assert should_prefer_gemini_recommendation(message)
    assert build_places_search_query(message) == "hospital near monash uni"
    result = asyncio.run(resolve_exploratory_poi(message, "en"))
    assert result is None


def test_enroute_rest_resolves_places(monkeypatch) -> None:
    async def fake_search(_query: str, limit: int = 5):
        return [
            PlaceDetail(
                display_name="Rest Stop, Sunway",
                google_place_id="rest_1",
                lat=3.07,
                lon=101.60,
                name="Sunway Rest Stop",
                formatted_address="Sunway City, Selangor",
            )
        ]

    monkeypatch.setattr("app.services.places_service.search_places_kv", fake_search)
    monkeypatch.setattr("app.services.ai_exploratory_poi_service.search_places_kv", fake_search)

    message = "从 Monash 到 Sunway 中途有没有适合休息的地方？"
    result = asyncio.run(resolve_exploratory_poi(message, "zh"))
    assert result is not None
    assert result.intent == "enroute_rest_poi"
    assert result.response_source == "api"
