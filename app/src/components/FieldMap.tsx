// Middle of the "My field" view: Leaflet map with the field outlines, a layer switch and a search box.
// The repo has no NDVI or ECOSTRESS raster tiles, so those two layers show a plain base map
// and a note with a button that opens the popup with that view of the selected field (spec 5.1 allows this).
import 'leaflet/dist/leaflet.css'
import { Browser, type LatLngBoundsExpression, type LatLngTuple } from 'leaflet'
import { ArrowUpRight } from 'lucide-react'
import { useEffect, useState } from 'react'
import { CircleMarker, MapContainer, Polygon, TileLayer, Tooltip, ZoomControl, AttributionControl, useMap } from 'react-leaflet'
import { MapSearch, type MapTarget } from '@/components/MapSearch'
import { SegmentedControl } from '@/components/ui/segmented-control'
import { fieldShortName, type County, type FieldFeature } from '@/lib/data'
import type { ViewerTab } from '@/lib/fieldMedia'
import { useT } from '@/lib/i18n'

type LayerId = 'aerial' | 'greenness' | 'heat'

const LAYERS: { value: LayerId; label: string }[] = [
  { value: 'aerial', label: 'Aerial' },
  { value: 'greenness', label: 'Greenness' },
  { value: 'heat', label: 'Surface heat' },
]

// Base maps from public tile services (attribution on the map is required).
const AERIAL_TILES = {
  url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics',
}
const STREET_TILES = {
  url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}

// Note for a layer the map cannot draw yet, the button that opens that view in the popup,
// and the note when the selected field has no such data either.
const LAYER_NOTES: Record<Exclude<LayerId, 'aerial'>, { note: string; action: string; none: string }> = {
  greenness: {
    note: 'Greenness is shown per field, as a chart. Open it for the selected field.',
    action: 'Open the greenness chart',
    none: 'Greenness is shown per field, as a chart, and there is no greenness record for this field.',
  },
  heat: {
    note: 'Surface heat is shown as images of the Tribune area. Open them for the selected field.',
    action: 'Open the heat images',
    none: 'Surface heat is shown as images of the Tribune area. They do not cover this field.',
  },
}

// GeoJSON stores [longitude, latitude]; Leaflet wants [latitude, longitude].
function ringToLatLng(field: FieldFeature): LatLngTuple[] {
  return field.geometry.coordinates[0].map(([lon, lat]) => [lat, lon] as LatLngTuple)
}

// Moves the map to the selected field. The fields lie at three sites more than 200 km apart.
function FlyToField({ field }: { field: FieldFeature }) {
  const map = useMap()
  useEffect(() => {
    const bounds: LatLngBoundsExpression = ringToLatLng(field)
    // On a wide screen the left and right panels cover the map, so the field is aimed at the free middle.
    const wide = window.matchMedia('(min-width: 1024px)').matches
    map.flyToBounds(bounds, {
      paddingTopLeft: wide ? [370, 150] : [60, 80],
      paddingBottomRight: wide ? [480, 60] : [60, 60],
      maxZoom: 14,
      duration: 0.8,
    })
  }, [field, map])
  return null
}

// Moves the map to a county or place picked in the search box.
function FlyToTarget({ target }: { target: MapTarget | null }) {
  const map = useMap()
  useEffect(() => {
    if (target) map.flyTo([target.lat, target.lon], target.zoom, { duration: 0.8 })
  }, [target, map])
  return null
}

type FieldMapProps = {
  fields: FieldFeature[]
  counties: County[]
  selected: FieldFeature
  onSelect: (fieldId: string) => void
  // Whether the selected field has a greenness record and heat images to open.
  viewerHas: { greenness: boolean; heat: boolean }
  onOpenViewer: (tab: ViewerTab) => void
}

