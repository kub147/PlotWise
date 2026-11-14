// Empty page with a heading only; used for unknown routes.
export function EmptyPage({ title }: { title: string }) {
  return (
    <div className="mx-auto max-w-[1680px] p-4 lg:p-6">
      <h1 className="text-[34px] font-semibold leading-tight">{title}</h1>
    </div>
  )
}
