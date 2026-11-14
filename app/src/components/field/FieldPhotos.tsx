// Dwa obrazy w karcie pola: zdjęcie lotnicze (NAIP) i mapa temperatury powierzchni (ECOSTRESS).
// Gdy obrazu dla pola nie ma w repo, mówimy to wprost zamiast pokazywać cokolwiek zastępczego.
import { useState } from 'react'
import { imageUrl, type HeatScene, type HeatSummary } from '@/lib/fieldMedia'
import { cToF, formatNumber } from '@/lib/units'

function Missing({ children }: { children: string }) {
  return (
    <div className="flex aspect-square items-center justify-center rounded-md border border-dashed border-input bg-muted px-3 text-center text-[13px] text-muted-foreground">
      {children}
    </div>
  )
}

// Miniatura z linkiem do pełnego obrazu w nowej karcie.
function Thumbnail({ file, alt }: { file: string; alt: string }) {
  return (
    <a href={imageUrl(file)} target="_blank" rel="noreferrer" className="block overflow-hidden rounded-md border border-border">
      <img src={imageUrl(file)} alt={alt} loading="lazy" className="aspect-square w-full object-cover" />
    </a>
  )
}

// "2023-07-30 20:08" -> "Jul 30, 2023"
function sceneDate(scene: HeatScene) {
  const date = new Date(`${scene.time_utc.slice(0, 10)}T00:00:00Z`)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' })
}

// "13:20" -> "1:20 pm"
function clockTime(time: string) {
  const [hour, minute] = time.split(':').map(Number)
  return `${((hour + 11) % 12) + 1}:${String(minute).padStart(2, '0')} ${hour < 12 ? 'am' : 'pm'}`
}

const fahrenheit = (celsius: number) => `${formatNumber(cToF(celsius))}°F`

type FieldPhotosProps = {
  fieldId: string
  fieldLabel: string
  hasAerial: boolean
  heat: HeatSummary | null
}

export function FieldPhotos({ fieldId, fieldLabel, hasAerial, heat }: FieldPhotosProps) {
  // Sceny, na których jest to pole, od najnowszej.
  const scenes = (heat?.scenes ?? [])
    .filter((scene) => fieldId in scene.fields)
    .sort((a, b) => b.time_utc.localeCompare(a.time_utc))
  const [sceneId, setSceneId] = useState<string | null>(null)
  const scene = scenes.find((candidate) => candidate.scene === sceneId) ?? scenes[0]
  const onField = scene?.fields[fieldId]
  const selectId = `heat-scene-${fieldId}`

  return (
    <div>
      <div className="grid grid-cols-2 gap-3">
        <figure>
          {hasAerial ? (
            <Thumbnail file={`field_${fieldId}_naip.png`} alt={`Aerial photo of ${fieldLabel}`} />
          ) : (
            <Missing>No aerial photo for this field yet.</Missing>
          )}
          <figcaption className="mt-1.5 text-[13px] text-muted-foreground">Aerial photo (USDA NAIP)</figcaption>
        </figure>
        <figure>
          {scene ? (
            <Thumbnail
              file={scene.image.split('/').pop() ?? scene.image}
              alt={`Surface heat map of the area around Tribune on ${sceneDate(scene)}; blue is cooler, red is hotter`}
            />
          ) : (
            <Missing>No surface heat image for this field yet.</Missing>
          )}
          <figcaption className="mt-1.5 text-[13px] text-muted-foreground">Surface heat (NASA ECOSTRESS)</figcaption>
        </figure>
      </div>

      {scene && onField && (
        <div className="mt-3">
          <label htmlFor={selectId} className="text-[13px] font-semibold">
            Heat image from
          </label>
          <select
            id={selectId}
            value={scene.scene}
            onChange={(event) => setSceneId(event.target.value)}
            className="mt-1 block min-h-11 w-full rounded-md border border-input bg-card px-3 text-[15px]"
          >
            {scenes.map((option) => (
              <option key={option.scene} value={option.scene}>
                {sceneDate(option)}, around {clockTime(option.local_solar_time)} sun time
              </option>
            ))}
          </select>

          <p className="mt-3 text-[15px] leading-snug">
            At that moment the ground on this field was{' '}
            <span className="font-mono font-semibold">{fahrenheit(onField.lst_c)}</span>, with {onField.crop} on it.
          </p>
          <p className="mt-2 text-[13px] text-muted-foreground">Average for the whole area at that moment:</p>
          <ul className="mt-1 grid grid-cols-2 gap-x-4 gap-y-0.5 text-[13px]">
            {Object.entries(scene.by_crop_class).map(([crop, value]) => (
              <li key={crop} className="flex justify-between gap-2">
                {/* Klucz bywa długi: "winter wheat (ripe in June, stubble from July)" -> sama nazwa uprawy */}
                <span className="capitalize">{crop.split(' (')[0]}</span>
                <span className="font-mono font-medium">{fahrenheit(value.mean_c)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-[13px] leading-snug text-muted-foreground">
            On the map blue is cooler (about {fahrenheit(scene.colour_scale_c[0])}) and red is hotter (about{' '}
            {fahrenheit(scene.colour_scale_c[1])}); black outlines are the demo fields. This is the temperature of the
            ground surface, not of the air, at one moment in the day.
          </p>
        </div>
      )}
    </div>
  )
}
