// Holds the interface language, remembers it in the browser and sets <html lang> for screen readers.
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { LanguageContext, readStoredLang, storeLang, type Lang } from '@/lib/i18n'
import { setNumberLocale } from '@/lib/units'

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(readStoredLang)
  // Set during render, so the children below format their numbers in this language on this very render.
  setNumberLocale(lang)
  useEffect(() => {
    document.documentElement.lang = lang
    storeLang(lang)
  }, [lang])
  const value = useMemo(() => ({ lang, setLang }), [lang])
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}
