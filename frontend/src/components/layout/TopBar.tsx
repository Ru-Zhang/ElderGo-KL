import { Globe, Type } from 'lucide-react';
import { useAppContext } from '../../app/AppProvider';

export default function TopBar() {
  const { language, fontSize, toggleLanguage, toggleFontSize } = useAppContext();

  return (
    <div className="fixed top-0 left-0 right-0 bg-white/70 backdrop-blur-md border-b border-gray-200/50 px-6 py-2 flex justify-between items-center z-50">
      <div className="flex items-center gap-3">
        <img
          src="https://github.com/Ru-Zhang/ElderGo-KL/blob/main/img/logo/ElderGo%20KL%20-%20app%20icon.png?raw=true"
          alt="ElderGo KL"
          className="h-16 w-auto"
        />
      </div>
      <div className="flex gap-3">
        <button
          onClick={toggleLanguage}
          className={`flex items-center gap-2 px-4 py-2 border-2 rounded-full transition-all shadow-sm active:scale-95 ${
            language === 'BM'
              ? 'bg-[#4A90E2] border-[#4A90E2] text-white'
              : 'bg-white/90 border-gray-300 text-[#1E3A5F] hover:bg-[#4A90E2] hover:border-[#4A90E2] hover:text-white'
          }`}
          style={{ fontFamily: 'Poppins' }}
        >
          <Globe size={18} strokeWidth={2.5} />
          <span className="text-[16px] font-medium">{language === 'EN' ? 'BM' : 'EN'}</span>
        </button>
        <button
          onClick={toggleFontSize}
          className={`flex items-center gap-2 px-4 py-2 border-2 rounded-full transition-all shadow-sm active:scale-95 ${
            fontSize === 'large'
              ? 'bg-[#6BBF59] border-[#6BBF59] text-white'
              : 'bg-white/90 border-gray-300 text-[#1E3A5F] hover:bg-[#6BBF59] hover:border-[#6BBF59] hover:text-white'
          }`}
          style={{ fontFamily: 'Poppins' }}
        >
          <Type size={18} strokeWidth={2.5} />
          <span className="text-[16px] font-medium">A+</span>
        </button>
      </div>
    </div>
  );
}
