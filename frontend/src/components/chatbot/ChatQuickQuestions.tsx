import { useState } from 'react';
import { ChevronDown, ChevronRight, ChevronUp } from 'lucide-react';
import { TranslationKey } from '../../i18n/translations';
import {
  MORE_SUGGESTED_QUESTIONS,
  PRIMARY_SUGGESTED_QUESTIONS,
  SuggestedQuestion,
} from './suggestedQuestions';

interface ChatQuickQuestionsProps {
  variant: 'empty' | 'compact';
  expanded: boolean;
  onToggleExpanded: () => void;
  onSelectQuestion: (messageKey: TranslationKey) => void;
  disabled: boolean;
  chipFontPx: number;
  bodyFontPx: number;
  sectionFontPx: number;
  t: (key: TranslationKey) => string;
}

export default function ChatQuickQuestions({
  variant,
  expanded,
  onToggleExpanded,
  onSelectQuestion,
  disabled,
  chipFontPx,
  bodyFontPx,
  sectionFontPx,
  t,
}: ChatQuickQuestionsProps) {
  const [moreTopicsExpanded, setMoreTopicsExpanded] = useState(false);
  const compactChipFontPx = Math.max(13, chipFontPx - 1);

  const handleSelectQuestion = (messageKey: TranslationKey, fromMoreGroup = false) => {
    onSelectQuestion(messageKey);
    if (fromMoreGroup) {
      setMoreTopicsExpanded(false);
    }
  };

  const renderEmptyPrimaryButton = (question: SuggestedQuestion) => (
    <button
      key={question.id}
      type="button"
      disabled={disabled}
      onClick={() => handleSelectQuestion(question.messageKey)}
      aria-label={`${t(question.labelKey)} — ${t('chatTapToAsk')}`}
      className="min-h-12 w-full max-w-full min-w-0 px-4 py-3 font-semibold text-eldergo-navy bg-white border-2 border-eldergo-blue rounded-xl shadow-sm hover:bg-eldergo-blue/10 hover:border-eldergo-blue-dark active:scale-[0.99] transition-all disabled:opacity-50 text-left flex items-center justify-between gap-2 box-border"
      style={{ fontSize: `${chipFontPx}px` }}
    >
      <span className="min-w-0 flex-1 break-words [overflow-wrap:anywhere]">{t(question.labelKey)}</span>
      <ChevronRight size={20} className="shrink-0 text-eldergo-blue" aria-hidden />
    </button>
  );

  const renderEmptyMoreSubButton = (question: SuggestedQuestion) => (
    <button
      key={question.id}
      type="button"
      disabled={disabled}
      onClick={() => handleSelectQuestion(question.messageKey, true)}
      aria-label={`${t(question.labelKey)} — ${t('chatTapToAsk')}`}
      className="min-h-12 w-full max-w-full min-w-0 px-4 py-3 font-semibold text-eldergo-navy bg-white border-2 border-eldergo-blue/80 rounded-xl shadow-sm hover:bg-eldergo-blue/10 hover:border-eldergo-blue-dark active:scale-[0.99] transition-all disabled:opacity-50 text-left flex items-center justify-between gap-2 box-border"
      style={{ fontSize: `${chipFontPx}px` }}
    >
      <span className="min-w-0 flex-1 break-words [overflow-wrap:anywhere]">{t(question.labelKey)}</span>
      <ChevronRight size={20} className="shrink-0 text-eldergo-blue" aria-hidden />
    </button>
  );

  const renderCompactChip = (question: SuggestedQuestion, fromMoreGroup = false) => (
    <button
      key={question.id}
      type="button"
      disabled={disabled}
      onClick={() => handleSelectQuestion(question.messageKey, fromMoreGroup)}
      aria-label={`${t(question.labelKey)} — ${t('chatTapToAsk')}`}
      className={`min-h-11 min-w-0 px-2.5 py-2 font-semibold text-eldergo-navy bg-white border-2 border-eldergo-blue rounded-xl shadow-sm hover:bg-eldergo-blue/10 hover:border-eldergo-blue-dark active:scale-[0.99] transition-all disabled:opacity-50 text-left break-words [overflow-wrap:anywhere] leading-snug box-border${fromMoreGroup ? ' w-full max-w-full' : ''}`}
      style={{ fontSize: `${compactChipFontPx}px` }}
    >
      {t(question.labelKey)}
    </button>
  );

  if (variant === 'empty') {
    return (
      <div className="space-y-2 min-w-0 pb-2">
        <p
          className="font-semibold text-eldergo-muted px-1"
          style={{ fontSize: `${bodyFontPx}px` }}
        >
          {t('chatSuggestedQuestionsLabel')}
        </p>
        {PRIMARY_SUGGESTED_QUESTIONS.map(renderEmptyPrimaryButton)}
        <button
          type="button"
          disabled={disabled}
          onClick={() => setMoreTopicsExpanded((prev) => !prev)}
          aria-expanded={moreTopicsExpanded}
          aria-label={t('chatSuggest_moreTopicsGroup')}
          className="min-h-12 w-full max-w-full min-w-0 px-4 py-3 font-semibold text-eldergo-navy bg-white border-2 border-eldergo-blue rounded-xl shadow-sm hover:bg-eldergo-blue/10 hover:border-eldergo-blue-dark active:scale-[0.99] transition-all disabled:opacity-50 text-left flex items-center justify-between gap-2 box-border"
          style={{ fontSize: `${chipFontPx}px` }}
        >
          <span className="min-w-0 flex-1 break-words [overflow-wrap:anywhere]">{t('chatSuggest_moreTopicsGroup')}</span>
          {moreTopicsExpanded ? (
            <ChevronUp size={20} className="shrink-0 text-eldergo-blue" aria-hidden />
          ) : (
            <ChevronDown size={20} className="shrink-0 text-eldergo-blue" aria-hidden />
          )}
        </button>
        {moreTopicsExpanded && (
          <div className="space-y-2 min-w-0 w-full max-w-full pl-3 border-l-2 border-eldergo-blue/30 box-border">
            {MORE_SUGGESTED_QUESTIONS.map(renderEmptyMoreSubButton)}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="min-w-0 mb-2">
      <button
        type="button"
        onClick={onToggleExpanded}
        className="w-full flex items-center justify-between gap-2 min-h-11 px-1 text-left font-bold text-eldergo-navy hover:text-eldergo-blue transition-colors"
        style={{ fontSize: `${sectionFontPx}px` }}
        aria-expanded={expanded}
      >
        <span>{t('chatSuggestedQuestionsLabel')}</span>
        <span className="flex items-center gap-1 shrink-0 text-eldergo-blue font-bold">
          <span style={{ fontSize: `${bodyFontPx}px` }}>
            {expanded ? t('chatSuggestedQuestionsHide') : t('chatSuggestedQuestionsShow')}
          </span>
          {expanded ? <ChevronUp size={20} aria-hidden /> : <ChevronDown size={20} aria-hidden />}
        </span>
      </button>
      {expanded && (
        <div className="mt-2 max-h-[14vh] overflow-y-auto overflow-x-hidden -mx-1 px-1">
          <div className="grid grid-cols-2 gap-2 min-w-0">
            {PRIMARY_SUGGESTED_QUESTIONS.map((question) => renderCompactChip(question))}
            <button
              type="button"
              disabled={disabled}
              onClick={() => setMoreTopicsExpanded((prev) => !prev)}
              aria-expanded={moreTopicsExpanded}
              aria-label={t('chatSuggest_moreTopicsGroup')}
              className="min-h-11 px-2.5 py-2 font-semibold text-eldergo-navy bg-white border-2 border-eldergo-blue rounded-xl shadow-sm hover:bg-eldergo-blue/10 hover:border-eldergo-blue-dark active:scale-[0.99] transition-all disabled:opacity-50 text-left break-words [overflow-wrap:anywhere] leading-snug flex items-center justify-between gap-1"
              style={{ fontSize: `${compactChipFontPx}px` }}
            >
              <span>{t('chatSuggest_moreTopicsGroup')}</span>
              {moreTopicsExpanded ? (
                <ChevronUp size={16} className="shrink-0 text-eldergo-blue" aria-hidden />
              ) : (
                <ChevronDown size={16} className="shrink-0 text-eldergo-blue" aria-hidden />
              )}
            </button>
          </div>
          {moreTopicsExpanded && (
            <div className="mt-2 space-y-2 min-w-0 w-full max-w-full pl-3 border-l-2 border-eldergo-blue/30 box-border">
              {MORE_SUGGESTED_QUESTIONS.map((question) => renderCompactChip(question, true))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
