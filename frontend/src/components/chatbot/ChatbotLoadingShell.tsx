import { Loader2 } from 'lucide-react';

interface ChatbotLoadingShellProps {
  onClose: () => void;
  closeLabel: string;
  openingLabel: string;
}

const TOP_OFFSET_PX = 110;

/** Lightweight placeholder while the chatbot chunk loads (avoids a blank white screen). */
export default function ChatbotLoadingShell({
  onClose,
  closeLabel,
  openingLabel
}: ChatbotLoadingShellProps) {
  return (
    <div className="fixed inset-0 z-[100] overflow-hidden" role="status" aria-live="polite">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div
        className="absolute left-0 right-0 bottom-0 bg-white rounded-t-3xl shadow-2xl flex flex-col items-center justify-center gap-4"
        style={{
          top: `${TOP_OFFSET_PX}px`,
          height: `calc(100dvh - ${TOP_OFFSET_PX}px)`
        }}
      >
        <Loader2 className="animate-spin text-eldergo-blue" size={40} aria-hidden />
        <p className="text-eldergo-navy font-medium px-6 text-center">{openingLabel}</p>
        <button
          type="button"
          onClick={onClose}
          className="min-h-11 px-4 font-semibold text-eldergo-navy border-2 border-eldergo-border rounded-xl"
        >
          {closeLabel}
        </button>
      </div>
    </div>
  );
}
