"""Tests for chatbot place query validation."""

from app.services.ai_route_parse_service import (
    is_plausible_place_query,
    is_unclear_place_reply,
    place_matches_user_query,
)


def test_gibberish_mixed_script_not_plausible() -> None:
    assert not is_plausible_place_query("为AA他和人")
    assert is_unclear_place_reply("为AA他和人")


def test_valid_place_queries() -> None:
    assert is_plausible_place_query("Subang Jaya")
    assert is_plausible_place_query("KLCC")
    assert is_plausible_place_query("Petaling Jaya")


def test_short_aa_token_does_not_match_unrelated_place() -> None:
    assert not place_matches_user_query(
        "为AA他和人",
        place_name="AA Aviation Sdn Bhd",
        formatted_address="Bukit Bintang, Kuala Lumpur",
    )


def test_subang_jaya_matches_place_name() -> None:
    assert place_matches_user_query(
        "Subang Jaya",
        place_name="Subang Jaya",
        formatted_address="Subang Jaya, Selangor, Malaysia",
    )
