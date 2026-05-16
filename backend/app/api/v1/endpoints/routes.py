import json
import time
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.exceptions.route_errors import RouteUnavailableError
from app.schemas.routes import RecommendedRoute, RouteRecommendationRequest
from app.services.route_service import recommend_route as recommend_route_service

router = APIRouter()
_DEBUG_LOG = Path(__file__).resolve().parents[5] / ".cursor" / "debug-ce83c2.log"


def _agent_log(hypothesis_id: str, message: str, data: dict) -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": "ce83c2",
            "hypothesisId": hypothesis_id,
            "location": "routes.py",
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _DEBUG_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion


@router.post("/recommend", response_model=RecommendedRoute)
async def recommend_route(
    payload: RouteRecommendationRequest,
    background_tasks: BackgroundTasks,
) -> RecommendedRoute:
    # Endpoint stays thin so scoring/persistence behavior is centralized in
    # service layer and reused by tests.
    started = time.perf_counter()
    try:
        result = await recommend_route_service(payload, background_tasks=background_tasks)
        _agent_log(
            "H6",
            "recommend_ok",
            {"ms": round((time.perf_counter() - started) * 1000, 1)},
        )
        return result
    except RouteUnavailableError as exc:
        _agent_log(
            "H6",
            "recommend_unavailable",
            {"ms": round((time.perf_counter() - started) * 1000, 1), "code": exc.code},
        )
        raise HTTPException(status_code=404, detail=exc.to_detail()) from exc
    except Exception as exc:
        _agent_log(
            "H5",
            "recommend_error",
            {
                "ms": round((time.perf_counter() - started) * 1000, 1),
                "error_type": type(exc).__name__,
                "error": str(exc)[:240],
            },
        )
        raise
