import { ChevronLeft, MapPin, Sliders, HelpCircle, ArrowRight, User, Building2 } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';

interface UseElderGoPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToHelp: () => void;
  onNavigateToStation: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function UseElderGoPage({
  onNavigateToPlanning,
  onNavigateToHelp,
  onNavigateToStation,
  onNavigateToPreference,
  onShowChatbot
}: UseElderGoPageProps) {
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

          <h2 className="font-semibold text-[#1E3A5F] mb-6" style={{ fontSize: `${30 * baseFontSize}px` }}>
            How to Use ElderGo
          </h2>

          <div className="bg-[#FFE5B4] border-l-4 border-[#E67E22] p-6 rounded-xl mb-8 flex items-start gap-4">
            <div className="w-14 h-14 bg-[#E67E22] rounded-full flex items-center justify-center flex-shrink-0">
              <User size={28 * baseFontSize} strokeWidth={2.5} className="text-white" />
            </div>
            <div>
              <p className="font-semibold text-[#1E3A5F] mb-2" style={{ fontSize: `${20 * baseFontSize}px` }}>
                Meet Mr. Tan!
              </p>
              <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                He wants to visit his friend at the hospital today. Let's see how ElderGo helps him travel safely and easily.
              </p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-[#6BBF59]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Sliders size={24 * baseFontSize} strokeWidth={2.5} className="text-[#6BBF59]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-[#1E3A5F] mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    Step 1: Set Your Needs
                  </h3>
                  <p className="text-gray-700 leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    Mr. Tan prefers using elevators instead of stairs. He taps the "Preference" button at the bottom of the screen and turns on <span className="font-semibold text-[#6BBF59]">"Accessibility First"</span>.
                  </p>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    Now, the app will only show him routes with elevators or ramps!
                  </p>
                </div>
              </div>
              <button
                onClick={onNavigateToPreference}
                className="w-full bg-[#6BBF59] hover:bg-[#5AAF49] text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
                style={{ fontSize: `${18 * baseFontSize}px` }}
              >
                Set My Preference
                <ArrowRight size={20 * baseFontSize} strokeWidth={2.5} />
              </button>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-[#4A90E2]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <MapPin size={24 * baseFontSize} strokeWidth={2.5} className="text-[#4A90E2]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-[#1E3A5F] mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    Step 2: Plan Your Trip
                  </h3>
                  <p className="text-gray-700 leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    He types his destination in the large "Where to?" box on the Home page.
                  </p>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    Instead of showing confusing options, ElderGo gives him <span className="font-semibold text-[#4A90E2]">one best route</span> that perfectly matches his needs.
                  </p>
                </div>
              </div>
              <button
                onClick={onNavigateToPlanning}
                className="w-full bg-[#4A90E2] hover:bg-[#3A7FD2] text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
                style={{ fontSize: `${18 * baseFontSize}px` }}
              >
                Try Planning a Route
                <ArrowRight size={20 * baseFontSize} strokeWidth={2.5} />
              </button>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-[#E67E22]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <HelpCircle size={24 * baseFontSize} strokeWidth={2.5} className="text-[#E67E22]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-[#1E3A5F] mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    Step 3: Follow the Steps
                  </h3>
                  <p className="text-gray-700 leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    Mr. Tan chooses "Text View". He reads his route step-by-step, just like reading a book.
                  </p>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    The app even gives him a gentle reminder to bring an umbrella because it might rain!
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-[#1E3A5F]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Building2 size={24 * baseFontSize} strokeWidth={2.5} className="text-[#1E3A5F]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-[#1E3A5F] mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    Explore Station Information
                  </h3>
                  <p className="text-gray-700 leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    Want to know if a station has wheelchair access or elevators before you travel?
                  </p>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    The <span className="font-semibold text-[#1E3A5F]">Stations page</span> shows you detailed information about each station, including accessibility features, ticket counters, and operating hours.
                  </p>
                </div>
              </div>
              <button
                onClick={onNavigateToStation}
                className="w-full bg-[#1E3A5F] hover:bg-[#15283F] text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
                style={{ fontSize: `${18 * baseFontSize}px` }}
              >
                View Station Information
                <ArrowRight size={20 * baseFontSize} strokeWidth={2.5} />
              </button>
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
