from app.services.route_station_images_service import (
    get_route_station_image_map,
    get_route_step_images,
    reload_route_station_images_cache,
)


def setup_function() -> None:
    reload_route_station_images_cache()


def test_klcc_monash_step_images_grouped_by_step_number() -> None:
    route_key = "klcc|monash university malaysia"
    image_map = get_route_station_image_map(route_key)

    assert image_map["step:1"] == [
        {
            "path": "/route-images/klcc-monash/step-01-01-entrance-exterior.jpg",
            "caption": "You are at the KLCC station entrance (Suria mall). Go inside when you are ready.",
        },
        {
            "path": "/route-images/klcc-monash/step-01-02-tap-in.jpg",
            "caption": "Tap your travel card on the reader to enter the station.",
        },
    ]
    assert image_map["step:5"][-1] == {
        "path": "/route-images/klcc-monash/step-05-03-monash-campus.jpg",
        "caption": "You have arrived at Monash University campus.",
    }


def test_get_route_step_images_by_number() -> None:
    route_key = "klcc|monash university malaysia"
    images = get_route_step_images(route_key, 4)

    assert images[0]["path"] == "/route-images/klcc-monash/step-04-01-usj7-platform-board.jpg"
    assert images[0]["caption"] == "This is the bus platform at USJ 7. Wait here for the BRT."
