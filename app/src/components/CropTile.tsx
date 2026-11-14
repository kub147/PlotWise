// Crop tile: always a letter plus a colour, never colour alone.
import { useT } from '@/lib/i18n'
import { CROP_NAMES, toCropLetter, type CropLetter } from '@/lib/rotation'
import { cn } from '@/lib/utils'

const TILE_CLASS: Record<CropLetter, string> = {
  W: 'bg-crop-w text-crop-w-fg',
  S: 'bg-crop-s text-crop-s-fg',
  C: 'bg-crop-c text-crop-c-fg',
  F: 'bg-crop-f text-crop-f-fg',
  O: 'bg-crop-o text-crop-o-fg',
  // Sunflower (only in the optional W-Sf-F): no colour of its own; a thick ring and two letters set it apart.
  Sf: 'bg-card text-foreground ring-[1.5px] ring-inset ring-foreground text-[13px]',
}

type CropTileProps = {
  letter: string
  size?: 'strip' | 'badge'
  className?: string
}

export function CropTile({ letter, size = 'badge', className }: CropTileProps) {
  const crop = toCropLetter(letter)
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-[8px] font-mono font-semibold leading-none',
        size === 'badge' ? 'h-8 w-8 text-[15px]' : 'h-8 w-full text-[13px]',
        TILE_CLASS[crop],
        className,
      )}
    >
      {crop}
    </span>
  )
}

// Legend of the letters used in the app.
export function CropLegend({ letters }: { letters: CropLetter[] }) {
  const t = useT()
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1.5 text-[13px] text-muted-foreground">
      {letters.map((letter) => (
        <li key={letter} className="flex items-center gap-1.5">
          <CropTile letter={letter} className="h-5 w-5 text-[13px]" />
          {t(CROP_NAMES[letter])}
        </li>
      ))}
    </ul>
  )
}
