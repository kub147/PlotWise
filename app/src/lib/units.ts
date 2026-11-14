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

// Number formatting in the US style.
export function formatNumber(value: number, digits = 0) {
  return value.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

// Dollars with the minus sign before the symbol: -31.2 -> "−$31".
export function formatUsd(value: number) {
  const rounded = Math.round(value)
  return `${rounded < 0 ? '−' : ''}$${Math.abs(rounded).toLocaleString('en-US')}`
}
