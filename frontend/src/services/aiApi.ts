import { AIConversationResponse, AIMessageResponse } from '../types/ai';
import { apiRequest } from './api';

export async function createAIConversation(): Promise<AIConversationResponse> {
  // Conversation bootstrap keeps message calls grouped under one UI thread id.
  return apiRequest<AIConversationResponse>('/ai/conversations', { method: 'POST' });
}

interface SendAIMessagePayload {
  message: string;
  current_route_id?: string | null;
  selected_location_id?: string | null;
  anonymous_user_id?: string | null;
}

export async function sendAIMessage(
  conversationId: string,
  payload: SendAIMessagePayload
): Promise<AIMessageResponse> {
  return apiRequest<AIMessageResponse>(`/ai/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}
