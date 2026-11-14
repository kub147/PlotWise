// Evidence register from crops-economics/reference/evidence.md.
// The file is read in the browser so that the E01… entries and the insurance sentence are not retyped by hand.
import { useEffect, useState } from 'react'
import { dataUrl } from '@/lib/data'

export type EvidenceItem = { id: string; finding: string; source: string; status: string }
export type Evidence = {
  items: Record<string, EvidenceItem>
  // Insurance sentence for every card (answer 5 in evidence.md); null when not found.
  insuranceSentence: string | null
}

export function parseEvidence(markdown: string): Evidence {
  const items: Record<string, EvidenceItem> = {}
  for (const line of markdown.split('\n')) {
    // Table row: | E07 | finding | source | status |
    const cells = line.split('|').map((cell) => cell.trim())
    if (cells.length >= 6 && /^E\d+$/.test(cells[1])) {
      items[cells[1]] = { id: cells[1], finding: cells[2], source: cells[3], status: cells[4] }
    }
  }
  const insurance = /one sentence for the cards:\*\*\s*"([^"]+)"/.exec(markdown)
  return { items, insuranceSentence: insurance ? insurance[1] : null }
}

// The file is shared by all fields, so it is fetched once.
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
        // Without the register the card shows the IDs only; we do not make up descriptions.
        if (!cancelled) setEvidence({ items: {}, insuranceSentence: null })
      })
    return () => {
      cancelled = true
    }
  }, [])
  return evidence
}
