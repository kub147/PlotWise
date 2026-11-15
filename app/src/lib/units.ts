// All unit conversions in one place (spec, section 6).
// Data in the repo is metric; the interface shows US units.

const KG_HA_TO_BU_ACRE_60LB = 0.01487 // pszenica, 60 lb/bu
const KG_HA_TO_BU_ACRE_56LB = 0.01593 // sorgo, kukurydza, 56 lb/bu
const HA_TO_ACRE = 2.471

export const haToAcres = (ha: number) => ha * HA_TO_ACRE
export const mmToInches = (mm: number) => mm / 25.4
export const cmToInches = (cm: number) => cm / 2.54
export const cToF = (c: number) => c * 1.8 + 32
// A difference or sum of degrees (e.g. degree days): no offset of 32.
export const cDeltaToF = (c: number) => c * 1.8
// Temperature unit of the interface: °F in English, °C in Polish (lib/i18n.ts, useTempUnit).
export type TempUnit = 'F' | 'C'
// A temperature reading, e.g. "95°F" or "35°C".
export const formatTemp = (c: number, unit: TempUnit, digits = 0) =>
  `${formatNumber(unit === 'F' ? cToF(c) : c, digits)}°${unit}`
// A difference of temperatures in the chosen unit (no offset of 32).
export const tempDelta = (c: number, unit: TempUnit) => (unit === 'F' ? cDeltaToF(c) : c)
export const usdPerHaToUsdPerAcre = (usd: number) => usd / HA_TO_ACRE

const KG_HA_TO_LB_ACRE = 0.8922

// Yield in the units a US farmer uses for that crop.
// Wheat, sorghum and corn in bu/acre; sunflower in lb/acre. Unknown crop -> null (we do not guess).
export function yieldInUsUnits(kgHa: number, crop: string): { value: number; unit: string } | null {
  if (crop === 'winter_wheat') return { value: kgHa * KG_HA_TO_BU_ACRE_60LB, unit: 'bu/acre' }
  if (crop === 'grain_sorghum' || crop === 'corn') return { value: kgHa * KG_HA_TO_BU_ACRE_56LB, unit: 'bu/acre' }
  if (crop === 'sunflower') return { value: kgHa * KG_HA_TO_LB_ACRE, unit: 'lb/acre' }
  return null
}

// Number style follows the interface language: "1,221.5" in English, "1221,5" / "31 660" in Polish.
// LanguageProvider sets it before the app renders, so every number on screen uses the current language.
let numberLocale = 'en-US'
export function setNumberLocale(lang: 'en' | 'pl') {
  numberLocale = lang === 'pl' ? 'pl-PL' : 'en-US'
}

export function formatNumber(value: number, digits = 0) {
  // Rounding first avoids "−0.0" when a tiny negative value rounds to zero.
  const rounded = Number(value.toFixed(digits)) || 0
  return rounded.toLocaleString(numberLocale, { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

// Dollars with the minus sign before the amount: -31.2 -> "−$31" in English, "−31 USD" in Polish.
export function formatUsd(value: number) {
  const rounded = Math.round(value) || 0
  const sign = rounded < 0 ? '−' : ''
  const amount = Math.abs(rounded).toLocaleString(numberLocale)
  return numberLocale === 'pl-PL' ? `${sign}${amount} USD` : `${sign}$${amount}`
}
