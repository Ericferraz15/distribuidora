// Wordmark da P12 Distribuidora. `compacto` mostra só o selo "P12" (bottom nav);
// caso contrário mostra selo + "DISTRIBUIDORA". As cores vêm dos tokens (âmbar).
export default function Logo({ compacto = false }) {
  return (
    <span className={'logo' + (compacto ? ' logo--compacto' : '')} aria-label="P12 Distribuidora">
      <span className="logo__selo" aria-hidden>
        P<span className="logo__num">12</span>
      </span>
      {!compacto && <span className="logo__wordmark">Distribuidora</span>}
    </span>
  )
}
