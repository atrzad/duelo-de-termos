import { useApiHealth } from '../hooks/useApiHealth'

export function ServerStatus() {
  const { isPending, isError } = useApiHealth()

  const [dot, text] = isPending
    ? ['bg-fg-muted', 'Verificando servidor…']
    : isError
      ? ['bg-danger', 'Servidor offline']
      : ['bg-tile-correct', 'Servidor online']

  return (
    <p role="status" className="inline-flex items-center gap-2 text-sm text-fg-muted">
      <span aria-hidden="true" className={`size-2.5 rounded-full ${dot}`} />
      {text}
    </p>
  )
}
