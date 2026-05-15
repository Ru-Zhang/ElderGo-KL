import { ReactNode, RefObject } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { PlaceSelection } from '../../types/locations';

interface PlanningPlaceFieldProps {
  fieldRef?: RefObject<HTMLDivElement | null>;
  icon: ReactNode;
  placeholder: string;
  value: string;
  clearAriaLabel: string;
  fieldError: string | null;
  showDropdown: boolean;
  suggestions: PlaceSelection[];
  baseFontSize: number;
  onValueChange: (value: string) => void;
  onClear: () => void;
  onInputClick: () => void;
  onFocus: () => void;
  onSelectSuggestion: (suggestion: PlaceSelection, label: string) => void;
  toSuggestionLabel: (value: string) => string;
}

export default function PlanningPlaceField({
  fieldRef,
  icon,
  placeholder,
  value,
  clearAriaLabel,
  fieldError,
  showDropdown,
  suggestions,
  baseFontSize,
  onValueChange,
  onClear,
  onInputClick,
  onFocus,
  onSelectSuggestion,
  toSuggestionLabel
}: PlanningPlaceFieldProps) {
  const hasValue = Boolean(value.trim());
  const inputBorderClass = fieldError
    ? 'border-eldergo-warning focus:border-eldergo-warning'
    : 'border-eldergo-border focus:border-eldergo-blue';

  return (
    <div ref={fieldRef} className="space-y-2">
      <div className="relative">
        <div className="absolute left-5 top-1/2 -translate-y-1/2 z-30 pointer-events-none">
          {icon}
        </div>
        <input
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onValueChange(e.target.value)}
          onClick={onInputClick}
          onFocus={onFocus}
          className={`w-full pl-16 py-5 bg-white border-2 rounded-xl font-medium text-eldergo-navy placeholder:text-eldergo-muted focus:outline-none shadow-md relative z-10 ${hasValue ? 'pr-14' : 'pr-6'} ${inputBorderClass}`}
          style={{ fontSize: `${18 * baseFontSize}px` }}
        />
        {hasValue && (
          <button
            type="button"
            onClick={onClear}
            aria-label={clearAriaLabel}
            className="absolute right-2 top-1/2 -translate-y-1/2 z-30 flex items-center justify-center w-11 h-11 min-w-[44px] min-h-[44px] rounded-full text-eldergo-muted hover:text-eldergo-navy hover:bg-eldergo-bg transition-colors"
          >
            <X size={22 * baseFontSize} strokeWidth={2.5} aria-hidden />
          </button>
        )}
        {showDropdown && suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white border-2 border-eldergo-border rounded-xl shadow-lg z-40 max-h-60 overflow-y-auto">
            {suggestions.map((suggestion, index) => {
              const label = toSuggestionLabel(suggestion.displayName);
              return (
                <button
                  key={`${suggestion.googlePlaceId}-${index}`}
                  type="button"
                  onClick={() => onSelectSuggestion(suggestion, label)}
                  className="w-full px-6 py-4 text-left font-medium text-eldergo-navy hover:bg-eldergo-bg transition-colors border-b border-eldergo-border last:border-b-0"
                  style={{ fontSize: `${18 * baseFontSize}px` }}
                >
                  {label}
                </button>
              );
            })}
          </div>
        )}
      </div>
      {fieldError && (
        <div className="flex items-start gap-2 px-1 text-eldergo-navy font-medium">
          <AlertCircle
            size={20 * baseFontSize}
            strokeWidth={2.5}
            className="text-eldergo-warning flex-shrink-0 mt-0.5"
            aria-hidden
          />
          <p style={{ fontSize: `${16 * baseFontSize}px` }}>{fieldError}</p>
        </div>
      )}
    </div>
  );
}
