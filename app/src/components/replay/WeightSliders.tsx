// Lewa kolumna Rotation replay: cztery suwaki priorytetów 0–100 i reset do równych wag.
// Kryteria są takie, jak liczy silnik (engine/scoring.py): income, dry_year_safety, water, soil.
import { Button } from '@/components/ui/button'
import { CRITERIA, EQUAL_WEIGHTS, type Criterion, type Weights } from '@/lib/results'

// Nazwy i opisy prostym językiem. Opis mówi, co dokładnie mierzy wynik w silniku.
const CRITERION_TEXT: Record<Criterion, { label: string; hint: string }> = {
  income: { label: 'Net return', hint: 'Average return per acre over all replayed years.' },
  dry_year_safety: { label: 'Holding up in dry years', hint: 'Average return per acre in the dry years only.' },
  water: { label: 'Putting rain to work', hint: 'Share of the rain that goes through a crop instead of being lost.' },
  soil: { label: 'Soil', hint: 'Crops harvested per year. More crops return more residue and roots.' },
}

type WeightSlidersProps = {
  weights: Weights
  onChange: (weights: Weights) => void
}

export function WeightSliders({ weights, onChange }: WeightSlidersProps) {
  const isEqual = CRITERIA.every((criterion) => weights[criterion] === EQUAL_WEIGHTS[criterion])
  return (
    <section aria-labelledby="priorities-heading" className="flex flex-col gap-4">
      <div>
        <h2 id="priorities-heading" className="text-[19px] font-semibold">
          Your priorities
        </h2>
        <p className="mt-1 text-[13px] text-muted-foreground">
          Move a slider to the right for what matters more to you. The ranking updates as you move.
        </p>
      </div>

      {CRITERIA.map((criterion) => {
        const id = `weight-${criterion}`
        const text = CRITERION_TEXT[criterion]
        const value = weights[criterion]
        return (
          <div key={criterion}>
            <div className="flex items-baseline justify-between gap-3">
              <label htmlFor={id} className="text-[15px] font-semibold">
                {text.label}
              </label>
              <output htmlFor={id} className="font-mono text-[15px] font-medium">
                {value}
              </output>
            </div>
            <input
              id={id}
              type="range"
              min={0}
              max={100}
              step={5}
              value={value}
              aria-describedby={`${id}-hint`}
              onChange={(event) => onChange({ ...weights, [criterion]: Number(event.target.value) })}
              className="pw-range"
              style={{ ['--fill' as string]: `${value}%` }}
            />
            <p id={`${id}-hint`} className="text-[13px] leading-snug text-muted-foreground">
              {text.hint}
            </p>
          </div>
        )
      })}

      <Button variant="outline" width="full" disabled={isEqual} onClick={() => onChange(EQUAL_WEIGHTS)}>
        Reset to equal weights
      </Button>
    </section>
  )
}
