/**
 * Brand-colored line code chip used on the station list and detail pages.
 *
 * Source `route_short_name` values from the backend include codes such as
 * KJL/KGL/AGL/SPL/PYL/MRL/BRT/ETS plus long-form KTM Komuter line names.
 * We standardize them into compact codes with elderly-friendly hues so older
 * users can recognize them at a glance.
 *
 * Visual design notes:
 * - Flat colored "signage" labels — NO drop shadow, NO inset highlight, NO
 *   border. The previous sticker/3D treatment caused users to read the chips
 *   as tappable buttons; here we deliberately flatten them so they read as
 *   read-only identifiers.
 * - Text color is uniformly white across every line. PYL (yellow) and MRL
 *   (light green) are nudged slightly darker than the official palette so
 *   white text still clears WCAG large-text contrast on these light hues.
 */
interface LineMeta {
  code: string;
  bg: string;
}

function getLineMeta(rawName: string): LineMeta {
  const upper = rawName.toUpperCase().trim();
  switch (upper) {
    case 'KJL':
      return { code: 'KJL', bg: '#EF3340' };
    case 'AGL':
      return { code: 'AGL', bg: '#F47A1F' };
    case 'SPL':
      return { code: 'SPL', bg: '#E11D48' };
    case 'KGL':
      return { code: 'KGL', bg: '#1FAA3F' };
    case 'PYL':
      // Darker amber/gold so white text retains acceptable contrast.
      return { code: 'PYL', bg: '#D9A300' };
    case 'MRL':
      // Darker fern green so white text retains acceptable contrast.
      return { code: 'MRL', bg: '#5DAB30' };
    case 'BRT':
      return { code: 'BRT', bg: '#9333EA' };
    case 'ETS':
      return { code: 'ETS', bg: '#2563EB' };
    case 'BUS':
      return { code: 'Bus', bg: '#CA8A04' };
    default:
      break;
  }

  if (upper.includes('PORT KLANG')) return { code: 'KTM·PK', bg: '#0EA5E9' };
  if (upper.includes('SEREMBAN')) return { code: 'KTM·SR', bg: '#0EA5E9' };
  if (upper.includes('SKYPARK')) return { code: 'KTM·SK', bg: '#0EA5E9' };
  if (upper.includes('KOMUTER')) return { code: 'KTM', bg: '#0EA5E9' };

  return { code: rawName, bg: '#64748B' };
}

interface LineBadgeProps {
  name: string;
  baseFontSize: number;
}

export function LineBadge({ name, baseFontSize }: LineBadgeProps) {
  const meta = getLineMeta(name);
  return (
    <span
      className="inline-flex items-center justify-center font-bold tracking-wide rounded-md px-3 py-1"
      style={{
        backgroundColor: meta.bg,
        color: '#FFFFFF',
        fontSize: `${15 * baseFontSize}px`,
        minHeight: `${28 * baseFontSize}px`,
      }}
      title={name}
    >
      {meta.code}
    </span>
  );
}
