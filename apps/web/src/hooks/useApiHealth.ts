import { useQuery } from '@tanstack/react-query'

import { getHealth } from '../services/api'

export function useApiHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => getHealth(signal),
    refetchInterval: 15_000,
  })
}
