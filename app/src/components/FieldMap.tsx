// Middle of the "My field" view: Leaflet map with the field outlines, a layer switch and a search box.
// The Greenness and Surface heat layers lay one image per site over a plain base map: mean summer greenness
// (Landsat NDVI) and the newest ECOSTRESS surface temperature scene. A legend names the colours and has a button
// that opens the popup with that view of the selected field (the chart over the years, the other heat days).
import 'leaflet/dist/leaflet.css'
import { Browser, type LatLngBoundsExpression, type LatLngTuple } from 'leaflet'
import { ArrowUpRight } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import {
  AttributionControl,
  CircleMarker,
  ImageOverlay,
  MapContainer,
  Pane,
  Polygon,
  TileLayer,
  Tooltip,
  ZoomControl,
  useMap,
} from 'react-leaflet'
import { MapSearch, type MapTarget } from '@/components/MapSearch'
import { SegmentedControl } from '@/components/ui/segmented-control'
import { fieldShortName, type County, type FieldFeature } from '@/lib/data'
import {
  clockTime,
  HEAT_SCALE,
  imageUrl,
  latestHeatScenes,
  sceneDate,
  useGreennessMap,
  type HeatSummary,
  type ImageBounds,
  type ViewerTab,
} from '@/lib/fieldMedia'
import { useDateLocale, useT, useTempUnit } from '@/lib/i18n'
import { formatTemp } from '@/lib/units'

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

// Button of a layer's legend (it opens that view of the selected field in the popup)
// and the note when there is no image for the area of the selected field.
const LAYER_NOTES: Record<Exclude<LayerId, 'aerial'>, { action: string; none: string }> = {
  greenness: { action: 'Open the greenness chart', none: 'No greenness record for this field yet.' },
  heat: { action: 'Open the heat images', none: 'No surface heat image for this field yet.' },
}

// Image bounds are west, south, east, north; Leaflet wants [[south, west], [north, east]].
function toLatLngBounds([west, south, east, north]: ImageBounds): LatLngBoundsExpression {
  return [
    [south, west],
    [north, east],
  ]
}

// Colour scale of a map layer: the gradient with a label at each end.
function ScaleBar({ low, high, gradient, numbers }: { low: string; high: string; gradient: string; numbers?: boolean }) {
  const end = numbers ? 'font-mono font-medium' : 'text-muted-foreground'
  return (
    <div className="flex w-full items-center gap-2.5">
      <span className={end}>{low}</span>
      <span aria-hidden className="h-2.5 min-w-10 flex-1 rounded-full" style={{ background: gradient }} />
      <span className={end}>{high}</span>
    </div>
  )
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
  // ECOSTRESS scenes of all sites; the surface heat layer shows the newest one of each site.
  heat: HeatSummary | null
  // Whether the selected field has a greenness record and heat images to open.
  viewerHas: { greenness: boolean; heat: boolean }
  onOpenViewer: (tab: ViewerTab) => void
}

export function FieldMap({ fields, counties, selected, onSelect, heat, viewerHas, onOpenViewer }: FieldMapProps) {
  const t = useT()
  const unit = useTempUnit()
  const locale = useDateLocale()
  const [layer, setLayer] = useState<LayerId>('aerial')
  // County or place found by the search; shown as a pin until a field is picked.
  const [target, setTarget] = useState<MapTarget | null>(null)
  const tiles = layer === 'aerial' ? AERIAL_TILES : STREET_TILES
  // Outlines must be light on the aerial photo and dark on the light base map.
  const outline = layer === 'aerial' ? '#ffffff' : '#2a221c'
  const highlight = layer === 'aerial' ? '#ffd60a' : '#b5179e'
  const canOpen = layer !== 'aerial' && viewerHas[layer]
  // Images of the two data layers: one per site. The legend describes the image around the selected field.
  const site = selected.properties.site
  const greenness = useGreennessMap()
  const heatScenes = useMemo(() => latestHeatScenes(heat), [heat])
  const heatScene = heatScenes.find((scene) => scene.site === site)
  const greennessHere = greenness?.sites.some((image) => image.site === site) ?? false
  const overlays =
    layer === 'heat'
      ? heatScenes.map((scene) => ({ file: scene.image, bounds: scene.bounds }))
      : layer === 'greenness'
        ? (greenness?.sites ?? []).map((image) => ({ file: image.image, bounds: image.bounds }))
        : []

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
        {/* Above the base map, below the field outlines (Leaflet's overlay pane is at 400) */}
        <Pane name="layer-images" style={{ zIndex: 350 }}>
          {overlays.map((overlay) => (
            <ImageOverlay
              key={overlay.file}
              url={imageUrl(overlay.file.split('/').pop() ?? overlay.file)}
              bounds={toLatLngBounds(overlay.bounds)}
            />
          ))}
        </Pane>
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

      {layer !== 'aerial' && (
        <div
          role="status"
          className="pw-glass absolute bottom-3 left-3 z-[1000] flex w-[min(24rem,calc(100%-5rem))] flex-col items-start gap-2 rounded-2xl px-4 py-3 text-[13px] text-foreground lg:bottom-4 lg:left-[336px]"
        >
          {layer === 'heat' && heatScene && (
            <>
              <div>
                <p className="font-semibold">{t('Ground temperature around {site}', { site })}</p>
                <p className="text-muted-foreground">
                  {t('{date}, around {time} local solar time', {
                    date: sceneDate(heatScene, locale),
                    time: clockTime(heatScene.local_solar_time, locale),
                  })}
                </p>
              </div>
              <ScaleBar
                low={formatTemp(heatScene.colour_scale_c[0], unit)}
                high={formatTemp(heatScene.colour_scale_c[1], unit)}
                gradient={HEAT_SCALE}
                numbers
              />
              {/* The explanation is left out on a phone, where the map is small */}
              <p className="hidden text-muted-foreground sm:block">
                {t('Temperature of the ground surface, not of the air, at one moment of that day. Measured by NASA’s ECOSTRESS instrument.')}
              </p>
            </>
          )}
          {layer === 'greenness' && greenness && greennessHere && (
            <>
              <div>
                <p className="font-semibold">{t('Average summer greenness around {site}', { site })}</p>
                <p className="text-muted-foreground">
                  {t('June–August {from}–{to}, from Landsat satellites', { from: greenness.years[0], to: greenness.years[1] })}
                </p>
              </div>
              <ScaleBar
                low={t('bare ground')}
                high={t('dense green crop')}
                gradient={`linear-gradient(to right, ${greenness.palette.map((colour) => `#${colour}`).join(', ')})`}
              />
              <p className="hidden text-muted-foreground sm:block">
                {t('Wheat is harvested in June, so wheat and fallow fields stay pale. Fields with a crop every summer are dark green.')}
              </p>
            </>
          )}
          {/* Loaded, and no image covers the selected field */}
          {((layer === 'heat' && heat && !heatScene) || (layer === 'greenness' && greenness && !greennessHere)) && (
            <p>{t(LAYER_NOTES[layer].none)}</p>
          )}
          {canOpen && (
            <button
              type="button"
              onClick={() => onOpenViewer(layer)}
              className="pw-press pw-brand inline-flex min-h-10 items-center gap-1.5 rounded-full px-4 text-[13px] font-medium"
            >
              {t(LAYER_NOTES[layer].action)}
              <ArrowUpRight aria-hidden className="h-4 w-4" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
