import { ChevronLeft, CreditCard, Coins } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';

interface TicketGuidePageProps {
  onNavigateToHelp: () => void;
  onNavigateToPlanning: () => void;
  onNavigateToStation: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function TicketGuidePage({
  onNavigateToHelp,
  onNavigateToPlanning,
  onNavigateToStation,
  onNavigateToPreference,
  onShowChatbot
}: TicketGuidePageProps) {
  const { fontSize } = useAppContext();
  const baseFontSize = fontSize === 'large' ? 1.25 : 1;

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
        <div className="absolute inset-0 bg-white/42" />
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
        <div className="max-w-2xl mx-auto">
          <button
            onClick={onNavigateToHelp}
            className="flex items-center gap-2 text-[#4A90E2] mb-6 hover:text-[#3A7FD2]"
          >
            <ChevronLeft size={24 * baseFontSize} strokeWidth={2.5} />
            <span className="font-medium" style={{ fontSize: `${18 * baseFontSize}px` }}>Back to Help</span>
          </button>

          <h2 className="font-semibold text-[#1E3A5F] mb-8" style={{ fontSize: `${30 * baseFontSize}px` }}>
            How to Buy a Ticket
          </h2>

          <div className="space-y-6">
            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-[#4A90E2]/20 rounded-full flex items-center justify-center">
                  <CreditCard size={28 * baseFontSize} strokeWidth={2.5} className="text-[#4A90E2]" />
                </div>
                <h3 className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${22 * baseFontSize}px` }}>
                  Method 1: Touch 'n Go Card
                </h3>
              </div>
              <p className="text-gray-700 leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                <span className="font-semibold text-[#6BBF59]">Highly Recommended!</span> This is the easiest and fastest way to travel.
              </p>
              <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                Just tap your card on the scanner at the entry gate, and tap it again when you exit. No need to queue for tickets!
              </p>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-[#6BBF59]/20 rounded-full flex items-center justify-center">
                  <Coins size={28 * baseFontSize} strokeWidth={2.5} className="text-[#6BBF59]" />
                </div>
                <h3 className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${22 * baseFontSize}px` }}>
                  Method 2: Buying a Token
                </h3>
              </div>
              <p className="text-gray-700 leading-relaxed mb-4" style={{ fontSize: `${18 * baseFontSize}px` }}>
                If you prefer to buy a ticket at the station, follow these simple steps:
              </p>
              <ol className="space-y-3 text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                <li className="flex gap-3">
                  <span className="font-bold text-[#4A90E2] flex-shrink-0">1.</span>
                  <span><span className="font-semibold">Find the Machine:</span> Look for the blue or green Ticket Vending Machines at the station entrance.</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-[#4A90E2] flex-shrink-0">2.</span>
                  <span><span className="font-semibold">Select Language:</span> Tap the screen to choose English or Bahasa Melayu.</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-[#4A90E2] flex-shrink-0">3.</span>
                  <span><span className="font-semibold">Choose Destination:</span> Tap your target station name on the screen map.</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-[#4A90E2] flex-shrink-0">4.</span>
                  <span><span className="font-semibold">Pay:</span> Insert your cash or coins into the slots.</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-[#4A90E2] flex-shrink-0">5.</span>
                  <span><span className="font-semibold">Collect:</span> Take your blue token and your change from the bottom tray.</span>
                </li>
              </ol>
            </div>

            <div className="bg-[#FFE5B4] border-l-4 border-[#E67E22] p-6 rounded-xl">
              <p className="font-semibold text-[#1E3A5F] mb-2" style={{ fontSize: `${18 * baseFontSize}px` }}>
                💡 Need Help at the Station?
              </p>
              <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                Don't worry! Look for the station staff wearing red uniforms. They are always happy to help you buy a ticket or find your way.
              </p>
            </div>
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
