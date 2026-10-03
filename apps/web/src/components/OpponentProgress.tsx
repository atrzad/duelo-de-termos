interface OpponentProgressProps {
  nome: string
  tentativasUsadas: number
  maxTentativas: number
}

export function OpponentProgress({ nome, tentativasUsadas, maxTentativas }: OpponentProgressProps) {
  return (
    <div className="text-center">
      <p className="text-sm font-semibold text-fg-muted">{nome}</p>
      <div
        className="mt-1 flex justify-center gap-1"
        role="img"
        aria-label={`${nome}: ${String(tentativasUsadas)} de ${String(maxTentativas)} tentativas usadas`}
      >
        {Array.from({ length: maxTentativas }, (_, indice) => (
          <span
            key={indice}
            className={`h-3 w-5 rounded-sm ${
              indice < tentativasUsadas ? 'bg-tile-border-filled' : 'bg-tile-border'
            }`}
          />
        ))}
      </div>
    </div>
  )
}
