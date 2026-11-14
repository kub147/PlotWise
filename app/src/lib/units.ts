// Wszystkie konwersje jednostek w jednym miejscu (specyfikacja, sekcja 6).
// Dane w repo są metryczne; interfejs pokazuje jednostki amerykańskie.

const KG_HA_TO_BU_ACRE_60LB = 0.01487 // pszenica, 60 lb/bu
const KG_HA_TO_BU_ACRE_56LB = 0.01593 // sorgo, kukurydza, 56 lb/bu
const HA_TO_ACRE = 2.471

export const haToAcres = (ha: number) => ha * HA_TO_ACRE
export const mmToInches = (mm: number) => mm / 25.4
export const cmToInches = (cm: number) => cm / 2.54
export const cToF = (c: number) => c * 1.8 + 32
// Różnica lub suma stopni (np. stopniodni): bez przesunięcia o 32.
export const cDeltaToF = (c: number) => c * 1.8
export const usdPerHaToUsdPerAcre = (usd: number) => usd / HA_TO_ACRE

const KG_HA_TO_LB_ACRE = 0.8922

// Plon w jednostkach, w których farmer w USA podaje daną uprawę.
// Pszenica, sorgo i kukurydza w bu/acre; słonecznik w lb/acre. Nieznana uprawa -> null (nie zgadujemy).
export function yieldInUsUnits(kgHa: number, crop: string): { value: number; unit: string } | null {
  if (crop === 'winter_wheat') return { value: kgHa * KG_HA_TO_BU_ACRE_60LB, unit: 'bu/acre' }
  if (crop === 'grain_sorghum' || crop === 'corn') return { value: kgHa * KG_HA_TO_BU_ACRE_56LB, unit: 'bu/acre' }
  if (crop === 'sunflower') return { value: kgHa * KG_HA_TO_LB_ACRE, unit: 'lb/acre' }
  return null
}

// Formatowanie liczb w stylu amerykańskim.
export function formatNumber(value: number, digits = 0) {
  return value.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

// Dolary ze znakiem minus przed symbolem: -31.2 -> "−$31".
export function formatUsd(value: number) {
  const rounded = Math.round(value)
  return `${rounded < 0 ? '−' : ''}$${Math.abs(rounded).toLocaleString('en-US')}`
}
