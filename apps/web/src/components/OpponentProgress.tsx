interface OpponentProgressProps {
  nome: string
  tentativasUsadas: number
  /** Competitivo tem teto fixo de 6; Hardcore/Normal não têm teto (tentativas
   * ilimitadas até acertar ou o tempo acabar) — isso só baliza o desenho das
   * caixinhas, o que importa de verdade é `tentativasUsadas`. */
  tentativasReferencia?: number
}

export function OpponentProgress({
  nome,
  tentativasUsadas,
  tentativasReferencia = 6,
}: OpponentProgressProps) {
  const emProrrogacao = tentativasUsadas > tentativasReferencia
  const quantidadePreenchida = Math.min(tentativasUsadas, tentativasReferencia)

  return (
    <div className="text-center">
      <p className="text-sm font-semibold text-fg-muted">{nome}</p>
      <div
        className="mt-1 flex items-center justify-center gap-1"
        role="img"
        aria-label={`${nome}: ${String(tentativasUsadas)} tentativa(s) usada(s)`}
      >
        {Array.from({ length: tentativasReferencia }, (_, indice) => (
          <span
            key={indice}
            className={`h-3 w-5 rounded-sm ${
              indice < quantidadePreenchida ? 'bg-tile-border-filled' : 'bg-tile-border'
            }`}
          />
        ))}
        {emProrrogacao && (
          <span className="ml-1 text-xs font-bold text-fg-muted">
            +{tentativasUsadas - tentativasReferencia}
          </span>
        )}
      </div>
    </div>
  )
}
