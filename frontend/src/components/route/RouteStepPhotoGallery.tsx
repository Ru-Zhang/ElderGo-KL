import { useEffect, useState } from 'react';
import { ImageWithFallback } from '../common/ImageWithFallback';
import type { RouteStationImage } from '../../services/routeStationImages';
import type { TranslationKey } from '../../i18n/translations';
import { resolveRouteImageUrl } from '../../utils/routeStationImages';
import RoutePhotoLightbox from './RoutePhotoLightbox';

interface RouteStepPhotoGalleryProps {
  images: RouteStationImage[];
  imageIndex: number;
  onImageIndexChange: (index: number) => void;
  imageAlt: string;
  baseFontSize: number;
  t: (key: TranslationKey) => string;
  /** Only the visible step should report lightbox state to the parent. */
  isActiveStep?: boolean;
  onLightboxOpenChange?: (open: boolean) => void;
}

function PhotoNumberStrip({
  images,
  imageIndex,
  onSelect,
  baseFontSize,
  t,
}: {
  images: RouteStationImage[];
  imageIndex: number;
  onSelect: (index: number) => void;
  baseFontSize: number;
  t: (key: TranslationKey) => string;
}) {
  if (images.length <= 1) return null;

  const buttonSize = 44 * baseFontSize;
  const fontSize = 16 * baseFontSize;

  return (
    <div
      className="flex items-center justify-center gap-2 flex-wrap"
      role="tablist"
      aria-label={t('routePhotoCounter')
        .replace('{current}', String(imageIndex + 1))
        .replace('{total}', String(images.length))}
    >
      {images.map((_, index) => {
        const isActive = index === imageIndex;
        return (
          <button
            key={`photo-tab-${index}`}
            type="button"
            role="tab"
            aria-selected={isActive}
            aria-current={isActive ? 'true' : undefined}
            aria-label={t('routePhotoGoTo').replace('{n}', String(index + 1))}
            onClick={() => onSelect(index)}
            className={`rounded-xl font-bold transition-colors border-2 ${
              isActive
                ? 'bg-eldergo-blue text-white border-eldergo-blue'
                : 'bg-white text-eldergo-navy border-eldergo-border hover:border-eldergo-blue'
            }`}
            style={{
              minWidth: buttonSize,
              minHeight: buttonSize,
              fontSize: `${fontSize}px`,
              paddingLeft: `${12 * baseFontSize}px`,
              paddingRight: `${12 * baseFontSize}px`,
            }}
          >
            {index + 1}
          </button>
        );
      })}
    </div>
  );
}

export default function RouteStepPhotoGallery({
  images,
  imageIndex,
  onImageIndexChange,
  imageAlt,
  baseFontSize,
  t,
  isActiveStep = true,
  onLightboxOpenChange,
}: RouteStepPhotoGalleryProps) {
  const [lightboxOpen, setLightboxOpen] = useState(false);

  const safeIndex = images.length > 0 ? Math.min(imageIndex, images.length - 1) : 0;
  const activeImage = images[safeIndex] ?? null;
  const imageSrc = activeImage?.path ? resolveRouteImageUrl(activeImage.path) : null;
  const imageCaption = activeImage?.caption?.trim() ?? '';
  const hasMultiple = images.length > 1;

  const counterLabel = hasMultiple
    ? t('routePhotoCounter')
        .replace('{current}', String(safeIndex + 1))
        .replace('{total}', String(images.length))
    : null;

  const setLightbox = (open: boolean) => {
    setLightboxOpen(open);
  };

  useEffect(() => {
    if (!isActiveStep && lightboxOpen) {
      setLightboxOpen(false);
    }
  }, [isActiveStep, lightboxOpen]);

  useEffect(() => {
    if (!isActiveStep) return;
    onLightboxOpenChange?.(lightboxOpen);
  }, [isActiveStep, lightboxOpen, onLightboxOpenChange]);

  if (!imageSrc) return null;

  const captionSize = 14 * baseFontSize;
  const hintSize = 13 * baseFontSize;
  const BRAND_BLUE = '#4A90E2';

  return (
    <>
      <div className="flex-1 min-h-[160px] flex flex-col gap-2" aria-live="polite">
        {hasMultiple && counterLabel && (
          <p
            className="text-center font-semibold text-eldergo-navy"
            style={{ fontSize: `${captionSize}px` }}
          >
            {counterLabel}
          </p>
        )}

        <button
          type="button"
          onClick={() => setLightbox(true)}
          className="relative flex-1 min-h-[160px] rounded-xl overflow-hidden border border-eldergo-border shadow-sm text-left w-full group"
          aria-label={t('routePhotoEnlarge')}
        >
          <ImageWithFallback
            src={imageSrc}
            alt={imageCaption || imageAlt}
            className="w-full h-full object-cover"
          />
          <span
            className="absolute bottom-2 right-2 rounded-lg bg-white/92 px-2.5 py-1 pointer-events-none font-semibold shadow-sm"
            style={{ fontSize: `${hintSize}px`, color: BRAND_BLUE }}
            aria-hidden
          >
            {t('routePhotoTapEnlarge')}
          </span>
        </button>

        {imageCaption && (
          <p
            className="text-center text-eldergo-navy/85 px-3 leading-snug"
            style={{ fontSize: `${captionSize}px` }}
          >
            {imageCaption}
          </p>
        )}

        <PhotoNumberStrip
          images={images}
          imageIndex={safeIndex}
          onSelect={onImageIndexChange}
          baseFontSize={baseFontSize}
          t={t}
        />
      </div>

      <RoutePhotoLightbox
        open={lightboxOpen}
        onClose={() => setLightbox(false)}
        imageSrc={imageSrc}
        imageAlt={imageCaption || imageAlt}
        caption={imageCaption}
        baseFontSize={baseFontSize}
        t={t}
      />
    </>
  );
}
