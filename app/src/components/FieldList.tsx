// Lewa kolumna widoku „My field": lista pól demo pogrupowana według miejscowości.
import { CropTile } from '@/components/CropTile'
import { fieldShortName, type AppData, type FieldFeature } from '@/lib/data'
import { rotationPhases } from '@/lib/rotation'
import { cn } from '@/lib/utils'

type FieldListProps = {
  data: AppData
  selectedId: string
  onSelect: (fieldId: string) => void
}

export function FieldList({ data, selectedId, onSelect }: FieldListProps) {
  // Grupy w kolejności, w jakiej miejscowości pojawiają się w pliku (Tribune, Colby, Hays).
  const groups = new Map<string, FieldFeature[]>()
  for (const field of data.fields) {
    const site = field.properties.site
    groups.set(site, [...(groups.get(site) ?? []), field])
  }

  return (
    <nav aria-label="Demo fields" className="flex flex-col gap-5">
      <div>
        <h2 className="text-[19px] font-semibold">Demo fields</h2>
        <p className="mt-1 text-[13px] text-muted-foreground">
          {data.fields.length} dryland fields at {groups.size} sites in western Kansas.
        </p>
      </div>

      {[...groups.entries()].map(([site, fields]) => {
        const county = data.countyNames[fields[0].properties.county_fips]
        return (
          <section key={site} aria-labelledby={`site-${site}`}>
            <h3
              id={`site-${site}`}
              className="mb-2 flex items-baseline justify-between gap-2 border-b border-border pb-1.5 font-sans text-[13px] font-semibold uppercase tracking-[0.06em] text-muted-foreground"
            >
              <span>{site}</span>
              {county && <span className="font-medium normal-case tracking-normal">{county} County</span>}
            </h3>
            <ul className="flex flex-col gap-1.5">
              {fields.map((field) => {
                const p = field.properties
                const selected = p.field_id === selectedId
                const phases = rotationPhases(p.current_rotation)
                const hasReplay = data.manifest.results.includes(p.field_id)
                return (
                  <li key={p.field_id}>
                    <button
                      type="button"
                      aria-pressed={selected}
                      onClick={() => onSelect(p.field_id)}
                      className={cn(
                        'flex w-full flex-col gap-1.5 rounded-md border px-3 py-2.5 text-left transition-colors',
                        selected
                          ? 'border-foreground bg-card ring-1 ring-foreground'
                          : 'border-transparent hover:border-border hover:bg-card',
                      )}
                    >
                      <span className="flex items-center justify-between gap-2">
                        <span className="font-mono text-[15px] font-semibold">{fieldShortName(p)}</span>
                        {phases ? (
                          <span className="flex gap-0.5" aria-label={`Rotation ${phases.join('-')}`}>
                            {phases.map((letter, i) => (
                              <CropTile key={i} letter={letter} className="h-6 w-6 text-[13px]" />
                            ))}
                          </span>
                        ) : (
                          <span className="rounded-sm border border-input px-1.5 py-0.5 text-[13px] font-medium">
                            No fallow
                          </span>
                        )}
                      </span>
                      <span className="text-[13px] leading-snug text-muted-foreground">{p.name}</span>
                      {!hasReplay && (
                        <span className="text-[13px] font-medium text-muted-foreground">Replay not ready yet</span>
                      )}
                    </button>
                  </li>
                )
              })}
            </ul>
          </section>
        )
      })}
    </nav>
  )
}
