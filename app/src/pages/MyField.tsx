// Widok „My field": trzy kolumny (lista pól, mapa, karta pola). Na telefonie kolumny układają się jedna pod drugą.
import { FieldCard } from '@/components/FieldCard'
import { FieldList } from '@/components/FieldList'
import { FieldMap } from '@/components/FieldMap'
import type { AppData, FieldFeature } from '@/lib/data'

type MyFieldProps = {
  data: AppData
  selected: FieldFeature
  onSelect: (fieldId: string) => void
}

export function MyField({ data, selected, onSelect }: MyFieldProps) {
  return (
    <div className="mx-auto grid max-w-[1680px] grid-cols-1 gap-4 p-4 lg:h-full lg:grid-cols-[280px_minmax(0,1fr)_420px] lg:gap-5 lg:p-5">
      <h1 className="sr-only">My field</h1>
      <div className="min-w-0 lg:min-h-0 lg:overflow-y-auto lg:pr-1">
        <FieldList data={data} selectedId={selected.properties.field_id} onSelect={onSelect} />
      </div>
      <div className="min-w-0 lg:min-h-0">
        <FieldMap fields={data.fields} selected={selected} onSelect={onSelect} />
      </div>
      <div className="min-w-0 lg:min-h-0 lg:overflow-y-auto lg:pr-1">
        <FieldCard data={data} field={selected} />
      </div>
    </div>
  )
}
