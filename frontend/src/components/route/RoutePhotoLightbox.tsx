import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import type { TranslationKey } from '../../i18n/translations';
import PinchZoomImage from './PinchZoomImage';

interface RoutePhotoLightboxProps {
  open: boolean;
  onClose: () => void;
  imageSrc: string;
  imageAlt: string;
  caption: string;
  baseFontSize: number;
  t: (key: TranslationKey) => string;
}

export default function RoutePhotoLightbox({
  open,
  onClose,
  imageSrc,
  imageAlt,
  caption,
  baseFontSize,
  t,
}: RoutePhotoLightboxProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const lightboxCaptionSize = 18 * baseFontSize;
  const closeFontSize = 14 * baseFontSize;

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeButtonRef.current?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKey);
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-3"
      role="dialog"
      aria-modal="true"
      aria-label={t('routePhotoEnlarge')}
    >
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />

      <div
        className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[88dvh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="shrink-0 overflow-hidden flex items-center justify-center bg-white"
          style={{ height: 'min(52dvh, 380px)' }}
        >
          <PinchZoomImage
            key={imageSrc}
            src={imageSrc}
            alt={caption || imageAlt}
            active={open}
            className="px-2"
          />
        </div>

        {caption && (
          <p
            className="shrink-0 text-center text-eldergo-navy leading-snug max-w-lg mx-auto font-medium px-4 pt-3 line-clamp-4"
            style={{ fontSize: `${lightboxCaptionSize}px` }}
          >
            {caption}
          </p>
        )}

        <div className="shrink-0 flex justify-center px-4 pt-2 pb-4">
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="inline-flex items-center justify-center rounded-xl bg-eldergo-blue hover:bg-eldergo-blue-dark text-white font-semibold shadow-sm px-6"
            style={{
              fontSize: `${closeFontSize}px`,
              minHeight: 36 * baseFontSize,
            }}
            aria-label={t('routePhotoClose')}
          >
            {t('routePhotoClose')}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
