// Widok „My field". Na szerokim ekranie mapa wypełnia cały ekran, a lista pól i karta pola pływają nad nią
// jako dwa panele (lista z lewej jako „szkło", karta z prawej). Na telefonie wszystko układa się jedno pod drugim.
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
    <div className="flex flex-col gap-4 p-4 lg:fixed lg:inset-0 lg:block lg:p-0">
      <h1 className="sr-only">My field</h1>
      <div className="order-2 min-w-0 lg:absolute lg:inset-0">
        <FieldMap fields={data.fields} selected={selected} onSelect={onSelect} />
      </div>
      <div className="pw-glass pw-scroll order-1 min-w-0 rounded-[28px] p-4 lg:absolute lg:bottom-4 lg:left-4 lg:top-[88px] lg:z-[1001] lg:w-[304px] lg:overflow-y-auto">
        <FieldList data={data} selectedId={selected.properties.field_id} onSelect={onSelect} />
      </div>
      {/* key: po wybraniu innego pola karta montuje się od nowa i wjeżdża miękko (pw-rise) */}
      <div
        key={selected.properties.field_id}
        className="pw-rise pw-scroll order-3 min-w-0 lg:absolute lg:bottom-4 lg:right-4 lg:top-[88px] lg:z-[1001] lg:w-[380px] lg:overflow-y-auto xl:w-[420px] lg:rounded-[28px] lg:shadow-lift"
      >
        <FieldCard data={data} field={selected} />
      </div>
    </div>
  )
}
