"""Unit tests for structured chat answer blocks."""

from app.schemas.ai import ChatBlock, KeyValueRow, SourceLink
from app.services.chat_blocks_service import (
    ALLOWED_SOURCE_URLS,
    blocks_ask_station,
    blocks_ask_weather_location,
    blocks_for_guide,
    blocks_for_station,
    blocks_for_weather,
    blocks_route_ready,
    blocks_to_plain_text,
    dedupe_sources_blocks,
    parse_gemini_blocks_json,
    sanitize_source_links,
)


def test_blocks_for_station_includes_key_values_and_sources() -> None:
    class FakeDetail:
        name = "SUBANG JAYA"
        accessibility_status = "supported"
        routes = ["KJL"]
        known_facilities = ["Lift"]
        station_facilities = None
        station_hours_summary = (
            "Station open: 06:00 am\n"
            "Station closed: 12:00 am (Mon - Sat) / 11:25 pm (Sunday & PH)\n"
            "Last Train to Gombak: 12:12 am (Mon - Sat) / 11:42 pm (Sunday & PH)"
        )
        station_address = "Jalan SS15"
        facility_source_url = "https://www.mrt.com.my/en/rail/klang-valley/sbk/subang-jaya-station"

    blocks = blocks_for_station(FakeDetail(), "en")
    types = [b.type for b in blocks]
    assert "heading" in types
    assert "key_values" in types
    assert "hours" in types
    assert "callout" in types
    assert "sources" in types
    assert "SUBANG JAYA" in blocks_to_plain_text(blocks)


def test_dedupe_sources_blocks_merges_duplicates() -> None:
    duplicate = [
        ChatBlock(type="paragraph", text="Summary"),
        ChatBlock(
            type="sources",
            text="Official information",
            links=[SourceLink(title="OpenWeather", url=ALLOWED_SOURCE_URLS["openweather"], org="OpenWeather")],
        ),
        ChatBlock(
            type="sources",
            text="Official information",
            links=[SourceLink(title="OpenWeather", url=ALLOWED_SOURCE_URLS["openweather"], org="OpenWeather")],
        ),
    ]
    merged = dedupe_sources_blocks(duplicate)
    source_blocks = [b for b in merged if b.type == "sources"]
    assert len(source_blocks) == 1
    assert source_blocks[0].links
    assert len(source_blocks[0].links) == 1


def test_blocks_ask_prompts_build_without_error() -> None:
    station = blocks_ask_station("en")
    weather = blocks_ask_weather_location("en")
    assert station[0].type == "heading"
    assert weather[0].type == "heading"
    assert any(b.type == "callout" for b in station)


def test_blocks_for_ticket_guide_has_myrapid_source() -> None:
    blocks = blocks_for_guide("ticket_guide", "en")
    source_blocks = [b for b in blocks if b.type == "sources"]
    assert source_blocks
    urls = [link.url for block in source_blocks for link in block.links or []]
    assert ALLOWED_SOURCE_URLS["myrapid"] in urls


def test_blocks_for_weather_structured() -> None:
    class FakeForecast:
        destination_name = "Subang Jaya"
        temperature_c = 31
        feels_like_c = 35
        weather_description = "light rain"
        risk_level = "rain"
        senior_advice = ["Bring an umbrella.", "Allow extra time."]

    blocks = blocks_for_weather(FakeForecast(), "en")
    types = [b.type for b in blocks]
    assert types[0] == "heading"
    assert "callout" in types
    assert "bullets" in types
    assert "sources" in types


def test_blocks_route_ready_labels() -> None:
    blocks = blocks_route_ready("Monash University Malaysia", "KLCC", "now", "en")
    plain = blocks_to_plain_text(blocks)
    assert "Monash University Malaysia" in plain
    assert "KLCC" in plain
    assert "From:" in plain
    assert "To:" in plain
    assert any(b.type == "key_values" for b in blocks)
    assert not any(b.type == "sources" for b in blocks)
    assert "Official information" not in plain
    assert "Google Maps" not in plain


def test_parse_gemini_blocks_json_sanitizes_bad_urls() -> None:
    raw = """
    {
      "blocks": [
        {"type": "heading", "text": "Tickets"},
        {"type": "bullets", "items": ["Use Touch n Go at gates"]},
        {
          "type": "sources",
          "links": [
            {"title": "MyRapid", "url": "https://myrapid.com.my/", "org": "MyRapid"},
            {"title": "Bad", "url": "https://evil.example/", "org": "Evil"}
          ]
        }
      ]
    }
    """
    blocks = parse_gemini_blocks_json(raw, "en")
    assert blocks is not None
    sources = next(b for b in blocks if b.type == "sources")
    assert sources.links
    assert len(sources.links) == 1
    assert sources.links[0].url == ALLOWED_SOURCE_URLS["myrapid"]


def test_sanitize_source_links_allowlist() -> None:
    cleaned = sanitize_source_links(
        [
            SourceLink(title="OK", url="https://myrapid.com.my/", org="MyRapid"),
            SourceLink(title="NO", url="https://not-allowed.test/", org="X"),
        ]
    )
    assert len(cleaned) == 1


def test_blocks_to_plain_text_key_values() -> None:
    blocks = [
        ChatBlock(
            type="key_values",
            rows=[KeyValueRow(label="Lines", value="KJL", emphasis="neutral")],
        )
    ]
    assert "Lines: KJL" in blocks_to_plain_text(blocks)


def test_blocks_exploratory_places_includes_sources() -> None:
    from app.services.chat_blocks_service import blocks_exploratory_places

    blocks = blocks_exploratory_places(
        [{"label": "Cafe A", "name": "Cafe A", "address": "KLCC"}],
        "en",
        search_label="cafes near KLCC",
    )
    assert any(block.type == "numbered" for block in blocks)
    assert any(block.type == "sources" for block in blocks)


def test_blocks_maps_grounding_places_place_cards() -> None:
    from app.services.chat_blocks_service import blocks_maps_grounding_places

    blocks = blocks_maps_grounding_places(
        [{"title": "Example Cafe", "url": "https://maps.google.com/?cid=1"}],
        "en",
        summary="A quiet spot with shade.",
    )
    place_cards = [block for block in blocks if block.type == "place_cards"]
    assert len(place_cards) == 1
    assert place_cards[0].links
    assert place_cards[0].links[0].title == "Example Cafe"
