import { useApp } from '@/contexts/AppContext';
import plTranslations from '@/locales/pl.json';
import enTranslations from '@/locales/en.json';

type TranslationKeys = typeof plTranslations;
type NestedKeyOf<ObjectType extends object> = {
  [Key in keyof ObjectType & (string | number)]: ObjectType[Key] extends object
    ? `${Key}` | `${Key}.${NestedKeyOf<ObjectType[Key]>}`
    : `${Key}`;
}[keyof ObjectType & (string | number)];

type TranslationKey = NestedKeyOf<TranslationKeys>;

const translations = {
  pl: plTranslations,
  en: enTranslations,
};

export function useTranslation() {
  const { language } = useApp();

  const t = (key: TranslationKey, params?: Record<string, string | number>): string => {
    const keys = key.split('.');
    let value: any = translations[language];

    for (const k of keys) {
      value = value?.[k];
    }

    if (typeof value !== 'string') {
      console.warn(`Translation missing for key: ${key}`);
      return key;
    }

    if (!params) {
      return value;
    }

    // Simple parameter replacement
    return value.replace(/\{(\w+)\}/g, (match, paramKey) => {
      return params[paramKey]?.toString() || match;
    });
  };

  return { t, language };
}