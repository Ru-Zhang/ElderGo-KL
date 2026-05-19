import { useCallback, useEffect, useRef, useState } from 'react';

const MIN_SCALE = 1;
const MAX_SCALE = 4;
const DOUBLE_TAP_MS = 300;

function touchDistance(touches: TouchList): number {
  if (touches.length < 2) return 0;
  const dx = touches[0].clientX - touches[1].clientX;
  const dy = touches[0].clientY - touches[1].clientY;
  return Math.hypot(dx, dy);
}

interface PinchZoomImageProps {
  src: string;
  alt: string;
  /** Reset zoom when the parent lightbox closes. */
  active?: boolean;
  className?: string;
}

/**
 * Scale-only pinch zoom (no pan). Image stays centered; overflow is clipped.
 */
export default function PinchZoomImage({
  src,
  alt,
  active = true,
  className = '',
}: PinchZoomImageProps) {
  const [scale, setScale] = useState(1);
  const scaleRef = useRef(1);
  const pinchStartDistance = useRef<number | null>(null);
  const pinchStartScale = useRef(1);
  const lastTapTime = useRef(0);
  const zoneRef = useRef<HTMLDivElement>(null);

  scaleRef.current = scale;

  useEffect(() => {
    if (!active) setScale(1);
  }, [active]);

  const clampScale = (value: number) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, value));

  const handleTouchStart = useCallback((event: TouchEvent) => {
    if (event.touches.length === 2) {
      pinchStartDistance.current = touchDistance(event.touches);
      pinchStartScale.current = scaleRef.current;
    }
  }, []);

  const handleTouchMove = useCallback((event: TouchEvent) => {
    if (event.touches.length !== 2 || pinchStartDistance.current == null) return;
    event.preventDefault();
    const distance = touchDistance(event.touches);
    if (pinchStartDistance.current <= 0) return;
    const next = clampScale(pinchStartScale.current * (distance / pinchStartDistance.current));
    setScale(next);
  }, []);

  const handleTouchEnd = useCallback((event: TouchEvent) => {
    if (event.touches.length < 2) {
      pinchStartDistance.current = null;
    }
  }, []);

  const handleDoubleTap = useCallback(() => {
    const now = Date.now();
    if (now - lastTapTime.current < DOUBLE_TAP_MS) {
      setScale(1);
      lastTapTime.current = 0;
      return;
    }
    lastTapTime.current = now;
  }, []);

  useEffect(() => {
    const el = zoneRef.current;
    if (!el || !active) return;

    el.addEventListener('touchstart', handleTouchStart, { passive: true });
    el.addEventListener('touchmove', handleTouchMove, { passive: false });
    el.addEventListener('touchend', handleTouchEnd, { passive: true });
    el.addEventListener('touchcancel', handleTouchEnd, { passive: true });

    return () => {
      el.removeEventListener('touchstart', handleTouchStart);
      el.removeEventListener('touchmove', handleTouchMove);
      el.removeEventListener('touchend', handleTouchEnd);
      el.removeEventListener('touchcancel', handleTouchEnd);
    };
  }, [active, handleTouchStart, handleTouchMove, handleTouchEnd]);

  return (
    <div
      ref={zoneRef}
      className={`h-full w-full flex items-center justify-center overflow-hidden touch-none ${className}`}
      onClick={handleDoubleTap}
    >
      <img
        src={src}
        alt={alt}
        draggable={false}
        className="max-w-full max-h-full object-contain select-none pointer-events-none"
        style={{
          transform: `scale(${scale})`,
          transformOrigin: 'center center',
        }}
      />
    </div>
  );
}
