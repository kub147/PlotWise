// The selected field is global state kept in the URL: #/replay?field=ks071-001.
import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { FieldFeature } from '@/lib/data'

export const DEFAULT_FIELD_ID = 'ks071-001'

export function useSelectedField(fields: FieldFeature[]) {
  const [params, setParams] = useSearchParams()
  const requested = params.get('field')
  // Unknown ID in the URL -> the default field, and if that is missing, the first in the list.
  const selected =
    fields.find((field) => field.properties.field_id === requested) ??
    fields.find((field) => field.properties.field_id === DEFAULT_FIELD_ID) ??
    fields[0]

  const select = useCallback(
    (fieldId: string) => {
      setParams((current) => {
        const next = new URLSearchParams(current)
        next.set('field', fieldId)
        return next
      })
    },
    [setParams],
  )

  return [selected, select] as const
}
