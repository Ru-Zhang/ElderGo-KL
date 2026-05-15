import { AIConversationResponse, AIMessageContext, AIMessageResponse } from '../types/ai';
import { LanguageCode } from '../types/settings';
import { apiRequest } from './api';

export async function createAIConversation(): Promise<AIConversationResponse> {
  return apiRequest<AIConversationResponse>('/ai/conversations', { method: 'POST' });
}

interface SendAIMessagePayload {
  message: string;
  uiLanguage?: LanguageCode;
  context?: AIMessageContext;
}

export async function sendAIMessage(
  conversationId: string,
  payload: SendAIMessagePayload
): Promise<AIMessageResponse> {
  const { context, message, uiLanguage = 'EN' } = payload;
  return apiRequest<AIMessageResponse>(`/ai/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify({
      message,
      ui_language: uiLanguage,
      has_current_route: context?.has_current_route ?? false,
      origin_name: context?.origin_name ?? null,
      destination_name: context?.destination_name ?? null,
      selected_station_id: context?.selected_station_id ?? null,
      selected_station_name: context?.selected_station_name ?? null,
      chat_flow: context?.chat_flow ?? null,
      flow_slots: context?.flow_slots ?? {}
    })
  });
}
