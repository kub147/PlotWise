// Kafelek uprawy: zawsze litera plus kolor, nigdy sam kolor.
import { CROP_NAMES, toCropLetter, type CropLetter } from '@/lib/rotation'
import { cn } from '@/lib/utils'

const TILE_CLASS: Record<CropLetter, string> = {
  W: 'bg-crop-w text-crop-w-fg',
  S: 'bg-crop-s text-crop-s-fg',
  C: 'bg-crop-c text-crop-c-fg',
  // Ugór jest najjaśniejszy, więc dostaje ramkę, żeby nie zlewał się z kartą.
  F: 'bg-crop-f text-crop-f-fg ring-1 ring-inset ring-input',
  O: 'bg-crop-o text-crop-o-fg',
  // Słonecznik (tylko w opcjonalnym W-Sf-F): bez własnego koloru, wyróżnia go gruba ramka i dwie litery.
  Sf: 'bg-card text-foreground ring-2 ring-inset ring-foreground text-[13px]',
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
        'inline-flex items-center justify-center rounded-sm font-mono font-semibold leading-none',
        size === 'badge' ? 'h-8 w-8 text-[15px]' : 'h-8 w-full text-[13px]',
        TILE_CLASS[crop],
        className,
      )}
    >
      {crop}
    </span>
  )
}

// Legenda liter używanych w aplikacji.
export function CropLegend({ letters }: { letters: CropLetter[] }) {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1.5 text-[13px] text-muted-foreground">
      {letters.map((letter) => (
        <li key={letter} className="flex items-center gap-1.5">
          <CropTile letter={letter} className="h-5 w-5 text-[13px]" />
          {CROP_NAMES[letter]}
        </li>
      ))}
    </ul>
  )
}
