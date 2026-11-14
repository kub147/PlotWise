// Pusta strona z samym nagłówkiem. Treść powstanie w kolejnych krokach (specyfikacja, sekcja 9).
export function EmptyPage({ title }: { title: string }) {
  return (
    <div className="mx-auto max-w-[1680px] p-4 lg:p-6">
      <h1 className="text-[28px] font-semibold">{title}</h1>
    </div>
  )
}
