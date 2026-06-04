import { BINDER } from '../../data/stub.js'

export default function Binder() {
  return (
    <>
      <div className="page-head">
        <h2>Binder</h2>
        <p>A downstream underwriting artifact derived from the audit evidence — not the product itself. Insurance becomes possible once the evidence layer exists.</p>
      </div>

      <div className="binder">
        <div className="binder-head">
          <div>
            <div className="label-mono">underwriting artifact</div>
            <div className="display-sm" style={{ marginTop: 4 }}>{BINDER.product}</div>
          </div>
          <span className="status-pill"><span className="dot dot-warn" /> {BINDER.status}</span>
        </div>
        <div className="binder-body">
          <div className="subgrid-cards" style={{ marginBottom: 24 }}>
            <div className="kv-list">
              <div className="row"><span className="k">named insured</span><span className="v">{BINDER.namedInsured}</span></div>
              <div className="row"><span className="k">coverage type</span><span className="v">{BINDER.coverageType}</span></div>
              <div className="row"><span className="k">coverage limit</span><span className="v">{BINDER.coverageLimit}</span></div>
              <div className="row"><span className="k">status</span><span className="v text-warn">{BINDER.status}</span></div>
            </div>
            <div className="card" style={{ background: 'var(--canvas-softer)' }}>
              <div className="label-mono">monthly premium</div>
              <div className="binder-amt" style={{ marginTop: 8 }}>{BINDER.monthlyPremium}</div>
              <div className="caption" style={{ marginTop: 6 }}>conditional on required controls remaining enabled</div>
            </div>
          </div>

          <div className="section-block">
            <span className="label-mono">required controls</span>
            <div className="chip-grid">
              {BINDER.requiredControls.map((c) => (
                <span className="chip" key={c}><span className="dot dot-ok" /> {c}</span>
              ))}
            </div>
          </div>

          <div className="section-block" style={{ marginBottom: 0 }}>
            <span className="label-mono">known exclusions</span>
            {BINDER.exclusions.map((e) => (
              <div className="notice" key={e} style={{ borderLeftColor: 'var(--risk)', marginBottom: 0 }}>
                <span className="dot dot-risk" />
                <span>{e}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}
