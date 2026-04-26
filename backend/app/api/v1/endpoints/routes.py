from fastapi import APIRouter

from app.schemas.routes import RecommendedRoute, RouteRecommendationRequest
from app.services.route_service import build_demo_recommendation

router = APIRouter()


@router.post("/recommend", response_model=RecommendedRoute)
def recommend_route(payload: RouteRecommendationRequest) -> RecommendedRoute:
    return build_demo_recommendation(payload)
