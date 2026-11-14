// Szkielet aplikacji: górny pasek + pięć tras. HashRouter, żeby działało na GitHub Pages bez konfiguracji serwera.
import { HashRouter, Route, Routes } from 'react-router-dom'
import { TopBar } from '@/components/TopBar'
import { useAppData } from '@/lib/data'
import { useSelectedField } from '@/lib/selection'
import { EmptyPage } from '@/pages/EmptyPage'
import { MyField } from '@/pages/MyField'
import { Region } from '@/pages/Region'
import { Replay } from '@/pages/Replay'

function Shell() {
  const state = useAppData()
  const fields = state.status === 'ready' ? state.data.fields : []
  const [selected, select] = useSelectedField(fields)

  return (
    <div className="flex min-h-screen flex-col lg:h-screen">
      <TopBar selected={selected} />
      {/* Nawigacja jest przyklejona nad treścią, więc treść dostaje odstęp u góry (i na telefonie u dołu). */}
      <main className="pw-scroll min-h-0 flex-1 pb-24 pt-[72px] lg:overflow-y-auto lg:pb-0 lg:pt-[76px]">
        {state.status === 'loading' && <p className="p-6 text-muted-foreground">Loading field data…</p>}
        {state.status === 'error' && (
          <p role="alert" className="p-6">
            The field data could not be loaded. {state.message}
          </p>
        )}
        {state.status === 'ready' && selected && (
          <Routes>
            <Route path="/" element={<MyField data={state.data} selected={selected} onSelect={select} />} />
            <Route path="/changed" element={<EmptyPage title="What has changed" />} />
            <Route path="/replay" element={<Replay data={state.data} selected={selected} />} />
            <Route path="/region" element={<Region selected={selected} />} />
            <Route path="/season" element={<EmptyPage title="This season" />} />
            <Route path="/how" element={<EmptyPage title="How we know" />} />
            <Route path="*" element={<EmptyPage title="Page not found" />} />
          </Routes>
        )}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <HashRouter>
      <Shell />
    </HashRouter>
  )
}
