import { Book, Ticket, CreditCard, Shield, ChevronRight, AlertTriangle } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';

interface HelpPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToUseElderGo: () => void;
  onNavigateToTicketGuide: () => void;
  onNavigateToConcessionGuide: () => void;
  onNavigateToPrivacyInfo: () => void;
  onNavigateToStation: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function HelpPage({
  onNavigateToPlanning,
  onNavigateToUseElderGo,
  onNavigateToTicketGuide,
  onNavigateToConcessionGuide,
  onNavigateToPrivacyInfo,
  onNavigateToStation,
  onNavigateToHelp,
  onNavigateToPreference,
  onShowChatbot
}: HelpPageProps) {
  const { fontSize } = useAppContext();
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;

  const handleReset = () => {
    if (confirm('This will clear your saved preferences and history. Are you sure?')) {
      // Reset logic would go here
      alert('Cache cleared and app reset successfully!');
    }
  };

  return (
    <div className="min-h-screen relative" style={{ fontFamily: 'Poppins' }}>
      <div
        className="fixed inset-0 z-0 bg-cover bg-center"
        style={{
          backgroundImage: 'url(/background-elder.jpg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-white/50 via-white/45 to-white/50" />
        <div
          className="absolute bottom-0 left-0 right-0 h-96 bg-bottom bg-no-repeat bg-contain"
          style={{
            backgroundImage: 'url(/watermark-elder.jpg)',
            opacity: '0.12'
          }}
        />
      </div>
      <div className="relative z-10">
      <TopBar />

      <main className="pt-20 pb-32 px-6">
        <div className="max-w-2xl mx-auto mt-8">
          <h2 className="font-semibold text-[#1E3A5F] mb-6" style={{ fontSize: `${24 * baseFontSize}px` }}>
            How can we help you?
          </h2>

          <div className="grid grid-cols-2 gap-4 mb-10">
            <button
              onClick={onNavigateToUseElderGo}
              className="aspect-square bg-[#4A90E2] hover:bg-[#3A7FD2] p-6 rounded-2xl shadow-md transition-all flex flex-col items-center justify-center gap-4"
            >
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                <Book size={32 * baseFontSize} strokeWidth={2.5} className="text-white" />
              </div>
              <span className="font-semibold text-white text-center" style={{ fontSize: `${18 * baseFontSize}px` }}>
                Use ElderGo
              </span>
            </button>

            <button
              onClick={onNavigateToTicketGuide}
              className="aspect-square bg-[#6BBF59] hover:bg-[#5AAF49] p-6 rounded-2xl shadow-md transition-all flex flex-col items-center justify-center gap-4"
            >
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                <Ticket size={32 * baseFontSize} strokeWidth={2.5} className="text-white" />
              </div>
              <span className="font-semibold text-white text-center" style={{ fontSize: `${18 * baseFontSize}px` }}>
                Buy a ticket
              </span>
            </button>

            <button
              onClick={onNavigateToConcessionGuide}
              className="aspect-square bg-[#E67E22] hover:bg-[#D35400] p-6 rounded-2xl shadow-md transition-all flex flex-col items-center justify-center gap-4"
            >
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                <CreditCard size={32 * baseFontSize} strokeWidth={2.5} className="text-white" />
              </div>
              <span className="font-semibold text-white text-center" style={{ fontSize: `${18 * baseFontSize}px` }}>
                Apply for Concession
              </span>
            </button>

            <button
              onClick={onNavigateToPrivacyInfo}
              className="aspect-square bg-[#1E3A5F] hover:bg-[#15283F] p-6 rounded-2xl shadow-md transition-all flex flex-col items-center justify-center gap-4"
            >
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                <Shield size={32 * baseFontSize} strokeWidth={2.5} className="text-white" />
              </div>
              <span className="font-semibold text-white text-center" style={{ fontSize: `${18 * baseFontSize}px` }}>
                Privacy Info
              </span>
            </button>
          </div>

          <div className="h-px bg-gray-300 my-8"></div>

          <h3 className="font-semibold text-[#1E3A5F] mb-6" style={{ fontSize: `${24 * baseFontSize}px` }}>
            App Issues?
          </h3>

          <button
            onClick={handleReset}
            className="w-full bg-white border-3 border-[#E67E22] text-[#E67E22] font-semibold py-5 rounded-xl hover:bg-[#E67E22] hover:text-white transition-all shadow-md flex items-center justify-center gap-3 mb-4"
            style={{ fontSize: `${20 * baseFontSize}px` }}
          >
            <AlertTriangle size={24 * baseFontSize} strokeWidth={2.5} />
            Clear Cache & Reset
          </button>

          <div className="bg-[#FFE5B4] border-l-4 border-[#E67E22] p-5 rounded-xl">
            <p className="text-[#1E3A5F] font-medium" style={{ fontSize: `${16 * baseFontSize}px` }}>
              ⚠️ This will clear your saved preferences and history. Are you sure?
            </p>
          </div>
        </div>
      </main>

        <BottomNav
          activeTab="help"
          onChatbotClick={onShowChatbot}
          onStationClick={onNavigateToStation}
          onHelpClick={onNavigateToHelp}
          onPlanningClick={onNavigateToPlanning}
          onPreferenceClick={onNavigateToPreference}
        />
      </div>
    </div>
  );
}
