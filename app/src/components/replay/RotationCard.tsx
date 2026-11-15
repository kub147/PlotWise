// Right column of Rotation replay: the card of the selected rotation.
// Sekcje: Why, Evidence, What you gain, What you risk, What we do not know, Check locally, zdanie o ubezpieczeniach.
// All texts come from the engine results (rotations.json of workstream C) and from evidence.md.
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { CropTile } from '@/components/CropTile'
import { Card, CardSection, SectionLabel } from '@/components/ui/card'
import type { Evidence } from '@/lib/evidence'
import { useLang, useT } from '@/lib/i18n'
import type { RotationResult } from '@/lib/results'
import { CROP_NAMES, rotationDisplayName, rotationPhases, toCropLetter } from '@/lib/rotation'
import { formatNumber, formatUsd, yieldInUsUnits } from '@/lib/units'

// Crop key in the results -> tile letter.
const CROP_KEY_LETTER: Record<string, string> = {
  winter_wheat: 'W',
  grain_sorghum: 'S',
  corn: 'C',
  sunflower: 'Sf',
}

function BulletList({ items }: { items: string[] }) {
  const t = useT()
  return (
    <ul className="flex list-disc flex-col gap-1.5 pl-5 text-[15px] leading-snug marker:text-muted-foreground">
      {items.map((item) => (
        <li key={item}>{t(item)}</li>
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
  const t = useT()
  const { lang } = useLang()

  return (
    <Card aria-live="polite">
      <CardSection>
        <div className="flex gap-1" aria-hidden>
          {phases.map((letter, i) => (
            <CropTile key={i} letter={letter} />
          ))}
        </div>
        <h2 className="mt-2 text-[21px] font-semibold leading-tight">{rotationDisplayName(t(rotation.name))}</h2>
        {rotation.is_current && <p className="mt-1 text-[13px] font-semibold">{t('Your rotation today')}</p>}

        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3">
          <Stat label={t('Average per acre a year')}>{formatUsd(rotation.summary.mean)}</Stat>
          <Stat label={t('Worst year ({year})', { year: rotation.summary.worst_year })}>{formatUsd(rotation.summary.worst)}</Stat>
          <Stat label={t('Years with a loss')}>
            {lossYears} <span className="font-sans text-[13px] font-medium text-muted-foreground">{t('of {n}', { n: yearCount })}</span>
          </Stat>
          <Stat label={t('No growing crop, modeled')}>
            {formatNumber(rotation.indicators.bare_days_per_year)}{' '}
            <span className="font-sans text-[13px] font-medium text-muted-foreground">{t('days a year')}</span>
          </Stat>
        </dl>

        <p className="mt-4 text-[13px] text-muted-foreground">{t('Average yield in this rotation, at farm level')}</p>
        <ul className="mt-1 flex flex-col gap-1">
          {Object.entries(rotation.mean_yield_kg_ha).map(([crop, kgHa]) => {
            const converted = yieldInUsUnits(kgHa, crop)
            const letter = toCropLetter(CROP_KEY_LETTER[crop] ?? 'O')
            return (
              <li key={crop} className="flex items-center gap-2 text-[15px]">
                <CropTile letter={letter} className="h-6 w-6 text-[13px]" />
                <span>{t(CROP_NAMES[letter])}</span>
                <span className="ml-auto font-mono font-medium">
                  {converted ? `${formatNumber(converted.value)} ${t(converted.unit)}` : `${formatNumber(kgHa)} kg/ha`}
                </span>
              </li>
            )
          })}
        </ul>
      </CardSection>

      <CardSection>
        <SectionLabel>{t('Why')}</SectionLabel>
        <p className="text-[15px] leading-snug">{t(rotation.why)}</p>
      </CardSection>

      <CardSection>
        <SectionLabel>{t('Evidence')}</SectionLabel>
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
                <span className="text-muted-foreground">{item ? (lang === 'pl' ? t(`Evidence ${id}`) : item.finding) : t('See “How we know” for this source.')}</span>
              </li>
            )
          })}
        </ul>
      </CardSection>

      <CardSection>
        <SectionLabel>{t('What you gain')}</SectionLabel>
        <BulletList items={rotation.benefits} />
      </CardSection>

      <CardSection>
        <SectionLabel>{t('What you risk')}</SectionLabel>
        <BulletList items={rotation.risks} />
      </CardSection>

      <CardSection>
        <SectionLabel>{t('What we do not know')}</SectionLabel>
        <BulletList items={rotation.gaps} />
      </CardSection>

      <CardSection>
        <SectionLabel>{t('Check locally')}</SectionLabel>
        <BulletList items={rotation.check_locally} />
      </CardSection>

      {/* Insurance sentence from evidence.md; a visible placeholder if it is ever missing there */}
      {evidence && (
        <CardSection>
          <p className="text-[13px] leading-snug text-muted-foreground">
            {evidence.insuranceSentence ? t(evidence.insuranceSentence) : '[INSURANCE SENTENCE NOT FOUND IN evidence.md]'}
          </p>
        </CardSection>
      )}
    </Card>
  )
}
