import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import * as Switch from '@radix-ui/react-switch';
import { useAppContext } from '../../app/AppProvider';

interface PreferencesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function PreferencesModal({ isOpen, onClose }: PreferencesModalProps) {
  const { preferences, updatePreferences } = useAppContext();
  const [localPreferences, setLocalPreferences] = useState(preferences);

  useEffect(() => {
    if (isOpen) {
      setLocalPreferences(preferences);
    }
  }, [isOpen, preferences]);

  const handleSave = () => {
    updatePreferences(localPreferences);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-6 p-8" style={{ fontFamily: 'Poppins' }}>
        <button
          onClick={onClose}
          className="absolute top-6 right-6 text-[#1E3A5F] hover:bg-gray-100 rounded-full p-2"
        >
          <X size={28} strokeWidth={2.5} />
        </button>

        <h2 className="text-3xl font-semibold text-[#1E3A5F] mb-8">
          Set Your Travel Preferences
        </h2>

        <div className="space-y-6 mb-10">
          <div className="flex items-center justify-between p-6 bg-[#F5F7FA] rounded-xl border-2 border-gray-200">
            <span className="text-[20px] font-medium text-[#1E3A5F]">
              Accessibility first (Wheelchair/Lift)
            </span>
            <Switch.Root
              className="w-16 h-8 bg-gray-300 rounded-full relative data-[state=checked]:bg-[#6BBF59] transition-colors"
              checked={localPreferences.accessibilityFirst}
              onCheckedChange={(checked) => setLocalPreferences({ ...localPreferences, accessibilityFirst: checked })}
            >
              <Switch.Thumb className="block w-7 h-7 bg-white rounded-full shadow-lg transition-transform translate-x-0.5 data-[state=checked]:translate-x-[34px]" />
            </Switch.Root>
          </div>

          <div className="flex items-center justify-between p-6 bg-[#F5F7FA] rounded-xl border-2 border-gray-200">
            <span className="text-[20px] font-medium text-[#1E3A5F]">
              Least walk
            </span>
            <Switch.Root
              className="w-16 h-8 bg-gray-300 rounded-full relative data-[state=checked]:bg-[#6BBF59] transition-colors"
              checked={localPreferences.leastWalk}
              onCheckedChange={(checked) => setLocalPreferences({ ...localPreferences, leastWalk: checked })}
            >
              <Switch.Thumb className="block w-7 h-7 bg-white rounded-full shadow-lg transition-transform translate-x-0.5 data-[state=checked]:translate-x-[34px]" />
            </Switch.Root>
          </div>

          <div className="flex items-center justify-between p-6 bg-[#F5F7FA] rounded-xl border-2 border-gray-200">
            <span className="text-[20px] font-medium text-[#1E3A5F]">
              Fewest Transfers
            </span>
            <Switch.Root
              className="w-16 h-8 bg-gray-300 rounded-full relative data-[state=checked]:bg-[#6BBF59] transition-colors"
              checked={localPreferences.fewestTransfers}
              onCheckedChange={(checked) => setLocalPreferences({ ...localPreferences, fewestTransfers: checked })}
            >
              <Switch.Thumb className="block w-7 h-7 bg-white rounded-full shadow-lg transition-transform translate-x-0.5 data-[state=checked]:translate-x-[34px]" />
            </Switch.Root>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="w-full bg-[#E67E22] hover:bg-[#D35400] text-white text-[22px] font-semibold py-5 rounded-xl transition-colors min-h-[64px]"
        >
          Save & Continue
        </button>
      </div>
    </div>
  );
}
