import { useState, type ReactNode } from 'react';
import { ChatBlock, KeyValueEmphasis } from '../../types/ai';
import { LanguageCode } from '../../types/settings';
import { HoursDisplay } from '../common/HoursDisplay';
import { parseHoursSummary } from '../../utils/hoursParser';
interface ChatMessageBlocksProps {
  blocks: ChatBlock[];
  bodyFontPx: number;
  headingFontPx: number;
  sourcesLabel: string;
  language: LanguageCode;
  t: (key: string) => string;
}

function emphasisClasses(emphasis?: KeyValueEmphasis | null): string {
  switch (emphasis) {
    case 'supported':
      return 'text-eldergo-green font-semibold';
    case 'not_supported':
      return 'text-red-700 font-semibold';
    case 'unknown':
      return 'text-eldergo-warning font-semibold';
    case 'highlight':
      return 'text-eldergo-navy font-bold';
    case 'route_endpoint':
      return 'text-eldergo-navy font-bold';
    default:
      return 'text-eldergo-navy';
  }
}

function labelClasses(emphasis?: KeyValueEmphasis | null): string {
  if (emphasis === 'route_endpoint') {
    return 'text-xs font-bold uppercase tracking-wide text-eldergo-blue';
  }
  return 'font-semibold text-eldergo-navy mb-1';
}

function valueSizeStyle(
  emphasis: KeyValueEmphasis | null | undefined,
  bodyFontPx: number
): { fontSize: string } | undefined {
  if (emphasis === 'highlight') {
    return { fontSize: `${Math.round(bodyFontPx * 1.2)}px` };
  }
  if (emphasis === 'route_endpoint') {
    return { fontSize: `${Math.round(bodyFontPx * 1.1)}px` };
  }
  return undefined;
}

function calloutClasses(tone?: string | null): string {
  switch (tone) {
    case 'warning':
      return 'bg-eldergo-warning-bg border-eldergo-warning text-eldergo-navy';
    case 'success':
      return 'bg-eldergo-green/15 border-eldergo-green text-eldergo-navy';
    default:
      return 'bg-white border-eldergo-blue text-eldergo-navy';
  }
}

function ChatHoursBlock({
  raw,
  bodyFontPx,
  language,
  t
}: {
  raw: string;
  bodyFontPx: number;
  language: LanguageCode;
  t: (key: string) => string;
}) {
  const [lastTrainsExpanded, setLastTrainsExpanded] = useState(false);
  const parsed = parseHoursSummary(raw);
  const fontScale = bodyFontPx / 16;

  if (!parsed) {
    return (
      <p
        className="leading-relaxed whitespace-pre-line break-words [overflow-wrap:anywhere] text-eldergo-navy"
        style={{ fontSize: `${bodyFontPx}px` }}
      >
        {raw}
      </p>
    );
  }

  return (
    <div
      className="rounded-xl border border-eldergo-border bg-white px-3 py-3 min-w-0"
      style={{ fontSize: `${bodyFontPx}px` }}
    >
      <p
        className="font-semibold text-eldergo-navy mb-3"
        style={{ fontSize: `${Math.round(15 * fontScale)}px` }}
      >
        {t('stationHours')}
      </p>
      <HoursDisplay
        parsed={parsed}
        baseFontSize={fontScale}
        t={t}
        language={language}
        isExpanded={lastTrainsExpanded}
        onToggle={() => setLastTrainsExpanded((prev) => !prev)}
      />
    </div>
  );
}

function formatLinesValue(value: string): ReactNode {
  const parts = value.split(',').map((p) => p.trim()).filter(Boolean);
  if (parts.length <= 1) {
    return value;
  }
  return (
    <span className="flex flex-wrap gap-1.5">
      {parts.map((part) => (
        <span
          key={part}
          className="inline-flex items-center rounded-lg bg-eldergo-blue/10 px-2 py-0.5 font-semibold text-eldergo-navy text-sm"
        >
          {part}
        </span>
      ))}
    </span>
  );
}

