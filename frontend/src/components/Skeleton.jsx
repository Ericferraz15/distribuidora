// Placeholders animados de carregamento (substituem o "Carregando…" text-only).
export function Skeleton({ className = '', style }) {
  return <div className={`skeleton ${className}`} style={style} aria-hidden />
}

// Bloco de N linhas — bom para simular tabelas/listas enquanto os dados chegam.
export function SkeletonLinhas({ linhas = 4 }) {
  return (
    <div aria-busy="true" aria-label="Carregando">
      <Skeleton className="skeleton--titulo" />
      {Array.from({ length: linhas }).map((_, i) => (
        <Skeleton key={i} className="skeleton--linha" style={{ width: `${90 - i * 8}%` }} />
      ))}
    </div>
  )
}
