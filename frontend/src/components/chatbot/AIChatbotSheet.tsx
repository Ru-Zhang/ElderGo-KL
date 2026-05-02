import { Mic, X, Plus, CloudRain, Headphones, ArrowRight } from 'lucide-react';
import { useState } from 'react';
import { useAppContext } from '../../app/AppProvider';
import { getTranslation } from '../../i18n/translations';

interface AIChatbotSheetProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AIChatbotSheet({ isOpen, onClose }: AIChatbotSheetProps) {
  const { language } = useAppContext();
  const t = (key: string) => getTranslation(language, key as any);
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean }>>([]);
  const [inputText, setInputText] = useState('');

  if (!isOpen) return null;

  const quickQuestions = [
    { text: t('quickHospital'), icon: Plus },
    { text: t('quickRain'), icon: CloudRain },
    { text: t('quickStationStaff'), icon: Headphones }
  ];

  const handleQuickQuestion = (question: string) => {
    // Prototype behavior: replace thread with one quick Q&A pair.
    setMessages([
      { text: question, isUser: true },
      { text: `${t('chatbotReplyPrefix')} "${question}".`, isUser: false }
    ]);
  };

  const handleSend = () => {
    if (inputText.trim()) {
      // Append local echo response until live AI endpoint is fully wired.
      setMessages([
        ...messages,
        { text: inputText, isUser: true },
        { text: `${t('chatbotReplyPrefix')}: ${inputText}`, isUser: false }
      ]);
      setInputText('');
    }
  };

  return (
    <div className="fixed inset-0 z-[100]">
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
      />
      <div
        className="absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl shadow-2xl"
        style={{ height: '75vh', fontFamily: 'Poppins' }}
      >
        <div className="relative h-full flex flex-col p-6">
          <div className="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-6" />

          <h2 className="text-3xl font-bold text-eldergo-navy mb-8">
            {t('chatbotGreeting')}
          </h2>

          <div className="flex-1 overflow-y-auto mb-6">
            {messages.length === 0 ? (
              <div className="space-y-4">
                {quickQuestions.map((question, index) => {
                  const IconComponent = question.icon;
                  return (
                    <button
                      key={index}
                      onClick={() => handleQuickQuestion(question.text)}
                      className="w-full px-6 py-5 bg-white border-3 border-eldergo-blue rounded-2xl text-[18px] font-semibold text-eldergo-navy hover:bg-eldergo-bg transition-colors flex items-center justify-between group"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-eldergo-blue rounded-lg flex items-center justify-center">
                          <IconComponent size={22} strokeWidth={2.5} className="text-white" />
                        </div>
                        <span>{question.text}</span>
                      </div>
                      <ArrowRight size={24} strokeWidth={2.5} className="text-eldergo-muted group-hover:text-eldergo-blue transition-colors" />
                    </button>
                  );
                })}
              </div>
            ) : (
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
                      <p className="text-[16px]">{msg.text}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-3 items-center">
            <input
              type="text"
              placeholder={t('askMeAnything')}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              className="flex-1 px-5 py-4 border-2 border-eldergo-border rounded-xl text-[18px] text-eldergo-navy placeholder:text-eldergo-muted focus:outline-none focus:border-eldergo-blue"
              style={{ fontFamily: 'Poppins' }}
            />
            <button
              onClick={handleSend}
              className="w-16 h-16 bg-eldergo-blue hover:bg-eldergo-blue-dark rounded-2xl flex items-center justify-center transition-colors shadow-lg"
            >
              <Mic size={28} strokeWidth={2.5} className="text-white" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
