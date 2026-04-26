import { RecommendedRoute, RouteRecommendationRequest, toApiRouteRequest } from '../types/routes';
import { apiRequest } from './api';

export async function recommendRoute(request: RouteRecommendationRequest): Promise<RecommendedRoute> {
  return apiRequest<RecommendedRoute>('/routes/recommend', {
    method: 'POST',
    body: JSON.stringify(toApiRouteRequest(request))
  });
}