export default function ChatMessageBlocks({
  blocks,
  bodyFontPx,
  headingFontPx,
  sourcesLabel,
  language,
  t
}: ChatMessageBlocksProps) {
  return (
    <div className="space-y-3 min-w-0">
      {blocks.map((block, blockIndex) => {
        if (block.type === 'heading' && block.text) {
          return (
            <p
              key={blockIndex}
              className="font-bold text-eldergo-navy leading-snug break-words [overflow-wrap:anywhere]"
              style={{ fontSize: `${headingFontPx}px` }}
            >
              {block.text}
            </p>
          );
        }

        if (block.type === 'paragraph' && block.text) {
          return (
            <p
              key={blockIndex}
              className="leading-relaxed break-words [overflow-wrap:anywhere] text-eldergo-navy"
              style={{ fontSize: `${bodyFontPx}px` }}
            >
              {block.text}
            </p>
          );
        }

        if (block.type === 'bullets' && block.items?.length) {
          const prev = blocks[blockIndex - 1];
          const isExampleList =
            prev?.type === 'callout' &&
            typeof prev.text === 'string' &&
            /type your answer|taip jawapan|输入框/i.test(prev.text);
          if (isExampleList) {
            return (
              <ul
                key={blockIndex}
                className="flex flex-wrap gap-2 list-none pl-0"
                aria-label="Examples"
              >
                {block.items.map((item, itemIndex) => (
                  <li
                    key={`${blockIndex}-${itemIndex}`}
                    className="inline-flex min-h-10 items-center rounded-xl border-2 border-dashed border-eldergo-blue/50 bg-white px-3 py-2 font-semibold text-eldergo-navy shadow-sm"
                    style={{ fontSize: `${Math.max(bodyFontPx - 1, 14)}px` }}
                  >
                    {item}
                  </li>
                ))}
              </ul>
            );
          }
          return (
            <ul
              key={blockIndex}
              className="list-disc pl-5 space-y-2 leading-relaxed break-words [overflow-wrap:anywhere] text-eldergo-navy bg-white/60 rounded-xl px-3 py-2"
              style={{ fontSize: `${bodyFontPx}px` }}
            >
              {block.items.map((item, itemIndex) => (
                <li key={`${blockIndex}-${itemIndex}`}>{item}</li>
              ))}
            </ul>
          );
        }

        if (block.type === 'numbered' && block.items?.length) {
          return (
            <ol
              key={blockIndex}
              className="list-decimal pl-5 space-y-2 leading-relaxed break-words [overflow-wrap:anywhere] text-eldergo-navy"
              style={{ fontSize: `${bodyFontPx}px` }}
            >
              {block.items.map((item, itemIndex) => (
                <li key={`${blockIndex}-${itemIndex}`} className="font-medium">
                  {item}
                </li>
              ))}
            </ol>
          );
        }

        if (block.type === 'hours' && block.text) {
          return (
            <ChatHoursBlock
              key={blockIndex}
              raw={block.text}
              bodyFontPx={bodyFontPx}
              language={language}
              t={t}
            />
          );
        }

        if (block.type === 'key_values' && block.rows?.length) {
          const hasRouteEndpoints = block.rows.some((row) => row.emphasis === 'route_endpoint');
          return (
            <dl
              key={blockIndex}
              className={`space-y-3 rounded-xl border px-3 py-3 ${
                hasRouteEndpoints
                  ? 'border-eldergo-blue/40 bg-eldergo-blue/5'
                  : 'border-eldergo-border bg-white/90'
              }`}
              style={{ fontSize: `${bodyFontPx}px` }}
            >
              {block.rows.map((row, rowIndex) => {
                const isLines = /^(lines|laluan|线路)$/i.test(row.label.trim());
                return (
                  <div
                    key={`${blockIndex}-${rowIndex}`}
                    className="border-b border-eldergo-border/60 pb-2 last:border-0 last:pb-0"
                  >
                    <dt className={labelClasses(row.emphasis)}>{row.label}</dt>
                    <dd
                      className={`leading-relaxed break-words [overflow-wrap:anywhere] ${isLines ? '' : emphasisClasses(row.emphasis)}`}
                      style={valueSizeStyle(row.emphasis, bodyFontPx)}
                    >
                      {isLines ? formatLinesValue(row.value) : row.value}
                    </dd>
                  </div>
                );
              })}
            </dl>
          );
        }

        if (block.type === 'callout' && block.text) {
          const isWeatherSnapshot = block.text.includes('°C');
          return (
            <div
              key={blockIndex}
              className={`rounded-xl border-l-4 px-4 py-3 leading-relaxed break-words [overflow-wrap:anywhere] whitespace-pre-line ${
                isWeatherSnapshot ? 'font-semibold' : 'font-medium'
              } ${calloutClasses(block.tone)}`}
              style={{
                fontSize: isWeatherSnapshot
                  ? `${Math.round(bodyFontPx * 1.05)}px`
                  : `${bodyFontPx}px`
              }}
            >
              {block.text}
            </div>
          );
        }

        if (block.type === 'place_cards' && block.links?.length) {
          return (
            <div
              key={blockIndex}
              className="space-y-2"
              style={{ fontSize: `${Math.max(bodyFontPx - 1, 14)}px` }}
            >
              {block.links.map((link, linkIndex) => (
                <div
                  key={`${blockIndex}-${linkIndex}`}
                  className="rounded-xl border-2 border-eldergo-border bg-white px-3 py-3 min-w-0"
                >
                  <p className="font-bold text-eldergo-navy leading-snug break-words [overflow-wrap:anywhere] mb-2">
                    {link.title}
                  </p>
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex min-h-11 items-center font-semibold text-eldergo-blue underline"
                  >
                    {t('chatViewOnMaps')}
                  </a>
                </div>
              ))}
            </div>
          );
        }

        if (block.type === 'sources' && block.links?.length) {
          return (
            <div
              key={blockIndex}
              className="rounded-xl border border-eldergo-border/80 bg-white/70 px-3 py-3 space-y-2"
              style={{ fontSize: `${Math.max(bodyFontPx - 1, 14)}px` }}
            >
              <p className="font-semibold text-eldergo-muted">{block.text || sourcesLabel}</p>
              <ul className="space-y-2">
                {block.links.map((link, linkIndex) => (
                  <li key={`${blockIndex}-${linkIndex}`}>
                    <a
                      href={link.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex min-h-11 items-center font-semibold text-eldergo-blue underline break-words [overflow-wrap:anywhere]"
                    >
                      {link.title}
                      {link.org &&
                      String(link.org).trim().toLowerCase() !== String(link.title ?? '').trim().toLowerCase()
                        ? ` (${link.org})`
                        : ''}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          );
        }

        return null;
      })}
    </div>
  );
}
