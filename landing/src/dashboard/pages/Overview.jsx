import { useNavigate, useOutletContext } from 'react-router-dom'
import { POLICIES, tone } from '../../data/stub.js'
import { deriveCertStatus } from '../Dashboard.jsx'

export default function Overview() {
  const navigate = useNavigate()
  const { controls } = useOutletContext()
  const cert = deriveCertStatus(controls)

  const metrics = [
    ['Certification status', cert.label, cert.tone],
    ['Known failure families', '3', 'mute'],
    ['Required controls', `${controls.filter((c) => c.enabled).length} / 4`, controls.every((c) => c.enabled) ? 'ok' : 'risk'],
    ['Residual risk', 'Moderate', 'warn'],
  ]

  return (
    <>
      <div className="page-head">
        <h2>Overview</h2>
        <p>Pre-deployment audit status for the Skild AI demo account. One active conditional certification across three audited policies.</p>
      </div>

      <div className="grid grid-4" style={{ marginBottom: 32 }}>
        {metrics.map(([k, v, t]) => (
          <div className="card metric" key={k}>
            <div className="k text-mute">{k}</div>
            <div className={`v ${tone[t]?.text || ''}`}>{v}</div>
          </div>
        ))}
      </div>

      <div className="label-mono" style={{ marginBottom: 12 }}>Policies</div>
      <div className="card card-flush">
        <table className="table">
          <thead>
            <tr>
              <th className="mono">policy</th>
              <th>status</th>
              <th>deployment scope</th>
              <th>notes</th>
            </tr>
          </thead>
          <tbody>
            {POLICIES.map((p) => (
              <tr key={p.id} className="clickable" onClick={() => navigate('/demo/policies')}>
                <td className="mono">{p.id}</td>
                <td>
                  <span className="status-pill"><span className={`dot ${tone[p.statusTone].dot}`} /> {p.status}</span>
                </td>
                <td>{p.scope}</td>
                <td className="text-body">{p.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
