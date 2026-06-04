import { POLICIES, tone } from '../../data/stub.js'

export default function Policies() {
  const primary = POLICIES[0]
  return (
    <>
      <div className="page-head">
        <h2>Policies</h2>
        <p>Robot policies registered for pre-deployment audit. Certification is issued per policy version and invalidated on model update.</p>
      </div>

      <div className="section-block">
        <div className="cert-seal" style={{ marginBottom: 24 }}>
          <div className="cert-seal-head">
            <div>
              <div className="label-mono">policy detail</div>
              <div className="display-sm mono" style={{ marginTop: 4 }}>{primary.id}</div>
            </div>
            <span className="status-pill"><span className={`dot ${tone[primary.statusTone].dot}`} /> {primary.status}</span>
          </div>
          <div className="cert-seal-body">
            <div className="kv-list">
              <div className="row"><span className="k">model family</span><span className="v">{primary.modelFamily}</span></div>
              <div className="row"><span className="k">deployment scope</span><span className="v">{primary.deploymentScope}</span></div>
              <div className="row"><span className="k">robot type</span><span className="v">{primary.robotType}</span></div>
              <div className="row"><span className="k">certification</span><span className={`v ${tone[primary.statusTone].text}`}>{primary.status}</span></div>
              <div className="row"><span className="k">valid until</span><span className="v">{primary.validUntil}</span></div>
            </div>
          </div>
        </div>
      </div>

      <div className="label-mono" style={{ marginBottom: 12 }}>All policies</div>
      <div className="card card-flush">
        <table className="table">
          <thead>
            <tr><th className="mono">policy</th><th>status</th><th>deployment scope</th><th>notes</th></tr>
          </thead>
          <tbody>
            {POLICIES.map((p) => (
              <tr key={p.id}>
                <td className="mono">{p.id}</td>
                <td><span className="status-pill"><span className={`dot ${tone[p.statusTone].dot}`} /> {p.status}</span></td>
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
