import type { ReactNode } from 'react';

export function HelpPageTitle({
  children,
  baseFontSize,
  icon,
}: {
  children: ReactNode;
  baseFontSize: number;
  icon?: ReactNode;
}) {
  if (icon) {
    return (
      <div className="flex items-center gap-4 mb-2">
        {icon}
        <h2 className="font-semibold text-eldergo-navy" style={{ fontSize: `${30 * baseFontSize}px` }}>
          {children}
        </h2>
      </div>
    );
  }
  return (
    <h2 className="font-semibold text-eldergo-navy mb-2" style={{ fontSize: `${30 * baseFontSize}px` }}>
      {children}
    </h2>
  );
}

export function HelpSectionTitle({
  children,
  baseFontSize,
}: {
  children: ReactNode;
  baseFontSize: number;
}) {
  return (
    <h3 className="font-semibold text-eldergo-navy" style={{ fontSize: `${22 * baseFontSize}px` }}>
      {children}
    </h3>
  );
}

export function HelpContentCard({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`bg-white border border-eldergo-border rounded-2xl shadow-md p-5 sm:p-6 ${className}`.trim()}
    >
      {children}
    </div>
  );
}

export function HelpBodyText({
  children,
  baseFontSize,
  className = '',
}: {
  children: ReactNode;
  baseFontSize: number;
  className?: string;
}) {
  return (
    <p
      className={`text-eldergo-muted leading-relaxed ${className}`.trim()}
      style={{ fontSize: `${17 * baseFontSize}px` }}
    >
      {children}
    </p>
  );
}

export function HelpCallout({
  children,
  baseFontSize,
  variant = 'warning',
}: {
  children: ReactNode;
  baseFontSize: number;
  variant?: 'warning' | 'info';
}) {
  const styles =
    variant === 'warning'
      ? 'bg-eldergo-warning-bg border-eldergo-warning text-eldergo-navy'
      : 'bg-eldergo-blue/10 border-eldergo-blue text-eldergo-navy';
  return (
    <div className={`border-l-4 p-5 rounded-xl ${styles}`}>
      <p className="font-medium leading-relaxed" style={{ fontSize: `${16 * baseFontSize}px` }}>
        {children}
      </p>
    </div>
  );
}

export function HelpNavTile({
  label,
  iconSrc,
  onClick,
  baseFontSize,
  hoverBorderClass = 'hover:border-eldergo-blue',
}: {
  label: string;
  iconSrc: string;
  onClick?: () => void;
  baseFontSize: number;
  hoverBorderClass?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`h-52 sm:h-56 bg-white border-2 border-eldergo-border ${hoverBorderClass} p-5 sm:p-6 rounded-2xl shadow-md transition-all flex flex-col items-center justify-center gap-4`}
    >
      <img src={iconSrc} alt="" className="w-20 h-20 flex-shrink-0" />
      <span
        className="min-h-[3.5rem] flex items-center justify-center font-semibold text-eldergo-navy text-center leading-tight line-clamp-2 px-1"
        style={{ fontSize: `${18 * baseFontSize}px` }}
      >
        {label}
      </span>
    </button>
  );
}

export function HelpPrimaryButton({
  children,
  onClick,
  baseFontSize,
  variant = 'green',
}: {
  children: ReactNode;
  onClick?: () => void;
  baseFontSize: number;
  variant?: 'green' | 'blue';
}) {
  const color =
    variant === 'green'
      ? 'bg-eldergo-green hover:bg-eldergo-green-dark'
      : 'bg-eldergo-blue hover:bg-eldergo-blue-dark';
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full ${color} text-white font-semibold py-4 rounded-xl transition-colors shadow-sm text-center`}
      style={{ fontSize: `${18 * baseFontSize}px` }}
    >
      {children}
    </button>
  );
}

export function HelpDivider() {
  return <div className="h-px bg-eldergo-border my-2" />;
}

export function HelpStepCard({
  icon,
  title,
  children,
  action,
  baseFontSize,
}: {
  icon: ReactNode;
  title: string;
  children: ReactNode;
  action?: ReactNode;
  baseFontSize: number;
}) {
  return (
    <HelpContentCard>
      <div className="flex items-start gap-4 mb-4">
        <div className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0">{icon}</div>
        <div className="flex-1 min-w-0">
          <HelpSectionTitle baseFontSize={baseFontSize}>{title}</HelpSectionTitle>
          <div className="mt-3 space-y-3">{children}</div>
        </div>
      </div>
      {action}
    </HelpContentCard>
  );
}
