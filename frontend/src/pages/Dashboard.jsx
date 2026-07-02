import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { useToast } from '../components/Toast.jsx'
import { SkeletonLinhas } from '../components/Skeleton.jsx'
import { formatBRL, formatData, hojeISO } from '../lib/format.js'

function Metrica({ titulo, valor, destaque }) {
  return (
    <div className={'card metrica' + (destaque ? ' metrica--destaque' : '')}>
      <span className="metrica__titulo">{titulo}</span>
      <strong className="metrica__valor">{valor}</strong>
    </div>
  )
}

export default function Dashboard() {
  const toast = useToast()
  const [dia, setDia] = useState(hojeISO())
  const [resumo, setResumo] = useState(null)
  const [caixa, setCaixa] = useState(null)
  const [vendidos, setVendidos] = useState([])
  const [carregando, setCarregando] = useState(true)

  const carregar = useCallback(
    async (dataAlvo) => {
      setCarregando(true)
      try {
        const [r, c, v] = await Promise.all([
          api.dashboardResumo(dataAlvo),
          api.dashboardCaixaStatus(),
          api.dashboardMaisVendidos(10),
        ])
        setResumo(r)
        setCaixa(c)
        setVendidos(v)
      } catch (err) {
        toast.erro(err.message)
      } finally {
        setCarregando(false)
      }
    },
    [toast]
  )

  useEffect(() => {
    carregar(dia)
  }, [dia, carregar])

  return (
    <div className="pagina">
      <header className="pagina__head">
        <div>
          <h2>Dashboard</h2>
          <p className="muted">Visão consolidada da operação (somente administrador).</p>
        </div>
        <label className="campo campo--inline">
          <span>Dia</span>
          <input type="date" value={dia} max={hojeISO()} onChange={(e) => setDia(e.target.value)} />
        </label>
      </header>

      <section className="grid grid--metricas">
        <Metrica titulo="Faturamento" valor={formatBRL(resumo?.faturamento)} destaque />
        <Metrica titulo="Vendas" valor={resumo?.num_vendas ?? '—'} />
        <Metrica titulo="Saídas" valor={formatBRL(resumo?.total_saidas)} />
        <Metrica titulo="Transações" valor={resumo?.num_transacoes ?? '—'} />
      </section>

      <section className="grid grid--2col">
        <div className="card">
          <div className="card__head">
            <h3>Caixa agora</h3>
            <span className={'pill ' + (caixa?.aberto ? 'pill--ok' : 'pill--neutro')}>
              {caixa?.aberto ? 'Aberto' : 'Fechado'}
            </span>
          </div>
          {caixa?.aberto ? (
            <dl className="def">
              <div>
                <dt>Saldo atual</dt>
                <dd className="forte">{formatBRL(caixa.saldo_atual)}</dd>
              </div>
              <div>
                <dt>Saldo inicial</dt>
                <dd>{formatBRL(caixa.saldo_inicial)}</dd>
              </div>
              <div>
                <dt>Entradas</dt>
                <dd className="positivo">{formatBRL(caixa.total_entradas)}</dd>
              </div>
              <div>
                <dt>Saídas</dt>
                <dd className="negativo">{formatBRL(caixa.total_saidas)}</dd>
              </div>
              <div>
                <dt>Responsável</dt>
                <dd>Usuário #{caixa.funcionario_id}</dd>
              </div>
              <div>
                <dt>Aberto em</dt>
                <dd>{formatData(caixa.abertura)}</dd>
              </div>
            </dl>
          ) : (
            <p className="vazio">Nenhum turno aberto no momento.</p>
          )}
        </div>

        <div className="card">
          <div className="card__head">
            <h3>Mais vendidos</h3>
          </div>
          {carregando && vendidos.length === 0 ? (
            <SkeletonLinhas linhas={5} />
          ) : vendidos.length === 0 ? (
            <p className="vazio">Sem vendas registradas.</p>
          ) : (
            <table className="tabela tabela--responsiva">
              <thead>
                <tr>
                  <th>Produto</th>
                  <th className="num">Qtd.</th>
                  <th className="num">Receita</th>
                </tr>
              </thead>
              <tbody>
                {vendidos.map((item) => (
                  <tr key={item.produto_id}>
                    <td data-label="Produto">{item.nome}</td>
                    <td className="num" data-label="Qtd.">{item.quantidade_total}</td>
                    <td className="num" data-label="Receita">{formatBRL(item.receita_total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {carregando && <p className="muted carregando">Atualizando…</p>}
    </div>
  )
}
