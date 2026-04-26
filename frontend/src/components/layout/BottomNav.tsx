import { Map, Sliders, Bot, HelpCircle, Train } from 'lucide-react';
import { useAppContext } from '../../app/AppProvider';
import { getTranslation } from '../../i18n/translations';

interface BottomNavProps {
  activeTab?: string;
  onChatbotClick?: () => void;
  onStationClick?: () => void;
  onPlanningClick?: () => void;
  onHelpClick?: () => void;
  onPreferenceClick?: () => void;
}

export default function BottomNav({
  activeTab = 'home',
  onChatbotClick,
  onStationClick,
  onPlanningClick,
  onHelpClick,
  onPreferenceClick
}: BottomNavProps) {
  const { language } = useAppContext();
  const t = (key: string) => getTranslation(language, key as any);

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-gray-200 px-4 py-3 z-50">
      <div className="grid grid-cols-5 gap-2 items-center max-w-5xl mx-auto">
        <button
          onClick={onPlanningClick}
          className={`flex flex-col items-center gap-1 py-2 ${
            activeTab === 'planning' ? 'text-[#4A90E2]' : 'text-[#1E3A5F]'
          }`}
        >
          <Map size={26} strokeWidth={activeTab === 'planning' ? 2.5 : 2} />
          <span className="text-[13px] font-medium" style={{ fontFamily: 'Poppins' }}>{t('planning')}</span>
        </button>

        <button
          onClick={onStationClick}
          className={`flex flex-col items-center gap-1 py-2 ${
            activeTab === 'station' ? 'text-[#4A90E2]' : 'text-[#1E3A5F]'
          }`}
        >
          <Train size={26} strokeWidth={activeTab === 'station' ? 2.5 : 2} />
          <span className="text-[13px] font-medium" style={{ fontFamily: 'Poppins' }}>{t('stations')}</span>
        </button>

        <button
          onClick={onChatbotClick}
          className="flex items-center justify-center py-2"
        >
          <div className="w-16 h-16 bg-[#4A90E2] rounded-full flex items-center justify-center shadow-xl hover:bg-[#3A7FD2] transition-colors">
            <Bot size={32} strokeWidth={2.5} className="text-white" />
          </div>
        </button>

        <button
          onClick={onPreferenceClick}
          className={`flex flex-col items-center gap-1 py-2 ${
            activeTab === 'preference' ? 'text-[#4A90E2]' : 'text-[#1E3A5F]'
          }`}
        >
          <Sliders size={26} strokeWidth={activeTab === 'preference' ? 2.5 : 2} />
          <span className="text-[13px] font-medium whitespace-nowrap" style={{ fontFamily: 'Poppins' }}>{t('preference')}</span>
        </button>

        <button
          onClick={onHelpClick}
          className={`flex flex-col items-center gap-1 py-2 ${
            activeTab === 'help' ? 'text-[#4A90E2]' : 'text-[#1E3A5F]'
          }`}
        >
          <HelpCircle size={26} strokeWidth={activeTab === 'help' ? 2.5 : 2} />
          <span className="text-[13px] font-medium" style={{ fontFamily: 'Poppins' }}>{t('help')}</span>
        </button>
      </div>
    </div>
  );
}
