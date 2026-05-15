import { MapPin, X } from 'lucide-react';

interface GoogleMapsInstallModalProps {
  isOpen: boolean;
  title: string;
  body: string;
  installLabel: string;
  cancelLabel: string;
  browserLabel: string;
  baseFontSize: number;
  onInstall: () => void;
  onOpenInBrowser: () => void;
  onClose: () => void;
}

export default function GoogleMapsInstallModal({
  isOpen,
  title,
  body,
  installLabel,
  cancelLabel,
  browserLabel,
  baseFontSize,
  onInstall,
  onOpenInBrowser,
  onClose,
}: GoogleMapsInstallModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[110] flex items-end sm:items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="google-maps-install-title"
        className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 sm:p-8"
        style={{ fontFamily: 'Poppins' }}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 text-eldergo-navy hover:bg-eldergo-bg rounded-full p-2"
          aria-label={cancelLabel}
        >
          <X size={24 * baseFontSize} strokeWidth={2.5} />
        </button>

        <div className="flex items-center gap-3 mb-4 pr-10">
          <div className="w-12 h-12 rounded-full bg-eldergo-blue/15 flex items-center justify-center flex-shrink-0">
            <MapPin size={26 * baseFontSize} className="text-eldergo-blue" strokeWidth={2.5} />
          </div>
          <h2
            id="google-maps-install-title"
            className="text-eldergo-navy font-semibold leading-tight"
            style={{ fontSize: `${22 * baseFontSize}px` }}
          >
            {title}
          </h2>
        </div>

        <p className="text-eldergo-navy mb-6" style={{ fontSize: `${18 * baseFontSize}px` }}>
          {body}
        </p>

        <div className="space-y-3">
          <button
            type="button"
            onClick={onInstall}
            className="w-full bg-eldergo-blue hover:bg-eldergo-blue-dark text-white font-semibold py-4 rounded-xl transition-colors shadow-md"
            style={{ fontSize: `${18 * baseFontSize}px` }}
          >
            {installLabel}
          </button>
          <button
            type="button"
            onClick={onOpenInBrowser}
            className="w-full bg-white border-2 border-eldergo-border text-eldergo-navy font-semibold py-4 rounded-xl hover:bg-eldergo-bg transition-colors"
            style={{ fontSize: `${18 * baseFontSize}px` }}
          >
            {browserLabel}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="w-full text-eldergo-muted font-medium py-2"
            style={{ fontSize: `${16 * baseFontSize}px` }}
          >
            {cancelLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
