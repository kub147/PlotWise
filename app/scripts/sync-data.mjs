// Kopiuje dane innych części projektu do app/static/ (katalog plików statycznych Vite), żeby aplikacja mogła je wczytać jako pliki statyczne.
// Uruchamiany automatycznie przed `npm run dev` i `npm run build`. Nie zmienia plików źródłowych.
import { cpSync, existsSync, mkdirSync, readdirSync, statSync, unlinkSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const appDir = join(dirname(fileURLToPath(import.meta.url)), '..')
const repo = join(appDir, '..')
const processed = join(repo, 'data', 'processed')
const outData = join(appDir, 'static', 'data')
const outImg = join(appDir, 'static', 'img')

// Katalogów nie usuwamy: gdy działa `npm run dev`, Windows blokuje je i usuwanie kończy się błędem EPERM.
// Nadpisujemy pliki, a na końcu kasujemy tylko te, których już nie ma w źródłach.
mkdirSync(outData, { recursive: true })
mkdirSync(outImg, { recursive: true })

const missing = []
const written = new Set()

function copyFile(from, to) {
  if (!existsSync(from)) {
    missing.push(from)
    return false
  }
  mkdirSync(dirname(to), { recursive: true })
  cpSync(from, to)
  written.add(to)
  return true
}

// Kopiuje pliki z katalogu pasujące do wzorca i zwraca ich nazwy.
function copyMatching(fromDir, toDir, pattern) {
  if (!existsSync(fromDir)) {
    missing.push(fromDir)
    return []
  }
  const names = readdirSync(fromDir).filter((name) => pattern.test(name))
  for (const name of names) copyFile(join(fromDir, name), join(toDir, name))
  return names
}

// Pojedyncze pliki
copyFile(join(processed, 'fields.geojson'), join(outData, 'fields.geojson'))
copyFile(join(processed, 'counties.geojson'), join(outData, 'counties.geojson'))
copyFile(join(processed, 'county_rotation_summary.json'), join(outData, 'county_rotation_summary.json'))
// Region page: rotations of 31,660 fields per county, field outlines of the demo counties, engine results per county.
copyFile(join(processed, 'county_field_rotations.json'), join(outData, 'county_field_rotations.json'))
copyFile(join(processed, 'county_fields.geojson'), join(outData, 'county_fields.geojson'))
copyFile(join(processed, 'results', 'counties.json'), join(outData, 'county_results.json'))
// "How we know" page: measured and modelled yields at the Tribune trials (python -m engine.validate).
// Optional: without it the page shows the report's picture instead of its own charts.
if (existsSync(join(processed, 'results', 'validation.json'))) {
  copyFile(join(processed, 'results', 'validation.json'), join(outData, 'validation.json'))
}
copyFile(join(processed, 'heat', 'ecostress_summary.json'), join(outData, 'ecostress_summary.json'))
copyFile(join(repo, 'crops-economics', 'reference', 'evidence.md'), join(outData, 'evidence.md'))

// Pliki per pole. Wzorzec ks<fips>-<nr> pomija sample.json i pliki pomocnicze.
const fieldJson = /^ks\d{3}-\d{3}\.json$/
const fieldCsv = /^ks\d{3}-\d{3}\.csv$/
const climate = copyMatching(join(processed, 'climate'), join(outData, 'climate'), fieldJson)
const results = copyMatching(join(processed, 'results'), join(outData, 'results'), fieldJson)
const ndvi = copyMatching(join(processed, 'ndvi'), join(outData, 'ndvi'), fieldCsv)

// Obrazki
const images = copyMatching(join(repo, 'docs', 'img'), outImg, /\.png$/)

// Manifest: aplikacja sprawdza w nim, co istnieje dla danego pola, zamiast zgadywać.
const idOf = (name) => name.replace(/\.(json|csv)$/, '')
const manifest = {
  climate: climate.map(idOf),
  results: results.map(idOf),
  ndvi: ndvi.map(idOf),
  naip: images
    .map((name) => /^field_(ks\d{3}-\d{3})_naip\.png$/.exec(name)?.[1])
    .filter(Boolean),
  ecostress: images.filter((name) => name.startsWith('ecostress_')),
}
writeFileSync(join(outData, 'manifest.json'), JSON.stringify(manifest, null, 1))
written.add(join(outData, 'manifest.json'))

// Usuwa pliki z poprzedniej kopii, których nie ma już w źródłach.
function pruneStale(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) pruneStale(path)
    else if (!written.has(path)) unlinkSync(path)
  }
}
pruneStale(outData)
pruneStale(outImg)

console.log(
  `sync-data: ${climate.length} climate, ${results.length} results, ${ndvi.length} ndvi, ${images.length} images`,
)
if (missing.length > 0) {
  console.error('sync-data: brakuje plików źródłowych:\n  ' + missing.join('\n  '))
  process.exit(1)
}
