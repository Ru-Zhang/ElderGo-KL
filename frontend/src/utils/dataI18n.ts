/**
 * Translate textual values that come from the database / scraped CSV (which
 * are stored in English only) so they follow the user's language setting.
 *
 * We do this on the client because:
 *   - Re-scraping mrt.com.my for BM is brittle and many MRT pages do not have
 *     a Bahasa Melayu version.
 *   - Mutating the database with translations is intrusive and would couple
 *     storage shape to UI concerns.
 *
 * The mapping uses a normalized key (lowercased + alpha-numeric only) so
 * minor source variations like "ATM & TNG Reload Machine" and
 * "ATMs & TnG Reload Machine" both resolve to the same translation.
 */

import type { Language } from '../i18n/translations';

function normalizeKey(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '');
}

// English -> Bahasa Melayu mapping for known facility labels found in the
// scraped mrt.com.my data set. Entries are keyed by the English label as it
// appears in the CSV; lookups go through `normalizeKey` so spelling variants
// (e.g. plurals, punctuation, casing) collapse to one entry.
const FACILITY_BM_BY_EN: Record<string, string> = {
  'Lift': 'Lif',
  'Escalator': 'Eskalator',
  'Escalators': 'Eskalator',
  'Escalator & Lift': 'Eskalator & Lif',
  'Public Toilets': 'Tandas Awam',
  'Customer Service Office': 'Pejabat Khidmat Pelanggan',
  'Surau': 'Surau',
  'Side Platform': 'Platform Sisi',
  'Island Platform': 'Platform Pulau',
  'Side & Island Platform': 'Platform Sisi & Pulau',
  'Island & Side Platform': 'Platform Pulau & Sisi',
  'Side Stacked Platform': 'Platform Bertingkat Sisi',
  'Split Platform': 'Platform Berasingan',
  'Shops': 'Kedai',
  'Shops & Mall': 'Kedai & Pusat Beli-belah',
  'Bus Hub': 'Hab Bas',
  'Bus Stop': 'Perhentian Bas',
  'Bus & Taxi Stop': 'Perhentian Bas & Teksi',
  'Rail Transportation': 'Pengangkutan Kereta Api',
  'Rail and Bus Hub': 'Hab Kereta Api & Bas',
  'Transportation Hub': 'Hab Pengangkutan',
  'Ticket Vending Machine': 'Mesin Tiket',
  'Drinks Vending Machine': 'Mesin Minuman',
  'Dinks Vending Machine': 'Mesin Minuman',
  'Concession Card Counter': 'Kaunter Kad Konsesi',
  'Car Park': 'Tempat Letak Kereta',
  'Car Parking': 'Tempat Letak Kereta',
  'Parking': 'Tempat Letak',
  "Park n' Ride": 'Letak & Naik',
  'Park n Ride': 'Letak & Naik',
  'Park & Ride': 'Letak & Naik',
  'Park and Ride': 'Letak & Naik',
  'Bicycle Parking Facilities': 'Tempat Letak Basikal',
  'Feeder Bus': 'Bas Penghubung',
  'Feeder bus': 'Bas Penghubung',
  'Airport Shuttle': 'Pengangkutan Lapangan Terbang',
  'ATM & TnG Reload Machine': 'ATM & Mesin Isi Semula TnG',
  'ATMs & TnG Reload Machine': 'ATM & Mesin Isi Semula TnG',
  'TnG Reload Machine': 'Mesin Isi Semula TnG',
  'Disabled Friendly': 'Mesra OKU',
  'Nursing Room': 'Bilik Penyusuan',
  'Co-located CIQ Facilities': 'Kemudahan CIQ Bersama',
  'Covered Link Bridge to JB Sentral': 'Jambatan Bersambung ke JB Sentral',
  'Interchange': 'Pertukaran',
  'Interchange Station': 'Stesen Pertukaran',
  'MRT Interchange': 'Pertukaran MRT',
  'LRT Interchange': 'Pertukaran LRT',
  'BRT Interchange': 'Pertukaran BRT',
  'Monorail Interchange': 'Pertukaran Monorel',
  'KL Monorail Interchange': 'Pertukaran KL Monorel',
  'KTM Komuter Interchange': 'Pertukaran KTM Komuter',
  'KTM Komuter & MRT Interchange': 'Pertukaran KTM Komuter & MRT',
  'KTM Interchange': 'Pertukaran KTM',
  'KLIA Transit Interchange': 'Pertukaran KLIA Transit',
  'LRT & MRT Interchanges': 'Pertukaran LRT & MRT',
  'LRT Line Integration': 'Integrasi Laluan LRT',
  'KTM Komuter Integration': 'Integrasi KTM Komuter',
  'Shah Alam Line Interchange (2025)': 'Pertukaran Laluan Shah Alam (2025)',
};

const FACILITY_BM_BY_NORMALIZED: Record<string, string> = Object.fromEntries(
  Object.entries(FACILITY_BM_BY_EN).map(([en, bm]) => [normalizeKey(en), bm]),
);

/**
 * Returns the user-language label for a scraped facility name. Falls back to
 * the English label when no translation is registered so we never display a
 * blank string.
 */
export function translateFacility(label: string, language: Language): string {
  if (!label) return label;
  if (language === 'EN') return label;
  const key = normalizeKey(label);
  return FACILITY_BM_BY_NORMALIZED[key] ?? label;
}

// Day-of-week and "& PH" replacements used inside the parsed hours condition
// strings ("Mon - Sat", "Sun & PH", etc.).
const HOUR_CONDITION_REPLACEMENTS_BM: Array<[RegExp, string]> = [
  [/\bMonday\b/gi, 'Isnin'],
  [/\bTuesday\b/gi, 'Selasa'],
  [/\bWednesday\b/gi, 'Rabu'],
  [/\bThursday\b/gi, 'Khamis'],
  [/\bFriday\b/gi, 'Jumaat'],
  [/\bSaturday\b/gi, 'Sabtu'],
  [/\bSunday\b/gi, 'Ahad'],
  [/\bMon\b/g, 'Isn'],
  [/\bTue\b/g, 'Sel'],
  [/\bWed\b/g, 'Rab'],
  [/\bThu\b/g, 'Kha'],
  [/\bFri\b/g, 'Jum'],
  [/\bSat\b/g, 'Sab'],
  [/\bSun\b/g, 'Ahd'],
  [/&\s*PH\b/gi, '& CU'],
];

export function translateHourCondition(condition: string, language: Language): string {
  if (!condition || language === 'EN') return condition;
  let result = condition;
  for (const [pattern, replacement] of HOUR_CONDITION_REPLACEMENTS_BM) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

// Free-form destination labels in last-train rows (e.g. "Gombak", "Putra
// Heights", "Sungai Buloh"). Most are proper nouns and should not be
// translated; we expose a hook so future edge-cases can be patched without
// touching call sites.
export function translateLastTrainDestination(value: string, _language: Language): string {
  return value;
}
