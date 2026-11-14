// Płodozmiany i litery upraw. Pliki zapisują płodozmian na dwa sposoby:
// `W-S-F` w fields.geojson i `WSF` w results/*.json. Tu jest jedna normalizacja.

export type CropLetter = 'W' | 'S' | 'C' | 'F' | 'O' | 'Sf'

export const CROP_NAMES: Record<CropLetter, string> = {
  W: 'Wheat',
  S: 'Sorghum',
  C: 'Corn',
  F: 'Fallow',
  O: 'Other crop',
  Sf: 'Sunflower',
}

// Płodozmiany, które liczy silnik (results/*.json).
export const MODELED_ROTATIONS = ['WF', 'WSF', 'WCF', 'WSSF', 'WWSF', 'WSfF'] as const

// Dzieli zapis płodozmianu na fazy: "W-S-F" -> ["W","S","F"], "WSfF" -> ["W","Sf","F"].
// Zwraca null, gdy tekst nie jest ciągiem liter upraw (np. "continuous (no fallow)").
export function rotationPhases(value: string | null | undefined): string[] | null {
  if (!value) return null
  const compact = value.replace(/-/g, '')
  if (!/^(Sf|[WSCF])+$/.test(compact)) return null
  return compact.match(/Sf|[WSCF]/g)
}

// Zapis bez myślników, taki jak identyfikatory w wynikach silnika: "W-S-F" -> "WSF".
export function rotationId(value: string | null | undefined): string | null {
  const phases = rotationPhases(value)
  return phases ? phases.join('') : null
}

// Zapis do wyświetlania: "WSF" -> "W-S-F".
export function rotationLabel(value: string | null | undefined): string | null {
  const phases = rotationPhases(value)
  return phases ? phases.join('-') : null
}

export function isModeledRotation(value: string | null | undefined): boolean {
  const id = rotationId(value)
  return id !== null && (MODELED_ROTATIONS as readonly string[]).includes(id)
}

// Litera z `crop_sequence` albo faza płodozmianu; wszystko spoza znanych liter traktujemy jako "Other".
export function toCropLetter(letter: string): CropLetter {
  return letter === 'W' || letter === 'S' || letter === 'C' || letter === 'F' || letter === 'Sf' ? letter : 'O'
}

// Nazwa płodozmianu do wyświetlenia: w plikach jest "Wheat - sorghum - fallow", pokazujemy z półpauzami.
export function rotationDisplayName(name: string): string {
  return name.replace(/ - /g, ' – ')
}

// Samo wypełnienie uprawy (klasa CSS), bez litery: do paska historii pola nad górnym paskiem.
export const CROP_FILL_CLASS: Record<CropLetter, string> = {
  W: 'bg-crop-w',
  S: 'bg-crop-s',
  C: 'bg-crop-c',
  F: 'bg-crop-f',
  O: 'bg-crop-o',
  Sf: 'bg-card',
}
