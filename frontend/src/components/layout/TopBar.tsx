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
      className="h-16 w-auto"
    />
  );

  return (
    <div className="fixed top-0 left-0 right-0 bg-white border-b border-eldergo-border/50 px-6 py-2 flex justify-between items-center z-50">
      <div className="flex items-center gap-3">
        {onLogoClick ? (
          // When page provides a handler, logo area becomes a back action.
          <button
            type="button"
            onClick={onLogoClick}
            aria-label="Back"
            className="flex items-center gap-2 rounded-full border-2 border-eldergo-border bg-white px-4 py-2 text-eldergo-navy shadow-sm transition-all hover:border-eldergo-blue hover:text-eldergo-blue active:scale-95 focus:outline-none focus:ring-2 focus:ring-eldergo-blue focus:ring-offset-2"
          >
            <ChevronLeft size={22} strokeWidth={2.5} />
            <span className="text-[16px] font-semibold">Back</span>
          </button>
        ) : (
          logo
        )}
      </div>
      <div className="flex gap-3">
        <button
          onClick={toggleLanguage}
          className={`flex items-center gap-2 px-4 py-2 border-2 rounded-full transition-all shadow-sm active:scale-95 ${
            language === 'BM'
              ? 'bg-eldergo-blue border-eldergo-blue text-white'
              : 'bg-white/90 border-eldergo-border text-eldergo-navy hover:bg-eldergo-blue hover:border-eldergo-blue hover:text-white'
          }`}
          style={{ fontFamily: 'Poppins' }}
        >
          <Globe size={18} strokeWidth={2.5} />
          <span className="text-[16px] font-medium">{language === 'EN' ? 'BM' : 'EN'}</span>
        </button>
        <button
          onClick={toggleFontSize}
          className={`flex items-center gap-2 px-4 py-2 border-2 rounded-full transition-all shadow-sm active:scale-95 ${
            fontSize !== 'standard'
              ? 'bg-eldergo-green border-eldergo-green text-white'
              : 'bg-white/90 border-eldergo-border text-eldergo-navy hover:bg-eldergo-green hover:border-eldergo-green hover:text-white'
          }`}
          style={{ fontFamily: 'Poppins' }}
        >
          <Type size={18} strokeWidth={2.5} />
          <span className="text-[16px] font-medium">{fontSize === 'extra_large' ? 'A++' : 'A+'}</span>
        </button>
      </div>
    </div>
  );
}
