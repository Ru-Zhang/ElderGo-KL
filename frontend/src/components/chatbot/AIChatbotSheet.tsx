import { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronRight, Loader2, Send } from 'lucide-react';
import { useAppContext } from '../../app/AppProvider';
import { getTranslation, TranslationKey } from '../../i18n/translations';
import { createAIConversation, sendAIMessage } from '../../services/aiApi';
import { ApiError } from '../../services/api';
import { ChatAction, ChatBlock, ChatFlowType, ResponseSourceType } from '../../types/ai';
import { FontSizeMode } from '../../types/settings';
import ChatMessageBlocks from './ChatMessageBlocks';
import ChatQuickQuestions from './ChatQuickQuestions';
import { formatChatActionLabel } from './suggestedQuestions';
interface AIChatbotSheetProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (action: ChatAction) => void | Promise<void>;
}

function navigatingLabelForAction(
  action: ChatAction,
  t: (key: string) => string
): string {
  if (action.type === 'compute_route') {
    return t('chatNavigatingRoute');
  }
  if (action.type === 'open_station_detail') {
    return action.station_name
      ? `${t('chatNavigatingStation')}: ${action.station_name}`
      : t('chatNavigatingStation');
  }
  return t('chatNavigatingPage');
}

interface ChatMessage {
  text: string;
  isUser: boolean;
  blocks?: ChatBlock[];
  actions?: ChatAction[];
  responseSource?: ResponseSourceType | null;
  inScope?: boolean;
}

function filterAssistantActions(
  actions: ChatAction[] | undefined,
  answerText: string,
  inScope: boolean
): ChatAction[] | undefined {
  if (!actions?.length) return actions;
  const hasComputeRoute = actions.some((a) => a.type === 'compute_route');
  const looksOutOfScope =
    !inScope ||
    /\[OUT_OF_SCOPE\]/i.test(answerText) ||
    /Klang Valley travel help only|仅限巴生谷出行|Lembah Klang sahaja/i.test(answerText);
  if (looksOutOfScope || !hasComputeRoute) {
    const filtered = actions.filter(
      (a) => a.type !== 'open_route_text' && a.type !== 'open_route_map'
    );
    return filtered.length > 0 ? filtered : undefined;
  }
  return actions;
}

type MessageBlock =
  | { type: 'paragraph'; text: string }
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: string[] };

const CHATBOT_STORAGE_KEY = 'eldergo_ai_chat_session_v2';
const CHATBOT_TOP_OFFSET_PX = 110;
const MAX_STORED_MESSAGES = 40;
/** response_source stays in API/state for routing; never shown in the chat UI */
const SHOW_RESPONSE_SOURCE = false;
function chatErrorMessage(
  error: unknown,
  language: string,
  t: (key: string) => string
): string {
  if (error instanceof ApiError) {
    if (error.status === 429) {
      return t('chatErrorQuota');
    }
    if (error.status && error.status >= 500) {
      return t('chatErrorServer');
    }
    if (error.status && error.status >= 400) {
      return t('chatErrorValidation');
    }
  }
  return t('chatErrorUnavailable');
}

function chatFontScale(fontSize: FontSizeMode): number {
  if (fontSize === 'extra_large') return 1.5;
  if (fontSize === 'large') return 1.25;
  return 1;
}

function toSafeChatText(raw: string): string {
  return raw
    .replace(/```[\s\S]*?```/g, '')
    .replace(/<\/?[^>]+(>|$)/g, '')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^\s*[-*+]\s+/gm, '- ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function parseMessageBlocks(raw: string): MessageBlock[] {
  const text = toSafeChatText(raw);
  if (!text) return [];

  const lines = text.split('\n').map((line) => line.trim());
  const blocks: MessageBlock[] = [];
  let paragraphBuffer: string[] = [];
  let listType: 'ul' | 'ol' | null = null;
  let listItems: string[] = [];

  const flushParagraph = () => {
    if (paragraphBuffer.length === 0) return;
    blocks.push({ type: 'paragraph', text: paragraphBuffer.join(' ') });
    paragraphBuffer = [];
  };

  const flushList = () => {
    if (!listType || listItems.length === 0) return;
    blocks.push({ type: listType, items: listItems });
    listType = null;
    listItems = [];
  };

  for (const line of lines) {
    if (!line) {
      flushParagraph();
      flushList();
      continue;
    }

    const orderedMatch = line.match(/^\d+\.\s+(.*)$/);
    const bulletMatch = line.match(/^[-*+]\s+(.*)$/);

    if (orderedMatch) {
      flushParagraph();
      if (listType !== 'ol') {
        flushList();
        listType = 'ol';
      }
      listItems.push(orderedMatch[1].trim());
      continue;
    }

    if (bulletMatch) {
      flushParagraph();
      if (listType !== 'ul') {
        flushList();
        listType = 'ul';
      }
      listItems.push(bulletMatch[1].trim());
      continue;
    }

    flushList();
    paragraphBuffer.push(line);
  }

  flushParagraph();
  flushList();
  return blocks;
}

