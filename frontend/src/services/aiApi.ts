import { AIConversationResponse, AIMessageResponse } from '../types/ai';
import { apiRequest } from './api';

export async function createAIConversation(): Promise<AIConversationResponse> {
  // Conversation bootstrap keeps message calls grouped under one UI thread id.
  return apiRequest<AIConversationResponse>('/ai/conversations', { method: 'POST' });
}

interface SendAIMessagePayload {
  message: string;
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
