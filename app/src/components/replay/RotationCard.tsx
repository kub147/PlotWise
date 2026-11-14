// Prawa kolumna Rotation replay: karta wybranego płodozmianu.
// Sekcje: Why, Evidence, What you gain, What you risk, What we do not know, Check locally, zdanie o ubezpieczeniach.
// Wszystkie teksty pochodzą z wyników silnika (rotations.json części C) i z evidence.md.
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { CropTile } from '@/components/CropTile'
import { Card, CardSection, SectionLabel } from '@/components/ui/card'
import type { Evidence } from '@/lib/evidence'
import type { RotationResult } from '@/lib/results'
import { CROP_NAMES, rotationDisplayName, rotationPhases, toCropLetter } from '@/lib/rotation'
import { formatNumber, formatUsd, yieldInUsUnits } from '@/lib/units'

// Klucz uprawy w wynikach -> litera kafelka.
const CROP_KEY_LETTER: Record<string, string> = {
  winter_wheat: 'W',
  grain_sorghum: 'S',
  corn: 'C',
  sunflower: 'Sf',
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="flex list-disc flex-col gap-1.5 pl-5 text-[15px] leading-snug marker:text-muted-foreground">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  )
}

function Stat({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-[13px] text-muted-foreground">{label}</dt>
      <dd className="font-mono text-[17px] font-semibold">{children}</dd>
    </div>
  )
}

type RotationCardProps = {
  rotation: RotationResult
  yearCount: number
  fieldId: string
  evidence: Evidence | null
}

export function RotationCard({ rotation, yearCount, fieldId, evidence }: RotationCardProps) {
  const phases = rotationPhases(rotation.id) ?? []
  const lossYears = Math.round(rotation.summary.share_of_years_with_loss * yearCount)

  return (
    <Card aria-live="polite">
      <CardSection>
        <div className="flex gap-1" aria-hidden>
          {phases.map((letter, i) => (
            <CropTile key={i} letter={letter} />
          ))}
        </div>
        <h2 className="mt-2 text-[21px] font-semibold leading-tight">{rotationDisplayName(rotation.name)}</h2>
        {rotation.is_current && <p className="mt-1 text-[13px] font-semibold">Your rotation today</p>}

        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3">
          <Stat label="Average per acre a year">{formatUsd(rotation.summary.mean)}</Stat>
          <Stat label={`Worst year (${rotation.summary.worst_year})`}>{formatUsd(rotation.summary.worst)}</Stat>
          <Stat label="Years with a loss">
            {lossYears} <span className="font-sans text-[13px] font-medium text-muted-foreground">of {yearCount}</span>
          </Stat>
          <Stat label="Bare ground, modeled">
            {formatNumber(rotation.indicators.bare_days_per_year)}{' '}
            <span className="font-sans text-[13px] font-medium text-muted-foreground">days a year</span>
          </Stat>
        </dl>

        <p className="mt-4 text-[13px] text-muted-foreground">Average yield in this rotation, at farm level</p>
        <ul className="mt-1 flex flex-col gap-1">
          {Object.entries(rotation.mean_yield_kg_ha).map(([crop, kgHa]) => {
            const converted = yieldInUsUnits(kgHa, crop)
            const letter = toCropLetter(CROP_KEY_LETTER[crop] ?? 'O')
            return (
              <li key={crop} className="flex items-center gap-2 text-[15px]">
                <CropTile letter={letter} className="h-6 w-6 text-[13px]" />
                <span>{CROP_NAMES[letter]}</span>
                <span className="ml-auto font-mono font-medium">
                  {converted ? `${formatNumber(converted.value)} ${converted.unit}` : `${formatNumber(kgHa)} kg/ha`}
                </span>
              </li>
            )
          })}
        </ul>
      </CardSection>

      <CardSection>
        <SectionLabel>Why</SectionLabel>
        <p className="text-[15px] leading-snug">{rotation.why}</p>
      </CardSection>

      <CardSection>
        <SectionLabel>Evidence</SectionLabel>
        <ul className="flex flex-col gap-2">
          {rotation.evidence.map((id) => {
            const item = evidence?.items[id]
            return (
              <li key={id} className="grid grid-cols-[2.75rem_minmax(0,1fr)] gap-x-2 text-[13px] leading-snug">
                <Link
                  to={{ pathname: '/how', search: `?field=${fieldId}&evidence=${id}` }}
                  className="font-mono text-[13px] font-semibold text-primary underline underline-offset-2"
                >
                  {id}
                </Link>
                <span className="text-muted-foreground">{item ? item.finding : 'See “How we know” for this source.'}</span>
              </li>
            )
          })}
        </ul>
      </CardSection>

      <CardSection>
        <SectionLabel>What you gain</SectionLabel>
        <BulletList items={rotation.benefits} />
      </CardSection>

      <CardSection>
        <SectionLabel>What you risk</SectionLabel>
        <BulletList items={rotation.risks} />
      </CardSection>

      <CardSection>
        <SectionLabel>What we do not know</SectionLabel>
        <BulletList items={rotation.gaps} />
      </CardSection>

      <CardSection>
        <SectionLabel>Check locally</SectionLabel>
        <BulletList items={rotation.check_locally} />
      </CardSection>

      {/* Zdanie o ubezpieczeniach z evidence.md; widoczny placeholder, gdyby go tam zabrakło */}
      {evidence && (
        <CardSection>
          <p className="text-[13px] leading-snug text-muted-foreground">
            {evidence.insuranceSentence ?? '[INSURANCE SENTENCE NOT FOUND IN evidence.md]'}
          </p>
        </CardSection>
      )}
    </Card>
  )
}