export default function AIChatbotSheet({ isOpen, onClose, onNavigate }: AIChatbotSheetProps) {
  const { language, fontSize, currentRoute, origin, destination, selectedStation } = useAppContext();
  const t = (key: string) => getTranslation(language, key as any);
  const fontScale = chatFontScale(fontSize);
  const bodyFontPx = Math.round(16 * fontScale);
  const chipFontPx = Math.round(15 * fontScale);
  const inputFontPx = Math.round(18 * fontScale);
  const disclaimerFontPx = Math.round(13 * fontScale);
  const quickQuestionsFontPx = Math.round(18 * fontScale);
  const welcomeFontPx = Math.round(20 * fontScale);
  const actionFontPx = Math.round(15 * fontScale);
  const blockHeadingFontPx = Math.round(20 * fontScale);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [chatFlow, setChatFlow] = useState<ChatFlowType>(null);
  const [flowSlots, setFlowSlots] = useState<Record<string, string>>({});
  const [isSending, setIsSending] = useState(false);
  const [isNavigating, setIsNavigating] = useState(false);
  const [navigatingLabel, setNavigatingLabel] = useState('');
  const [hasHydrated, setHasHydrated] = useState(false);
  const [quickQuestionsExpanded, setQuickQuestionsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const runNavigation = async (action: ChatAction) => {
    if (isNavigating) return;
    setIsNavigating(true);
    setNavigatingLabel(navigatingLabelForAction(action, t));
    try {
      await onNavigate(action);
      onClose();
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          text:
            action.type === 'open_station_detail'
              ? t('chatNavigationStationFailed')
              : t('chatNavigationFailed'),
          isUser: false
        }
      ]);
    } finally {
      setIsNavigating(false);
      setNavigatingLabel('');
    }
  };

  useEffect(() => {
    if (!isOpen) return;
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isSending, isOpen]);

  useEffect(() => {
    if (!isOpen || hasHydrated) return;

    let cancelled = false;
    const restore = () => {
      if (cancelled) return;
      try {
        const raw = localStorage.getItem(CHATBOT_STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw) as {
            messages?: ChatMessage[];
            conversationId?: string | null;
            chatFlow?: ChatFlowType;
            flowSlots?: Record<string, string>;
          };
          if (Array.isArray(parsed.messages)) {
            setMessages(parsed.messages.slice(-MAX_STORED_MESSAGES));
          }
          if (typeof parsed.conversationId === 'string' || parsed.conversationId === null) {
            setConversationId(parsed.conversationId ?? null);
          }
          if (parsed.chatFlow !== undefined) {
            setChatFlow(parsed.chatFlow ?? null);
          }
          if (parsed.flowSlots && typeof parsed.flowSlots === 'object') {
            setFlowSlots(parsed.flowSlots);
          }
        }
      } catch {
      } finally {
        if (!cancelled) setHasHydrated(true);
      }
    };

    if (typeof window.requestIdleCallback === 'function') {
      const id = window.requestIdleCallback(restore, { timeout: 120 });
      return () => {
        cancelled = true;
        window.cancelIdleCallback(id);
      };
    }

    const timer = window.setTimeout(restore, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [isOpen, hasHydrated]);

  useEffect(() => {
    if (!hasHydrated || !isOpen) return;
    const timer = window.setTimeout(() => {
      localStorage.setItem(
        CHATBOT_STORAGE_KEY,
        JSON.stringify({
          messages: messages.slice(-MAX_STORED_MESSAGES),
          conversationId,
          chatFlow,
          flowSlots
        })
      );
    }, 250);
    return () => window.clearTimeout(timer);
  }, [hasHydrated, isOpen, messages, conversationId, chatFlow, flowSlots]);

  const buildMessageContext = () => ({
    has_current_route: Boolean(currentRoute),
    // Do not send Planning-page origin/destination — avoids weather/planning pollution in chat flows.
    origin_name: null,
    destination_name: null,
    selected_station_id: selectedStation?.id ?? null,
    selected_station_name: selectedStation?.name ?? null,
    chat_flow: chatFlow,
    flow_slots: flowSlots
  });

  const clearConversation = () => {
    const confirmed = window.confirm(t('chatClearConfirm'));
    if (!confirmed) return;
    setMessages([]);
    setConversationId(null);
    setChatFlow(null);
    setFlowSlots({});
    setInputText('');
    localStorage.removeItem(CHATBOT_STORAGE_KEY);
  };

  const sendToAI = useCallback(async (messageText: string, options?: { resetFlow?: boolean }) => {
    const trimmed = messageText.trim();
    if (!trimmed || isSending) return;

    const outgoingFlow = options?.resetFlow ? null : chatFlow;
    const outgoingSlots = options?.resetFlow ? {} : flowSlots;

    setIsSending(true);
    setQuickQuestionsExpanded(false);
    setMessages((prev) => [...prev, { text: trimmed, isUser: true }]);

    try {
      let activeConversationId = conversationId;
      if (!activeConversationId) {
        const conversation = await createAIConversation();
        activeConversationId = conversation.conversation_id;
        setConversationId(activeConversationId);
      }

      const ctx = {
        has_current_route: Boolean(currentRoute),
        origin_name: null,
        destination_name: null,
        selected_station_id: selectedStation?.id ?? null,
        selected_station_name: selectedStation?.name ?? null,
        chat_flow: outgoingFlow,
        flow_slots: outgoingSlots
      };
      const response = await sendAIMessage(activeConversationId, {
        message: trimmed,
        uiLanguage: language,
        context: ctx
      });
      setChatFlow(response.chat_flow ?? null);
      setFlowSlots(response.flow_slots ?? {});
      const assistantActions = filterAssistantActions(
        response.actions,
        response.answer,
        response.in_scope
      );
      const computeRouteAction = assistantActions?.find((a) => a.type === 'compute_route');
      setMessages((prev) => [
        ...prev,
        {
          text: response.answer,
          isUser: false,
          blocks: response.answer_blocks?.length ? response.answer_blocks : undefined,
          actions: assistantActions,
          responseSource: response.response_source ?? null,
          inScope: response.in_scope
        }
      ]);
      if (computeRouteAction) {
        await runNavigation(computeRouteAction);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          text: chatErrorMessage(error, language, t),
          isUser: false
        }
      ]);
    } finally {
      setIsSending(false);
    }
  }, [
    chatFlow,
    conversationId,
    currentRoute,
    flowSlots,
    isSending,
    language,
    selectedStation?.id,
    selectedStation?.name,
    t
  ]);

  const handleSend = async () => {
    const text = inputText;
    setInputText('');
    await sendToAI(text);
  };

  const handleSuggestedQuestion = (messageKey: TranslationKey) => {
    const keepPlanFlow =
      chatFlow === 'plan_route' && messageKey === 'chatSuggest_planRouteMsg';
    if (!keepPlanFlow) {
      setChatFlow(null);
      setFlowSlots({});
    }
    void sendToAI(t(messageKey), { resetFlow: !keepPlanFlow });
  };

  const handleActionClick = (action: ChatAction) => {
    void runNavigation(action);
  };

  if (!isOpen) return null;

  const isEmptyChat = hasHydrated && messages.length === 0;

  return (
    <>
      <div className="fixed inset-0 z-[100] overflow-hidden">
        <div
          className="absolute inset-0 bg-black/40"
          onClick={() => {
            if (!isNavigating) onClose();
          }}
        />
        <div
          className="absolute left-0 right-0 bottom-0 bg-white rounded-t-3xl shadow-2xl flex flex-col min-w-0 overflow-hidden relative"
          style={{
            top: `${CHATBOT_TOP_OFFSET_PX}px`,
            height: `calc(100vh - ${CHATBOT_TOP_OFFSET_PX}px)`,
            maxHeight: `calc(100dvh - ${CHATBOT_TOP_OFFSET_PX}px)`,
            fontFamily: 'Poppins'
          }}
        >
          {isNavigating && (
            <div
              className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-4 bg-white/90 px-6 text-center"
              role="status"
              aria-live="polite"
            >
              <Loader2 className="animate-spin text-eldergo-blue" size={44} aria-hidden />
              <p
                className="font-semibold text-eldergo-navy leading-relaxed"
                style={{ fontSize: `${bodyFontPx}px` }}
              >
                {navigatingLabel}
              </p>
            </div>
          )}
          <div className="flex flex-col min-h-0 min-w-0 flex-1 px-4 pt-4 pb-3 sm:px-6 sm:pt-6">
            <div className="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-4 shrink-0" />

            <div className="mb-3 flex items-center justify-between gap-2 shrink-0 min-w-0">
              <button
                type="button"
                onClick={clearConversation}
                disabled={isNavigating}
                className="min-h-11 px-3 sm:px-5 font-semibold text-eldergo-navy bg-eldergo-bg border-2 border-eldergo-border rounded-xl hover:bg-eldergo-border transition-colors shrink-0 disabled:opacity-50"
                style={{ fontSize: `${bodyFontPx}px` }}
              >
                {t('chatClearLabel')}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={isNavigating}
                className="min-h-11 px-3 sm:px-5 font-semibold text-eldergo-navy bg-eldergo-bg border-2 border-eldergo-border rounded-xl hover:bg-eldergo-border transition-colors shrink-0 disabled:opacity-50"
                style={{ fontSize: `${bodyFontPx}px` }}
                aria-label="Close chatbot"
              >
                {t('chatCloseLabel')}
              </button>
            </div>

            {!hasHydrated && (
              <div
                className="mb-3 flex items-center gap-2 text-eldergo-muted shrink-0"
                style={{ fontSize: `${bodyFontPx}px` }}
                role="status"
              >
                <Loader2 className="animate-spin text-eldergo-blue shrink-0" size={20} aria-hidden />
                <span>{t('chatRestoringSession')}</span>
              </div>
            )}

            <div className="flex-1 min-h-0 min-w-0 overflow-y-auto overflow-x-hidden mb-3">
              <div className="space-y-4 min-w-0">
                {isEmptyChat && (
                  <div className="space-y-4 min-w-0 pb-2">
                    <h2
                      className="font-bold text-eldergo-navy leading-snug break-words"
                      style={{ fontSize: `${welcomeFontPx}px` }}
                    >
                      {t('chatbotGreeting')}
                    </h2>
                    <ChatQuickQuestions
                      variant="empty"
                      expanded
                      onToggleExpanded={() => {}}
                      onSelectQuestion={handleSuggestedQuestion}
                      disabled={isSending || isNavigating}
                      chipFontPx={chipFontPx}
                      bodyFontPx={bodyFontPx}
                      sectionFontPx={quickQuestionsFontPx}
                      t={t}
                    />
                  </div>
                )}
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex min-w-0 ${msg.isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[min(85%,100%)] min-w-0 px-4 py-3 rounded-2xl break-words [overflow-wrap:anywhere] ${
                        msg.isUser
                          ? 'bg-eldergo-blue text-white'
                          : 'bg-eldergo-bg text-eldergo-navy'
                      }`}
                    >
                      {msg.isUser ? (
                        <p
                          className="whitespace-pre-line leading-relaxed"
                          style={{ fontSize: `${bodyFontPx}px` }}
                        >
                          {msg.text}
                        </p>
                      ) : (
                        <div className="space-y-2 min-w-0" style={{ fontSize: `${bodyFontPx}px` }}>
                          {SHOW_RESPONSE_SOURCE && msg.responseSource && (
                            <p className="text-xs font-mono text-eldergo-muted/90">
                              source: {msg.responseSource}
                            </p>
                          )}
                          {msg.blocks && msg.blocks.length > 0 ? (
                            <ChatMessageBlocks
                              blocks={msg.blocks}
                              bodyFontPx={bodyFontPx}
                              headingFontPx={blockHeadingFontPx}
                              sourcesLabel={t('chatOfficialSources')}
                              language={language}
                              t={t}
                            />
                          ) : (
                          parseMessageBlocks(msg.text).map((block, blockIndex) => {
                            if (block.type === 'paragraph') {
                              return (
                                <p
                                  key={blockIndex}
                                  className="leading-relaxed break-words [overflow-wrap:anywhere]"
                                >
                                  {block.text}
                                </p>
                              );
                            }

                            if (block.type === 'ol') {
                              return (
                                <ol
                                  key={blockIndex}
                                  className="list-decimal pl-5 space-y-1 leading-relaxed break-words [overflow-wrap:anywhere]"
                                >
                                  {block.items.map((item, itemIndex) => (
                                    <li key={`${blockIndex}-${itemIndex}`}>{item}</li>
                                  ))}
                                </ol>
                              );
                            }

                            return (
                              <ul
                                key={blockIndex}
                                className="list-disc pl-5 space-y-1 leading-relaxed break-words [overflow-wrap:anywhere]"
                              >
                                {block.items.map((item, itemIndex) => (
                                  <li key={`${blockIndex}-${itemIndex}`}>{item}</li>
                                ))}
                              </ul>
                            );
                          }))}
                          {msg.actions && msg.actions.length > 0 && (
                            <div className="pt-2 flex flex-col gap-2 min-w-0">
                              {msg.actions.map((action, actionIndex) => (
                                <button
                                  key={`${index}-${actionIndex}-${action.type}`}
                                  type="button"
                                  onClick={() => handleActionClick(action)}
                                  disabled={isNavigating}
                                  aria-label={`${formatChatActionLabel(action, t)} — ${t('chatTapToOpen')}`}
                                  className="min-h-12 w-full max-w-full px-4 py-3 text-left font-semibold text-white bg-eldergo-blue border-2 border-eldergo-blue-dark rounded-xl shadow-md hover:bg-eldergo-blue-dark hover:shadow-lg active:scale-[0.99] transition-all break-words [overflow-wrap:anywhere] disabled:opacity-50 flex items-center justify-between gap-2"
                                  style={{ fontSize: `${actionFontPx}px` }}
                                >
                                  <span>{formatChatActionLabel(action, t)}</span>
                                  <ChevronRight size={22} className="shrink-0 opacity-90" aria-hidden />
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} className="h-1 shrink-0" aria-hidden />
              </div>
            </div>

            <div className="shrink-0 min-w-0 border-t border-eldergo-border/70 bg-white pt-3">
              {!isEmptyChat && (
                <ChatQuickQuestions
                  variant="compact"
                  expanded={quickQuestionsExpanded}
                  onToggleExpanded={() => setQuickQuestionsExpanded((prev) => !prev)}
                  onSelectQuestion={handleSuggestedQuestion}
                  disabled={isSending || isNavigating}
                  chipFontPx={chipFontPx}
                  bodyFontPx={bodyFontPx}
                  sectionFontPx={quickQuestionsFontPx}
                  t={t}
                />
              )}
              <div className="flex gap-2 items-stretch min-w-0">
                <input
                  type="text"
                  placeholder={t('chatInputPlaceholder')}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      void handleSend();
                    }
                  }}
                  disabled={isSending || isNavigating}
                  className="flex-1 min-w-0 px-4 py-3 border-2 border-eldergo-border rounded-xl text-eldergo-navy placeholder:text-slate-500 focus:outline-none focus:border-eldergo-blue bg-white"
                  style={{ fontFamily: 'Poppins', fontSize: `${inputFontPx}px` }}
                />
                <button
                  type="button"
                  onClick={() => void handleSend()}
                  disabled={isSending || isNavigating || !inputText.trim()}
                  className="min-w-[52px] shrink-0 px-3 flex items-center justify-center bg-eldergo-blue text-white rounded-xl hover:bg-eldergo-blue-dark transition-colors disabled:opacity-50"
                  aria-label={t('chatSendLabel')}
                >
                  <Send size={22} strokeWidth={2.5} />
                </button>
              </div>
              <p
                className="mt-2 text-slate-500 leading-snug break-words [overflow-wrap:anywhere]"
                style={{ fontSize: `${disclaimerFontPx}px` }}
              >
                {t('chatInputDisclaimer')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
