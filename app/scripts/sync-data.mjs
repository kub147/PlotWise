// Copies the data of the other workstreams into app/static/ (Vite's static folder) so that the app can load them as static files.
// Runs automatically before `npm run dev` and `npm run build`. It never changes the source files.
import { cpSync, existsSync, mkdirSync, readdirSync, statSync, unlinkSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const appDir = join(dirname(fileURLToPath(import.meta.url)), '..')
const repo = join(appDir, '..')
const processed = join(repo, 'data', 'processed')
const outData = join(appDir, 'static', 'data')
const outImg = join(appDir, 'static', 'img')

// Folders are not deleted: on some drives Windows keeps them locked and the delete fails with EPERM.
// Files are overwritten, and at the end only those no longer present in the sources are removed.
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

// Copies the files of a folder that match the pattern and returns their names.
function copyMatching(fromDir, toDir, pattern) {
  if (!existsSync(fromDir)) {
    missing.push(fromDir)
    return []
  }
  const names = readdirSync(fromDir).filter((name) => pattern.test(name))
  for (const name of names) copyFile(join(fromDir, name), join(toDir, name))
  return names
}

// Single files
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

// Per-field files. The pattern ks<fips>-<no> skips sample.json and helper files.
const fieldJson = /^ks\d{3}-\d{3}\.json$/
const fieldCsv = /^ks\d{3}-\d{3}\.csv$/
const climate = copyMatching(join(processed, 'climate'), join(outData, 'climate'), fieldJson)
const results = copyMatching(join(processed, 'results'), join(outData, 'results'), fieldJson)
const ndvi = copyMatching(join(processed, 'ndvi'), join(outData, 'ndvi'), fieldCsv)

// Images
const images = copyMatching(join(repo, 'docs', 'img'), outImg, /\.png$/)

// Manifest: the app looks up what exists for a field here instead of guessing.
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

// Removes files of the previous copy that are no longer in the sources.
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
  console.error('sync-data: missing source files:\n  ' + missing.join('\n  '))
  process.exit(1)
}
