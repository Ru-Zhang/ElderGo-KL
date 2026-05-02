import { AIConversationResponse, AIMessageResponse } from '../types/ai';
import { apiRequest } from './api';

export async function createAIConversation(): Promise<AIConversationResponse> {
  // Conversation bootstrap keeps message calls grouped under one UI thread id.
  return apiRequest<AIConversationResponse>('/ai/conversations', { method: 'POST' });
}

export async function sendAIMessage(conversationId: string, message: string): Promise<AIMessageResponse> {
  return apiRequest<AIMessageResponse>(`/ai/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ message })
  });
}
