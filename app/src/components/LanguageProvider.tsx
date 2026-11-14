// Holds the interface language, remembers it in the browser and sets <html lang> for screen readers.
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { LanguageContext, readStoredLang, storeLang, type Lang } from '@/lib/i18n'

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(readStoredLang)
  useEffect(() => {
    document.documentElement.lang = lang
    storeLang(lang)
  }, [lang])
  const value = useMemo(() => ({ lang, setLang }), [lang])
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}
