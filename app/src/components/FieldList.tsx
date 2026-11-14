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
        <h2 className="text-[21px] font-semibold">Demo fields</h2>
        <p className="mt-1 text-[13px] text-muted-foreground">
          {data.fields.length} dryland fields at {groups.size} sites in western Kansas.
        </p>
      </div>

      {/* Phone: a drop-down instead of the long list, so the map and the field card are one swipe away */}
      <div className="lg:hidden">
        <label htmlFor="field-select" className="sr-only">
          Choose a field
        </label>
        <select
          id="field-select"
          value={selectedId}
          onChange={(event) => onSelect(event.target.value)}
          className="block min-h-12 w-full rounded-2xl border border-input bg-card px-3 text-[16px] font-medium"
        >
          {[...groups.entries()].map(([site, fields]) => (
            <optgroup key={site} label={site}>
              {fields.map((field) => (
                <option key={field.properties.field_id} value={field.properties.field_id}>
                  {fieldShortName(field.properties)} · {field.properties.current_rotation}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      {[...groups.entries()].map(([site, fields]) => {
        const county = data.countyNames[fields[0].properties.county_fips]
        return (
          <section key={site} aria-labelledby={`site-${site}`} className="hidden lg:block">
            <h3
              id={`site-${site}`}
              className="mb-1.5 flex items-baseline justify-between gap-2 px-3 text-[15px] font-semibold"
            >
              <span>{site}</span>
              {county && <span className="text-[13px] font-normal tracking-normal text-muted-foreground">{county} County</span>}
            </h3>
            <ul className="flex flex-col gap-1">
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
                        'pw-press flex w-full flex-col gap-1.5 rounded-[20px] px-3 py-3 text-left',
                        selected ? 'bg-card shadow-soft ring-2 ring-leaf' : 'hover:bg-card/60',
                      )}
                    >
                      <span className="flex items-center justify-between gap-2">
                        <span className="font-mono text-[15px] font-medium">{fieldShortName(p)}</span>
                        {phases ? (
                          <span className="flex gap-0.5" aria-label={`Rotation ${phases.join('-')}`}>
                            {phases.map((letter, i) => (
                              <CropTile key={i} letter={letter} className="h-6 w-6 text-[13px]" />
                            ))}
                          </span>
                        ) : (
                          <span className="rounded-full bg-foreground/[0.06] px-2.5 py-0.5 text-[13px]">
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
