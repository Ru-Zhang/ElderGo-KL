export interface AIConversationResponse {
  conversation_id: string;
}

export interface AIMessageResponse {
  conversation_id: string;
  answer: string;
  // Guardrail result indicating whether prompt matched ElderGo support scope.
  in_scope: boolean;
  response_source: 'database' | 'static_help' | 'mixed' | 'fallback';
  grounded: boolean;
  used_data_keys: string[];
}
