// Two interface languages: English (the source) and Polish.
// The English text itself is the key: t('My field') returns the Polish text from lib/pl.ts when Polish is on,
// and the English text otherwise or when a translation is missing. Variables go in braces: t('{n} fields', { n: 11 }).
import { createContext, useCallback, useContext } from 'react'
import { PL } from '@/lib/pl'

export type Lang = 'en' | 'pl'
export type Translate = (text: string, vars?: Record<string, string | number>) => string

const STORAGE_KEY = 'plotwise-lang'

export function translate(lang: Lang, text: string, vars?: Record<string, string | number>): string {
  const base = lang === 'pl' ? (PL[text] ?? text) : text
  if (!vars) return base
  return base.replace(/\{(\w+)\}/g, (match, name: string) => (name in vars ? String(vars[name]) : match))
}

export function readStoredLang(): Lang {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'pl' ? 'pl' : 'en'
  } catch {
    // Private mode or blocked storage: stay with English.
    return 'en'
  }
}

export function storeLang(lang: Lang) {
  try {
    localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    // The choice simply does not persist.
  }
}

export const LanguageContext = createContext<{ lang: Lang; setLang: (lang: Lang) => void }>({
  lang: 'en',
  setLang: () => {},
})

export function useLang() {
  return useContext(LanguageContext)
}

// Translation function for the current language.
export function useT(): Translate {
  const { lang } = useContext(LanguageContext)
  return useCallback((text, vars) => translate(lang, text, vars), [lang])
}

// Locale for dates (month names). Numbers stay in the US format in both languages, like the US units.
export function useDateLocale(): string {
  return useContext(LanguageContext).lang === 'pl' ? 'pl-PL' : 'en-US'
}
