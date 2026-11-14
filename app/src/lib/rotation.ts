// Rotations and crop letters. The files write a rotation in two ways:
// `W-S-F` in fields.geojson and `WSF` in results/*.json. This is the one place that normalises them.

export type CropLetter = 'W' | 'S' | 'C' | 'F' | 'O' | 'Sf'

export const CROP_NAMES: Record<CropLetter, string> = {
  W: 'Wheat',
  S: 'Sorghum',
  C: 'Corn',
  F: 'Fallow',
  O: 'Other crop',
  Sf: 'Sunflower',
}

// Rotations the engine replays (results/*.json).
export const MODELED_ROTATIONS = ['WF', 'WSF', 'WCF', 'WSSF', 'WWSF', 'WSfF'] as const

// Splits a rotation into phases: "W-S-F" -> ["W","S","F"], "WSfF" -> ["W","Sf","F"].
// Returns null when the text is not a string of crop letters (e.g. "continuous (no fallow)").
export function rotationPhases(value: string | null | undefined): string[] | null {
  if (!value) return null
  const compact = value.replace(/-/g, '')
  if (!/^(Sf|[WSCF])+$/.test(compact)) return null
  return compact.match(/Sf|[WSCF]/g)
}

// Form without dashes, like the IDs in the engine results: "W-S-F" -> "WSF".
export function rotationId(value: string | null | undefined): string | null {
  const phases = rotationPhases(value)
  return phases ? phases.join('') : null
}

// Form for display: "WSF" -> "W-S-F".
export function rotationLabel(value: string | null | undefined): string | null {
  const phases = rotationPhases(value)
  return phases ? phases.join('-') : null
}

export function isModeledRotation(value: string | null | undefined): boolean {
  const id = rotationId(value)
  return id !== null && (MODELED_ROTATIONS as readonly string[]).includes(id)
}

// Letter from `crop_sequence` or a rotation phase; anything outside the known letters counts as "Other".
export function toCropLetter(letter: string): CropLetter {
  return letter === 'W' || letter === 'S' || letter === 'C' || letter === 'F' || letter === 'Sf' ? letter : 'O'
}

// Rotation name for display: the files have "Wheat - sorghum - fallow"; we show it with en dashes.
export function rotationDisplayName(name: string): string {
  return name.replace(/ - /g, ' – ')
}

// Crop fill only (a CSS class), without the letter: for the field-history strip in the top bar.
export const CROP_FILL_CLASS: Record<CropLetter, string> = {
  W: 'bg-crop-w',
  S: 'bg-crop-s',
  C: 'bg-crop-c',
  F: 'bg-crop-f',
  O: 'bg-crop-o',
  Sf: 'bg-card',
}
