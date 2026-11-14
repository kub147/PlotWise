// Rejestr dowodów z crops-economics/reference/evidence.md.
// Czytamy plik w przeglądarce, żeby opisy E01… i zdanie o ubezpieczeniach nie były przepisane ręcznie.
import { useEffect, useState } from 'react'
import { dataUrl } from '@/lib/data'

export type EvidenceItem = { id: string; finding: string; source: string; status: string }
export type Evidence = {
  items: Record<string, EvidenceItem>
  // Zdanie o ubezpieczeniach na każdą kartę (odpowiedź 5 w evidence.md); null, gdy nie znaleziono.
  insuranceSentence: string | null
}

export function parseEvidence(markdown: string): Evidence {
  const items: Record<string, EvidenceItem> = {}
  for (const line of markdown.split('\n')) {
    // Wiersz tabeli: | E07 | finding | source | status |
    const cells = line.split('|').map((cell) => cell.trim())
    if (cells.length >= 6 && /^E\d+$/.test(cells[1])) {
      items[cells[1]] = { id: cells[1], finding: cells[2], source: cells[3], status: cells[4] }
    }
  }
  const insurance = /one sentence for the cards:\*\*\s*"([^"]+)"/.exec(markdown)
  return { items, insuranceSentence: insurance ? insurance[1] : null }
}

// Plik jest wspólny dla wszystkich pól, więc pobieramy go raz.
let cache: Promise<Evidence> | null = null

function loadEvidence(): Promise<Evidence> {
  cache ??= fetch(dataUrl('evidence.md'))
    .then((response) => {
      if (!response.ok) throw new Error(`Could not load evidence.md (${response.status})`)
      return response.text()
    })
    .then(parseEvidence)
  return cache
}

export function useEvidence(): Evidence | null {
  const [evidence, setEvidence] = useState<Evidence | null>(null)
  useEffect(() => {
    let cancelled = false
    loadEvidence()
      .then((loaded) => {
        if (!cancelled) setEvidence(loaded)
      })
      .catch(() => {
        // Bez rejestru karta pokaże same identyfikatory; nie zmyślamy opisów.
        if (!cancelled) setEvidence({ items: {}, insuranceSentence: null })
      })
    return () => {
      cancelled = true
    }
  }, [])
  return evidence
}
