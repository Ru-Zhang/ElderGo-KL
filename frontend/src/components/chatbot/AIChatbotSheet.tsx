import { useEffect, useState } from 'react';
import { useAppContext } from '../../app/AppProvider';
import { getTranslation } from '../../i18n/translations';
import { createAIConversation, sendAIMessage } from '../../services/aiApi';

interface AIChatbotSheetProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ChatMessage {
  text: string;
  isUser: boolean;
}

type MessageBlock =
  | { type: 'paragraph'; text: string }
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: string[] };

const CHATBOT_STORAGE_KEY = 'eldergo_ai_chat_session_v1';
const CHATBOT_TOP_OFFSET_PX = 110;
const CHAT_UNAVAILABLE_MESSAGE_BY_LANGUAGE: Record<string, string> = {
  EN: 'Sorry, the AI assistant is temporarily unavailable.\nNext step: try again in 1 minute, or ask a shorter question.',
  BM: 'Maaf, pembantu AI tidak tersedia buat sementara waktu.\nLangkah seterusnya: cuba semula dalam 1 minit, atau gunakan soalan yang lebih ringkas.'
};

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

export default function AIChatbotSheet({ isOpen, onClose }: AIChatbotSheetProps) {
  const { language } = useAppContext();
  const t = (key: string) => getTranslation(language, key as any);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [hasHydrated, setHasHydrated] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(CHATBOT_STORAGE_KEY);
      if (!raw) {
        setHasHydrated(true);
        return;
      }
      const parsed = JSON.parse(raw) as { messages?: ChatMessage[]; conversationId?: string | null };
      if (Array.isArray(parsed.messages)) {
        setMessages(parsed.messages);
      }
      if (typeof parsed.conversationId === 'string' || parsed.conversationId === null) {
        setConversationId(parsed.conversationId ?? null);
      }
    } catch (_err) {
      // Ignore malformed localStorage payload and continue with empty session.
    } finally {
      setHasHydrated(true);
    }
  }, []);

  useEffect(() => {
    if (!hasHydrated) return;
    localStorage.setItem(
      CHATBOT_STORAGE_KEY,
      JSON.stringify({
        messages,
        conversationId
      })
    );
  }, [hasHydrated, messages, conversationId]);

  const clearConversation = () => {
    const confirmed = window.confirm(t('chatClearConfirm'));
    if (!confirmed) return;
    setMessages([]);
    setConversationId(null);
    setInputText('');
    localStorage.removeItem(CHATBOT_STORAGE_KEY);
  };

  if (!isOpen) return null;

  const sendToAI = async (messageText: string) => {
    const trimmed = messageText.trim();
    if (!trimmed || isSending) return;

    setIsSending(true);
    setMessages((prev) => [...prev, { text: trimmed, isUser: true }]);

    try {
      let activeConversationId = conversationId;
      if (!activeConversationId) {
        const conversation = await createAIConversation();
        activeConversationId = conversation.conversation_id;
        setConversationId(activeConversationId);
      }

      const response = await sendAIMessage(activeConversationId, {
        message: trimmed
      });
      setMessages((prev) => [...prev, { text: response.answer, isUser: false }]);
    } catch (_error) {
      setMessages((prev) => [
        ...prev,
        {
          text: CHAT_UNAVAILABLE_MESSAGE_BY_LANGUAGE[language] ?? CHAT_UNAVAILABLE_MESSAGE_BY_LANGUAGE.EN,
          isUser: false
        }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleSend = async () => {
    const text = inputText;
    setInputText('');
    await sendToAI(text);
  };

  return (
    <div className="fixed inset-0 z-[100]">
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
      />
      <div
        className="absolute left-0 right-0 bottom-0 bg-white rounded-t-3xl shadow-2xl"
        style={{
          top: `${CHATBOT_TOP_OFFSET_PX}px`,
          height: `calc(100vh - ${CHATBOT_TOP_OFFSET_PX}px)`,
          fontFamily: 'Poppins'
        }}
      >
        <div className="h-full flex flex-col p-6">
          <div className="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-5" />

          <div className="h-12 mb-3 flex items-center justify-between">
            <button
              type="button"
              onClick={clearConversation}
              className="min-h-11 px-5 text-base font-semibold text-eldergo-navy bg-eldergo-bg border-2 border-eldergo-border rounded-xl hover:bg-eldergo-border transition-colors"
            >
              {t('chatClearLabel')}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="min-h-11 px-5 text-base font-semibold text-eldergo-navy bg-eldergo-bg border-2 border-eldergo-border rounded-xl hover:bg-eldergo-border transition-colors"
              aria-label="Close chatbot"
            >
              {t('chatCloseLabel')}
            </button>
          </div>
          <h2 className="text-2xl font-bold text-eldergo-navy leading-tight mb-4">
            {t('chatbotGreeting')}
          </h2>

          <div className="flex-1 overflow-y-auto mb-4">
            <div className="space-y-4">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] px-5 py-3 rounded-2xl ${
                      msg.isUser
                        ? 'bg-eldergo-blue text-white'
                        : 'bg-eldergo-bg text-eldergo-navy'
                    }`}
                  >
                    {msg.isUser ? (
                      <p className="text-[16px] whitespace-pre-line">{msg.text}</p>
                    ) : (
                      <div className="text-[16px] space-y-2">
                        {parseMessageBlocks(msg.text).map((block, blockIndex) => {
                          if (block.type === 'paragraph') {
                            return (
                              <p
                                key={blockIndex}
                                className="leading-relaxed"
                              >
                                {block.text}
                              </p>
                            );
                          }

                          if (block.type === 'ol') {
                            return (
                              <ol
                                key={blockIndex}
                                className="list-decimal pl-5 space-y-1 leading-relaxed"
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
                              className="list-disc pl-5 space-y-1 leading-relaxed"
                            >
                              {block.items.map((item, itemIndex) => (
                                <li key={`${blockIndex}-${itemIndex}`}>{item}</li>
                              ))}
                            </ul>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-3 border-t border-eldergo-border/70 bg-eldergo-bg/40 rounded-t-2xl">
            <input
              type="text"
              placeholder={t('askMeAnything')}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && void handleSend()}
              disabled={isSending}
              className="w-full px-5 py-4 border-2 border-eldergo-border rounded-xl text-[18px] text-eldergo-navy placeholder:text-slate-500 focus:outline-none focus:border-eldergo-blue bg-white"
              style={{ fontFamily: 'Poppins' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
