export const translations = {
  EN: {
    // Planning Page
    howToUse: "How to use ElderGo?",
    from: "From",
    to: "To",
    enterStartingPoint: "Enter starting point",
    enterDestination: "Enter destination",
    search: "Search",

    // Navigation
    planning: "Planning",
    stations: "Stations",
    help: "Help",
    preference: "Preference",

    // Other common labels
    back: "Back",
    next: "Next",
    save: "Save",
    cancel: "Cancel",
  },
  BM: {
    // Planning Page
    howToUse: "Cara menggunakan ElderGo?",
    from: "Dari",
    to: "Ke",
    enterStartingPoint: "Masukkan titik permulaan",
    enterDestination: "Masukkan destinasi",
    search: "Cari",

    // Navigation
    planning: "Perancangan",
    stations: "Stesen",
    help: "Bantuan",
    preference: "Keutamaan",

    // Other common labels
    back: "Kembali",
    next: "Seterusnya",
    save: "Simpan",
    cancel: "Batal",
  }
};

export type Language = keyof typeof translations;
export type TranslationKey = keyof typeof translations.EN;

export const getTranslation = (language: Language, key: TranslationKey): string => {
  return translations[language][key] || translations.EN[key];
};
