from app.schemas.places import PlaceSuggestion
from app.services.places_service import is_transit_station_types, pick_autocomplete_place_id


def test_is_transit_station_types_accepts_rail_and_bus() -> None:
    assert is_transit_station_types(["train_station", "point_of_interest"])
    assert is_transit_station_types(["bus_station"])
    assert not is_transit_station_types(["restaurant", "point_of_interest"])
    assert not is_transit_station_types([])


def test_pick_autocomplete_place_id_matches_kl_sentral_case_insensitive() -> None:
    suggestions = [
        PlaceSuggestion(
            description="KL Sentral, Kuala Lumpur, Federal Territory of Kuala Lumpur, Malaysia",
            place_id="ChIJ9dMoUktJzDER2C5eos1Vfm4",
            main_text="KL Sentral",
            secondary_text="Kuala Lumpur, Federal Territory of Kuala Lumpur, Malaysia",
            types=["train_station", "transit_station"],
        ),
        PlaceSuggestion(
            description="KL Sentral Bus Station, Kuala Lumpur, Malaysia",
            place_id="ChIJp_kvRMBJzDERNwU4WTrkwt4",
            main_text="KL Sentral Bus Station",
            types=["bus_station"],
        ),
    ]
    assert pick_autocomplete_place_id("KL SENTRAL", suggestions) == "ChIJ9dMoUktJzDER2C5eos1Vfm4"


def test_pick_autocomplete_place_id_transit_only_skips_non_transit() -> None:
    suggestions = [
        PlaceSuggestion(
            description="USJ7, Subang Jaya, Selangor, Malaysia",
            place_id="ChIJwrong",
            main_text="USJ7",
            types=["restaurant", "food"],
        ),
        PlaceSuggestion(
            description="USJ7 LRT Station, Subang Jaya, Selangor, Malaysia",
            place_id="ChIJright",
            main_text="USJ7 LRT Station",
            types=["transit_station", "train_station"],
        ),
    ]
    assert pick_autocomplete_place_id("USJ7", suggestions, transit_only=True) == "ChIJright"


def test_pick_autocomplete_place_id_returns_none_without_match() -> None:
    suggestions = [
        PlaceSuggestion(
            description="Pavilion Kuala Lumpur, Malaysia",
            place_id="ChIJother",
            main_text="Pavilion Kuala Lumpur",
        ),
    ]
    assert pick_autocomplete_place_id("KL Sentral", suggestions) is None
