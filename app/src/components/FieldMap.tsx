// Środkowa kolumna widoku „My field": mapa Leaflet z granicami pól i przełącznikiem warstw.
// W repo nie ma kafli rastrowych NDVI ani ECOSTRESS, więc te dwie warstwy pokazują zwykły podkład
// i informację, gdzie szukać obrazów (specyfikacja 5.1 dopuszcza takie rozwiązanie).
import 'leaflet/dist/leaflet.css'
import type { LatLngBoundsExpression, LatLngTuple } from 'leaflet'
import { useEffect, useState } from 'react'
import { MapContainer, Polygon, TileLayer, Tooltip, ZoomControl, useMap } from 'react-leaflet'
import { SegmentedControl } from '@/components/ui/segmented-control'
import { fieldShortName, type FieldFeature } from '@/lib/data'

type LayerId = 'aerial' | 'greenness' | 'heat'

const LAYERS: { value: LayerId; label: string }[] = [
  { value: 'aerial', label: 'Aerial' },
  { value: 'greenness', label: 'Greenness' },
  { value: 'heat', label: 'Surface heat' },
]

// Podkłady z publicznych serwisów kafli (wymagają podania źródła na mapie).
const AERIAL_TILES = {
  url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics',
}
const STREET_TILES = {
  url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}

const LAYER_NOTES: Record<LayerId, string | null> = {
  aerial: null,
  greenness: 'Greenness is not on the map yet. The field card shows how green this field was over the years.',
  heat: 'Surface heat is not on the map yet. The field card shows the heat images where we have them.',
}

// GeoJSON zapisuje [długość, szerokość]; Leaflet chce [szerokość, długość].
function ringToLatLng(field: FieldFeature): LatLngTuple[] {
  return field.geometry.coordinates[0].map(([lon, lat]) => [lat, lon] as LatLngTuple)
}

// Przesuwa mapę do wybranego pola. Pola leżą w trzech miejscowościach oddalonych o ponad 200 km.
function FlyToField({ field }: { field: FieldFeature }) {
  const map = useMap()
  useEffect(() => {
    const bounds: LatLngBoundsExpression = ringToLatLng(field)
    map.flyToBounds(bounds, { padding: [80, 80], maxZoom: 14, duration: 0.8 })
  }, [field, map])
  return null
}

type FieldMapProps = {
  fields: FieldFeature[]
  selected: FieldFeature
  onSelect: (fieldId: string) => void
}

export function FieldMap({ fields, selected, onSelect }: FieldMapProps) {
  const [layer, setLayer] = useState<LayerId>('aerial')
  const tiles = layer === 'aerial' ? AERIAL_TILES : STREET_TILES
  // Na zdjęciu lotniczym obrysy muszą być jasne, na jasnym podkładzie ciemne.
  const outline = layer === 'aerial' ? '#ffffff' : '#0e1a24'
  const highlight = layer === 'aerial' ? '#ffd43b' : '#b5179e'
  const note = LAYER_NOTES[layer]

  return (
    <div className="relative h-[440px] overflow-hidden rounded-lg border border-map-frame bg-map-frame lg:h-full">
      <MapContainer
        center={[selected.properties.lat, selected.properties.lon]}
        zoom={13}
        zoomControl={false}
        scrollWheelZoom
        className="h-full w-full"
      >
        <TileLayer key={layer} url={tiles.url} attribution={tiles.attribution} maxZoom={18} />
        <ZoomControl position="bottomright" />
        {fields.map((field) => {
          const isSelected = field.properties.field_id === selected.properties.field_id
          return (
            <Polygon
              key={`${field.properties.field_id}-${layer}-${isSelected}`}
              positions={ringToLatLng(field)}
              pathOptions={{
                color: isSelected ? highlight : outline,
                weight: isSelected ? 4 : 2,
                fillColor: isSelected ? highlight : outline,
                fillOpacity: isSelected ? 0.12 : 0.04,
              }}
              eventHandlers={{ click: () => onSelect(field.properties.field_id) }}
            >
              <Tooltip sticky>
                {fieldShortName(field.properties)} · {field.properties.current_rotation}
              </Tooltip>
            </Polygon>
          )
        })}
        <FlyToField field={selected} />
      </MapContainer>

      {/* Przełącznik warstw nad mapą (z-index powyżej warstw Leaflet) */}
      <div className="absolute left-3 top-3 z-[1000] max-w-[calc(100%-1.5rem)] overflow-x-auto rounded-md shadow-md">
        <SegmentedControl label="Map layer" options={LAYERS} value={layer} onValueChange={setLayer} />
      </div>

      {note && (
        <p
          role="status"
          className="absolute bottom-3 left-3 z-[1000] max-w-[min(26rem,calc(100%-5rem))] rounded-md border border-border bg-card px-3 py-2 text-[13px] text-foreground shadow-md"
        >
          {note}
        </p>
      )}
    </div>
  )
}
