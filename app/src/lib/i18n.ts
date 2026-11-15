// Two interface languages: English (the source) and Polish.
// The English text itself is the key: t('My field') returns the Polish text from lib/pl.ts when Polish is on,
// and the English text otherwise or when a translation is missing. Variables go in braces: t('{n} fields', { n: 11 }).
import { createContext, useCallback, useContext } from 'react'
import { PL } from '@/lib/pl'
import type { TempUnit } from '@/lib/units'

export type Lang = 'en' | 'pl'
export type Translate = (text: string, vars?: Record<string, string | number>) => string

const STORAGE_KEY = 'plotwise-lang'

// Keys that carry a hint for the translator, not text to show: Polish needs another case or a shorter word there,
// English does not.
const EN: Record<string, string> = {
  'wheat in genitive': 'wheat',
  'sorghum in genitive': 'sorghum',
  'Aerial photo (tab)': 'Aerial photo',
  'Greenness (tab)': 'Greenness',
  'Surface heat (tab)': 'Surface heat',
  '{n} in (axis)': '{n} in',
  // Rotation codes shown to people: the words, not the letters.
  'W-F': 'wheat – fallow',
  'W-S-F': 'wheat – sorghum – fallow',
  'W-C-F': 'wheat – corn – fallow',
  'W-S-S-F': 'wheat – sorghum – sorghum – fallow',
  'W-W-S-F': 'wheat – wheat – sorghum – fallow',
  'W-Sf-F': 'wheat – sunflower – fallow',
  // Evidence status words: the short codes of the evidence file, written out.
  'How we have it:': 'Basis:',
  read: 'full report read',
  data: 'source data',
  abstract: 'abstract only',
  secondhand: 'secondhand source',
  assumption: 'our assumption',
}

// Dev only: every text shown in Polish without an entry in lib/pl.ts is reported once in the console.
const reportedMissing = new Set<string>()

export function translate(lang: Lang, text: string, vars?: Record<string, string | number>): string {
  if (import.meta.env.DEV && lang === 'pl' && text && !(text in PL) && !reportedMissing.has(text)) {
    reportedMissing.add(text)
    console.warn('[i18n] missing Polish text:', text)
  }
  const base = lang === 'pl' ? (PL[text] ?? text) : (EN[text] ?? text)
  if (!vars) return base
  return base
    .replace(/\{(\w+)\|([^}]+)\}/g, (match, name: string, forms: string) =>
      name in vars ? pluralForm(lang, vars[name], forms.split('|')) : match,
    )
    .replace(/\{(\w+)\}/g, (match, name: string) => (name in vars ? String(vars[name]) : match))
}

// Word form for a number: "{n|pole|pola|pól|pola}" picks the Polish form for one / few (2–4) / many / a fraction.
// Only the word is written; the number itself goes in a separate {n}. The value may already be formatted ("1 221", "5,3").
const PLURAL_ORDER = ['one', 'few', 'many', 'other'] as const
function pluralForm(lang: Lang, value: string | number, forms: string[]): string {
  const number =
    typeof value === 'number' ? value : Number(String(value).replace(/[\s  +]/g, '').replace('−', '-').replace(',', '.'))
  if (!Number.isFinite(number)) return forms[forms.length - 1]
  // A number written with decimals ("1,0") takes the fraction form even when its value is whole.
  if (lang === 'pl' && typeof value === 'string' && /,\d/.test(value)) return forms[forms.length - 1]
  const category = new Intl.PluralRules(lang === 'pl' ? 'pl-PL' : 'en-US').select(Math.abs(number))
  const index = PLURAL_ORDER.indexOf(category as (typeof PLURAL_ORDER)[number])
  return forms[Math.min(index < 0 ? forms.length - 1 : index, forms.length - 1)]
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

// Temperatures: Fahrenheit in English (US farmers), Celsius in Polish (Polish readers think in °C).
export function useTempUnit(): TempUnit {
  return useContext(LanguageContext).lang === 'pl' ? 'C' : 'F'
}

// Locale for dates (month names). Numbers stay in the US format in both languages, like the US units.
export function useDateLocale(): string {
  return useContext(LanguageContext).lang === 'pl' ? 'pl-PL' : 'en-US'
}
