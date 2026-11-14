// Search box over the map. It looks in three places:
// 1. the demo fields (name, site, rotation) and 2. the 46 counties, both from the files already loaded;
// 3. any place on the map by name, through the public OpenStreetMap search service (Nominatim).
// Picking a field selects it; picking a county or a place moves the map there.
import { Loader2, MapPin, Search, Sprout, X } from 'lucide-react'
import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { fieldShortName, type County, type FieldFeature } from '@/lib/data'
import { useLang, useT } from '@/lib/i18n'
import { cn } from '@/lib/utils'

export type MapTarget = { lat: number; lon: number; zoom: number; label: string }

type Result =
  | { kind: 'field'; key: string; title: string; detail: string; fieldId: string }
  | { kind: 'place'; key: string; title: string; detail: string; target: MapTarget }

type NominatimHit = { place_id: number; display_name: string; lat: string; lon: string }

const PLACE_SEARCH_URL = 'https://nominatim.openstreetmap.org/search'
// The service asks for at most one request a second; we wait until typing pauses.
const TYPING_PAUSE_MS = 600

type MapSearchProps = {
  fields: FieldFeature[]
  counties: County[]
  onSelectField: (fieldId: string) => void
  onGoTo: (target: MapTarget) => void
  className?: string
}

export function MapSearch({ fields, counties, onSelectField, onGoTo, className }: MapSearchProps) {
  const t = useT()
  const { lang } = useLang()
  const inputId = useId()
  const listId = useId()
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  // Places found by the online search, kept with the query they belong to.
  const [places, setPlaces] = useState<{ query: string; results: Result[]; failed: boolean } | null>(null)
  const box = useRef<HTMLDivElement>(null)

  const needle = query.trim().toLowerCase()

  // Fields and counties: matched in the browser, instantly.
  const local = useMemo<Result[]>(() => {
    if (needle.length < 2) return []
    const fieldResults: Result[] = fields
      .filter((field) => {
        const p = field.properties
        return [fieldShortName(p), p.name, p.site, p.field_id, p.current_rotation]
          .join(' ')
          .toLowerCase()
          .includes(needle)
      })
      .map((field) => ({
        kind: 'field',
        key: `field-${field.properties.field_id}`,
        title: fieldShortName(field.properties),
        detail: t(field.properties.name),
        fieldId: field.properties.field_id,
      }))
    const countyResults: Result[] = counties
      .filter((county) => county.name.toLowerCase().includes(needle))
      .slice(0, 5)
      .map((county) => ({
        kind: 'place',
        key: `county-${county.fips}`,
        title: t('{name} County, Kansas', { name: county.name }),
        detail: t('County'),
        target: { lat: county.lat, lon: county.lon, zoom: 10, label: t('{name} County', { name: county.name }) },
      }))
    return [...fieldResults, ...countyResults]
  }, [needle, fields, counties, t])

  // Places anywhere on the map: asked online once typing pauses.
  useEffect(() => {
    if (needle.length < 3) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams({ format: 'jsonv2', limit: '5', q: needle, 'accept-language': lang })
      fetch(`${PLACE_SEARCH_URL}?${params.toString()}`, { signal: controller.signal })
        .then((response) => {
          if (!response.ok) throw new Error(String(response.status))
          return response.json() as Promise<NominatimHit[]>
        })
        .then((hits) => {
          const results: Result[] = hits.map((hit) => {
            const [name, ...rest] = hit.display_name.split(', ')
            return {
              kind: 'place',
              key: `place-${hit.place_id}`,
              title: name,
              detail: rest.join(', '),
              target: { lat: Number(hit.lat), lon: Number(hit.lon), zoom: 12, label: name },
            }
          })
          setPlaces({ query: needle, results, failed: false })
        })
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === 'AbortError') return
          setPlaces({ query: needle, results: [], failed: true })
        })
    }, TYPING_PAUSE_MS)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [needle, lang])

  // Close the list when the pointer goes elsewhere.
  useEffect(() => {
    const onPointerDown = (event: PointerEvent) => {
      if (box.current && !box.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [])

  const placesReady = places !== null && places.query === needle
  const searchingPlaces = needle.length >= 3 && !placesReady
  const results = [...local, ...(placesReady ? places.results : [])]
  const showList = open && needle.length >= 2
  const activeIndex = Math.min(active, Math.max(results.length - 1, 0))

  const pick = (result: Result) => {
    if (result.kind === 'field') onSelectField(result.fieldId)
    else onGoTo(result.target)
    setQuery(result.title)
    setOpen(false)
  }

  return (
    <div ref={box} className={cn('relative', className)}>
      <label htmlFor={inputId} className="sr-only">
        {t('Search the map')}
      </label>
      <div className="pw-glass flex min-h-12 items-center gap-2 rounded-full pl-4 pr-1.5">
        <Search aria-hidden className="h-5 w-5 shrink-0 text-muted-foreground" />
        <input
          id={inputId}
          type="search"
          role="combobox"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={showList && results[activeIndex] ? `${listId}-${activeIndex}` : undefined}
          autoComplete="off"
          value={query}
          placeholder={t('Search a field, county or place')}
          onChange={(event) => {
            setQuery(event.target.value)
            setActive(0)
            setOpen(true)
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={(event) => {
            if (event.key === 'ArrowDown') {
              event.preventDefault()
              setOpen(true)
              setActive(Math.min(activeIndex + 1, results.length - 1))
            } else if (event.key === 'ArrowUp') {
              event.preventDefault()
              setActive(Math.max(activeIndex - 1, 0))
            } else if (event.key === 'Enter' && showList && results[activeIndex]) {
              event.preventDefault()
              pick(results[activeIndex])
            } else if (event.key === 'Escape') {
              setOpen(false)
            }
          }}
          className="min-h-11 min-w-0 flex-1 bg-transparent text-[15px] outline-none placeholder:text-muted-foreground [&::-webkit-search-cancel-button]:hidden"
        />
        {searchingPlaces && <Loader2 aria-hidden className="h-5 w-5 shrink-0 animate-spin text-muted-foreground" />}
        {query !== '' && (
          <button
            type="button"
            aria-label={t('Clear the search')}
            onClick={() => {
              setQuery('')
              setOpen(false)
            }}
            className="pw-press flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-foreground/5 hover:text-foreground"
          >
            <X aria-hidden className="h-5 w-5" />
          </button>
        )}
      </div>

      {showList && (
        <div className="pw-sheet pw-scroll absolute inset-x-0 top-[calc(100%+6px)] max-h-[320px] overflow-y-auto rounded-3xl p-1.5 shadow-lift">
          <ul id={listId} role="listbox" aria-label={t('Search results')}>
            {results.map((result, index) => (
              <li
                key={result.key}
                id={`${listId}-${index}`}
                role="option"
                aria-selected={index === activeIndex}
                onPointerEnter={() => setActive(index)}
                onClick={() => pick(result)}
                className={cn(
                  'flex min-h-11 cursor-pointer items-center gap-3 rounded-2xl px-3 py-2',
                  index === activeIndex && 'bg-foreground/[0.06]',
                )}
              >
                {result.kind === 'field' ? (
                  <Sprout aria-hidden className="h-5 w-5 shrink-0 text-leaf" />
                ) : (
                  <MapPin aria-hidden className="h-5 w-5 shrink-0 text-muted-foreground" />
                )}
                <span className="min-w-0">
                  <span className="block truncate text-[15px] font-medium">{result.title}</span>
                  <span className="block truncate text-[13px] text-muted-foreground">{result.detail}</span>
                </span>
              </li>
            ))}
          </ul>
          <p role="status" className="px-3 py-2 text-[13px] text-muted-foreground">
            {searchingPlaces && t('Looking for places…')}
            {!searchingPlaces && results.length === 0 && needle.length >= 3 && t('Nothing found.')}
            {!searchingPlaces && results.length === 0 && needle.length < 3 && t('Type at least 3 letters to search places.')}
            {placesReady && places.failed && ` ${t('The place search is not reachable right now; fields and counties still work.')}`}
            {placesReady && !places.failed && places.results.length > 0 && t('Places: © OpenStreetMap contributors')}
          </p>
        </div>
      )}
    </div>
  )
}