export function FieldMap({ fields, counties, selected, onSelect, viewerHas, onOpenViewer }: FieldMapProps) {
  const t = useT()
  const [layer, setLayer] = useState<LayerId>('aerial')
  // County or place found by the search; shown as a pin until a field is picked.
  const [target, setTarget] = useState<MapTarget | null>(null)
  const tiles = layer === 'aerial' ? AERIAL_TILES : STREET_TILES
  // Outlines must be light on the aerial photo and dark on the light base map.
  const outline = layer === 'aerial' ? '#ffffff' : '#2a221c'
  const highlight = layer === 'aerial' ? '#ffd60a' : '#b5179e'
  const note = layer === 'aerial' ? null : LAYER_NOTES[layer]
  const canOpen = layer !== 'aerial' && viewerHas[layer]

  const selectField = (fieldId: string) => {
    setTarget(null)
    if (fieldId === selected.properties.field_id) {
      // Already selected, so FlyToField will not run again: go back to it as a plain target.
      setTarget({ lat: selected.properties.lat, lon: selected.properties.lon, zoom: 14, label: '' })
    }
    onSelect(fieldId)
  }

  return (
    <div className="pw-map-bleed relative h-[340px] overflow-hidden rounded-[28px] bg-map-frame shadow-soft lg:h-full lg:rounded-none lg:shadow-none">
      <MapContainer
        attributionControl={false}
        center={[selected.properties.lat, selected.properties.lon]}
        zoom={13}
        zoomControl={false}
        scrollWheelZoom
        // On a phone one finger scrolls the page; the map moves and zooms with two fingers or the buttons.
        dragging={!Browser.mobile}
        className="h-full w-full"
      >
        <TileLayer key={layer} url={tiles.url} attribution={tiles.attribution} maxZoom={18} />
        <ZoomControl position="bottomright" zoomInTitle={t('Zoom in')} zoomOutTitle={t('Zoom out')} />
        <AttributionControl position="bottomright" prefix="Leaflet" />
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
              eventHandlers={{ click: () => selectField(field.properties.field_id) }}
            >
              <Tooltip sticky>
                {fieldShortName(field.properties)}, {t(field.properties.current_rotation)}
              </Tooltip>
            </Polygon>
          )
        })}
        {target && target.label !== '' && (
          <CircleMarker
            key={`${target.lat}-${target.lon}-${layer}`}
            center={[target.lat, target.lon]}
            radius={9}
            pathOptions={{ color: '#ffffff', weight: 3, fillColor: '#b5179e', fillOpacity: 1 }}
          >
            <Tooltip permanent direction="top" offset={[0, -10]}>
              {target.label}
            </Tooltip>
          </CircleMarker>
        )}
        <FlyToField field={selected} />
        <FlyToTarget target={target} />
      </MapContainer>

      {/* Search and layer switch over the map (z-index above the Leaflet layers) */}
      <div className="absolute inset-x-3 top-3 z-[1000] flex flex-col gap-2 lg:left-[336px] lg:right-[412px] lg:top-[88px] xl:right-[452px]">
        <MapSearch
          fields={fields}
          counties={counties}
          onSelectField={selectField}
          onGoTo={setTarget}
          className="z-20 w-full max-w-[420px]"
        />
        <div className="max-w-full self-start">
          <SegmentedControl
            label={t('Map layer')}
            options={LAYERS.map((option) => ({ ...option, label: t(option.label) }))}
            value={layer}
            onValueChange={setLayer}
            tone="glass"
          />
        </div>
      </div>

      {note && layer !== 'aerial' && (
        <div
          role="status"
          className="pw-glass absolute bottom-3 left-3 z-[1000] flex max-w-[min(26rem,calc(100%-5rem))] flex-col items-start gap-2.5 rounded-2xl px-4 py-3 text-[13px] text-foreground lg:bottom-4 lg:left-[336px]"
        >
          <p>{t(canOpen ? note.note : note.none)}</p>
          {canOpen && (
            <button
              type="button"
              onClick={() => onOpenViewer(layer)}
              className="pw-press pw-brand inline-flex min-h-10 items-center gap-1.5 rounded-full px-4 text-[13px] font-medium"
            >
              {t(note.action)}
              <ArrowUpRight aria-hidden className="h-4 w-4" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
