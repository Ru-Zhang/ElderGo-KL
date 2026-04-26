from fastapi import APIRouter

from app.schemas.locations import LocationDetail, LocationSummary

router = APIRouter()

DEMO_LOCATIONS: list[LocationDetail] = [
    LocationDetail(
        id="kl-sentral",
        name="KL Sentral",
        lat=3.1341,
        lon=101.6862,
        accessibility_status="unknown",
        confidence="unknown",
        note="Demo record only. Verify accessibility with imported station profile data.",
        routes=["KTM", "LRT", "MRT", "Monorail"],
        source_list=["frontend_demo_seed"],
    ),
    LocationDetail(
        id="pasar-seni",
        name="Pasar Seni",
        lat=3.1422,
        lon=101.6955,
        accessibility_status="unknown",
        confidence="unknown",
        note="Demo record only. Verify accessibility with imported station profile data.",
        routes=["LRT", "MRT"],
        source_list=["frontend_demo_seed"],
    ),
    LocationDetail(
        id="bukit-bintang",
        name="Bukit Bintang",
        lat=3.1468,
        lon=101.7113,
        accessibility_status="unknown",
        confidence="unknown",
        note="Demo record only. Verify accessibility with imported station profile data.",
        routes=["MRT", "Monorail"],
        source_list=["frontend_demo_seed"],
    ),
    LocationDetail(
        id="sunu-monash",
        name="SunU-Monash",
        lat=3.0654,
        lon=101.6036,
        accessibility_status="unknown",
        confidence="unknown",
        note="Demo record only. Verify accessibility with imported station profile data.",
        routes=["BRT"],
        source_list=["frontend_demo_seed"],
    ),
]


@router.get("/popular", response_model=list[LocationSummary])
def popular_locations() -> list[LocationSummary]:
    return [LocationSummary(**location.model_dump()) for location in DEMO_LOCATIONS[:4]]


@router.get("/search", response_model=list[LocationSummary])
def search_locations(q: str = "") -> list[LocationSummary]:
    query = q.strip().lower()
    if not query:
        return []
    return [
        LocationSummary(**location.model_dump())
        for location in DEMO_LOCATIONS
        if query in location.name.lower()
    ]


@router.get("/{location_id}", response_model=LocationDetail)
def location_detail(location_id: str) -> LocationDetail:
    for location in DEMO_LOCATIONS:
        if location.id == location_id:
            return location
    return LocationDetail(
        id=location_id,
        name=location_id.replace("-", " ").title(),
        accessibility_status="unknown",
        confidence="unknown",
        note="No verified local station or accessibility data is available yet.",
    )
