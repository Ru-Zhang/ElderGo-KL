import { ChevronLeft, Globe, Type } from 'lucide-react';
import { useAppContext } from '../../app/AppProvider';

interface TopBarProps {
  onLogoClick?: () => void;
}

export default function TopBar({ onLogoClick }: TopBarProps) {
  const { language, fontSize, toggleLanguage, toggleFontSize } = useAppContext();
  const logo = (
    <img
      src="/eldergo-logo.png"
      alt="ElderGo KL"
      className="h-11 max-h-[48px] w-auto max-w-[min(180px,46vw)] object-contain sm:h-16 sm:max-h-none sm:max-w-none"
    />
  );

  return (
    <div className="fixed top-0 left-0 right-0 z-50 max-w-full overflow-x-hidden border-b border-eldergo-border/50 bg-white px-3 py-2 sm:px-6">
      <div className="mx-auto flex max-w-full items-center justify-between gap-2">
        <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-3">
          {onLogoClick ? (
            <button
              type="button"
              onClick={onLogoClick}
              aria-label="Back"
              className="flex max-w-full min-w-0 shrink items-center gap-1.5 rounded-full border-2 border-eldergo-border bg-white px-2.5 py-2 text-eldergo-navy shadow-sm transition-all hover:border-eldergo-blue hover:text-eldergo-blue active:scale-95 focus:outline-none focus:ring-2 focus:ring-eldergo-blue focus:ring-offset-2 sm:gap-2 sm:px-4"
            >
              <ChevronLeft className="shrink-0" size={22} strokeWidth={2.5} />
              <span className="hidden min-[380px]:inline text-[15px] font-semibold sm:text-[16px]">Back</span>
            </button>
          ) : (
            logo
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1.5 sm:gap-3">
          <button
            type="button"
            onClick={toggleLanguage}
            className={`flex items-center gap-1.5 rounded-full border-2 px-2.5 py-2 shadow-sm transition-all active:scale-95 sm:gap-2 sm:px-4 ${
              language === 'BM'
                ? 'border-eldergo-blue bg-eldergo-blue text-white'
                : 'border-eldergo-border bg-white/90 text-eldergo-navy hover:border-eldergo-blue hover:bg-eldergo-blue hover:text-white'
            }`}
            style={{ fontFamily: 'Poppins' }}
            aria-label={language === 'EN' ? 'Switch to Bahasa Melayu' : 'Switch to English'}
          >
            <Globe className="shrink-0" size={18} strokeWidth={2.5} />
            <span className="text-[15px] font-medium sm:text-[16px]">{language === 'EN' ? 'BM' : 'EN'}</span>
          </button>
          <button
            type="button"
            onClick={toggleFontSize}
            className={`flex items-center gap-1.5 rounded-full border-2 px-2.5 py-2 shadow-sm transition-all active:scale-95 sm:gap-2 sm:px-4 ${
              fontSize !== 'standard'
                ? 'border-eldergo-green bg-eldergo-green text-white'
                : 'border-eldergo-border bg-white/90 text-eldergo-navy hover:border-eldergo-green hover:bg-eldergo-green hover:text-white'
            }`}
            style={{ fontFamily: 'Poppins' }}
            aria-label="Adjust text size"
          >
            <Type className="shrink-0" size={18} strokeWidth={2.5} />
            <span className="text-[15px] font-medium sm:text-[16px]">{fontSize === 'extra_large' ? 'A++' : 'A+'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
