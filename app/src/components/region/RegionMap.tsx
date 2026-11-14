// Map of the study area: 46 counties coloured by the chosen layer, plus the field outlines of the three
// demo counties coloured by rotation. Drawn on canvas so a few thousand polygons stay smooth.
import 'leaflet/dist/leaflet.css'
import type { LatLngBoundsExpression, Layer, PathOptions } from 'leaflet'
import { useEffect, useMemo, useState } from 'react'
import { GeoJSON, MapContainer, TileLayer, ZoomControl, useMap, useMapEvents } from 'react-leaflet'
import {
  ROTATION_CLASS_STYLE,
  countyColor,
  type CountyCollection,
  type CountyFieldCollection,
  type CountyResults,
  type RegionLayer,
  type RotationClass,
} from '@/lib/region'
import type { Scenario } from '@/lib/results'

const STREET_TILES = {
  url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}

// Western Kansas, west of 98.3° W.
const REGION_BOUNDS: LatLngBoundsExpression = [
  [36.95, -102.1],
  [40.05, -98.25],
]

// Moves the map when the page asks for a county or for the whole region. `nonce` lets the same target repeat.
function FlyTo({ target }: { target: { bounds: LatLngBoundsExpression; nonce: number } | null }) {
  const map = useMap()
  useEffect(() => {
    if (target) map.flyToBounds(target.bounds, { padding: [24, 24], duration: 0.7 })
  }, [target, map])
  return null
}

// From this zoom on the fields are large enough to read, so the county colour steps back.
const FIELD_ZOOM = 8

function WatchZoom({ onChange }: { onChange: (close: boolean) => void }) {
  // moveend as well: an animated flight to a county does not always end with a zoomend.
  const report = () => onChange(map.getZoom() >= FIELD_ZOOM)
  const map = useMapEvents({ zoomend: report, moveend: report })
  return null
}

type RegionMapProps = {
  counties: CountyCollection
  results: CountyResults
  fields: CountyFieldCollection | null
  layer: RegionLayer
  scenario: Scenario
  selectedId: string | null
  onSelect: (countyId: string) => void
  focus: { bounds: LatLngBoundsExpression; nonce: number } | null
}

export function RegionMap({ counties, results, fields, layer, scenario, selectedId, onSelect, focus }: RegionMapProps) {
  // The selected county is drawn again on top so its outline is not hidden by its neighbours.
  const selected = useMemo(
    () => counties.features.find((feature) => feature.properties.county_id === selectedId) ?? null,
    [counties, selectedId],
  )

  const [close, setClose] = useState(false)
  // Without field outlines there is nothing to reveal, so the county colour stays.
  const showFields = close && fields !== null

  return (
    <div className="relative h-[460px] overflow-hidden rounded-[28px] bg-map-frame shadow-soft lg:h-full">
      <MapContainer bounds={REGION_BOUNDS} zoomControl={false} scrollWheelZoom preferCanvas zoomSnap={0.25} className="h-full w-full">
        <TileLayer url={STREET_TILES.url} attribution={STREET_TILES.attribution} maxZoom={15} />
        <ZoomControl position="bottomright" />
        <GeoJSON
          key={`${layer}-${scenario}-${showFields}`}
          data={counties}
          style={(feature): PathOptions => ({
            color: '#0e1a24',
            weight: 1,
            fillColor: feature
              ? countyColor(layer, feature.properties, results.counties[feature.properties.county_id], scenario)
              : undefined,
            fillOpacity: showFields ? 0.12 : 0.72,
          })}
          onEachFeature={(feature, leafletLayer: Layer) => {
            leafletLayer.on('click', () => onSelect(feature.properties.county_id))
            leafletLayer.bindTooltip(`${feature.properties.name} County`, { sticky: true })
          }}
        />
        {fields && (
          <GeoJSON
            data={fields}
            interactive={false}
            style={(feature): PathOptions => {
              const rotation = feature?.properties.rotation as RotationClass | undefined
              const color = rotation ? ROTATION_CLASS_STYLE[rotation]?.color : undefined
              return { stroke: false, fillColor: color ?? '#7f8a96', fillOpacity: 0.95 }
            }}
          />
        )}
        {selected && (
          <GeoJSON
            key={`selected-${selectedId}`}
            data={selected}
            interactive={false}
            style={{ color: '#b5179e', weight: 3.5, fill: false }}
          />
        )}
        <FlyTo target={focus} />
        <WatchZoom onChange={setClose} />
      </MapContainer>
    </div>
  )
}
