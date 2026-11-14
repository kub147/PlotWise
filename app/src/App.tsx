// App shell: navigation plus the routes. HashRouter, so that it works on GitHub Pages without server configuration.
import { HashRouter, Route, Routes } from 'react-router-dom'
import { LanguageProvider } from '@/components/LanguageProvider'
import { TopBar } from '@/components/TopBar'
import { useAppData } from '@/lib/data'
import { useT } from '@/lib/i18n'
import { useSelectedField } from '@/lib/selection'
import { Changed } from '@/pages/Changed'
import { EmptyPage } from '@/pages/EmptyPage'
import { How } from '@/pages/How'
import { MyField } from '@/pages/MyField'
import { Region } from '@/pages/Region'
import { Replay } from '@/pages/Replay'
import { Season } from '@/pages/Season'

function Shell() {
  const state = useAppData()
  const fields = state.status === 'ready' ? state.data.fields : []
  const [selected, select] = useSelectedField(fields)
  const t = useT()

  return (
    <div className="flex min-h-screen flex-col lg:h-screen">
      <TopBar selected={selected} />
      {/* The navigation floats over the content, so the content gets padding at the top (and at the bottom on a phone). */}
      <main className="pw-scroll min-h-0 flex-1 pb-24 pt-[72px] lg:overflow-y-auto lg:pb-0 lg:pt-[76px]">
        {state.status === 'loading' && <p className="p-6 text-muted-foreground">{t('Loading field data…')}</p>}
        {state.status === 'error' && (
          <p role="alert" className="p-6">
            {t('The field data could not be loaded.')} {state.message}
          </p>
        )}
        {state.status === 'ready' && selected && (
          <Routes>
            <Route path="/" element={<MyField data={state.data} selected={selected} onSelect={select} />} />
            <Route path="/changed" element={<Changed data={state.data} selected={selected} />} />
            <Route path="/replay" element={<Replay data={state.data} selected={selected} />} />
            <Route path="/region" element={<Region selected={selected} />} />
            <Route path="/season" element={<Season data={state.data} selected={selected} />} />
            <Route path="/how" element={<How data={state.data} />} />
            <Route path="*" element={<EmptyPage title={t('Page not found')} />} />
          </Routes>
        )}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <LanguageProvider>
      <HashRouter>
        <Shell />
      </HashRouter>
    </LanguageProvider>
  )
}
