from fastapi import APIRouter

from app.api.v1.endpoints import ai, health, locations, places, routes, users, weather


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(places.router, prefix="/places", tags=["places"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
