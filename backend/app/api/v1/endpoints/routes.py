from fastapi import APIRouter

from app.schemas.routes import RecommendedRoute, RouteRecommendationRequest
from app.services.route_service import recommend_route as recommend_route_service

router = APIRouter()


@router.post("/recommend", response_model=RecommendedRoute)
async def recommend_route(payload: RouteRecommendationRequest) -> RecommendedRoute:
    # Endpoint stays thin so scoring/persistence behavior is centralized in
    # service layer and reused by tests.
    return await recommend_route_service(payload)
