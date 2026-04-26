export interface AIConversationResponse {
  conversation_id: string;
}

export interface AIMessageResponse {
  conversation_id: string;
  answer: string;
  in_scope: boolean;
}
