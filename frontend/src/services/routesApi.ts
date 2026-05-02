import { RecommendedRoute, RouteRecommendationRequest, toApiRouteRequest } from '../types/routes';
import { apiRequest } from './api';

export async function recommendRoute(request: RouteRecommendationRequest): Promise<RecommendedRoute> {
  // Keep payload conversion centralized so UI types can stay camelCase while
  // backend contract remains snake_case.
  return apiRequest<RecommendedRoute>('/routes/recommend', {
    method: 'POST',
    body: JSON.stringify(toApiRouteRequest(request))
  });
}
