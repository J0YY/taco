import { useNavigate } from 'react-router-dom'
import { FAILURE_CERTS, tone } from '../../data/stub.js'

const asset = (p) => `${import.meta.env.BASE_URL}${String(p).replace(/^\//, '')}`

const REPLAYS = [
  { tone: 'dot-ok', lbl: 'Native success', src: '/videos/native_success_cropped.gif' },
  { tone: 'dot-risk', lbl: 'Counterfactual failure', src: '/videos/counter_fail_cropped.gif' },
  { tone: 'dot-ok', lbl: 'Mitigated replay', src: '/videos/mitigate_cropped.gif' },
]

export default function FailureEvidence() {
  const navigate = useNavigate()
  const fr1 = FAILURE_CERTS[0]
  const others = FAILURE_CERTS.slice(1)

  return (
    <>
      <div className="page-head">
        <h2>Failure Evidence</h2>
        <p>Simulation-validated, replayable failure certificates for skild_vla_warehouse_v1. Each is reproducible from its replay command.</p>
      </div>

      <div className="section-block">
        <div className="kicker-row">
          <span className="status-pill"><span className="dot dot-risk" /> {fr1.id}</span>
          <span className="display-sm">{fr1.title}</span>
        </div>

        <div className="replay-grid" style={{ marginBottom: 20 }}>
          {REPLAYS.map((r) => (
            <div className="card replay-card" key={r.lbl}>
              <div className="replay-head"><span className="lbl">{r.lbl}</span><span className={`dot ${r.tone}`} /></div>
              <div className="replay-scene">
                <img src={asset(r.src)} alt={r.lbl}
                     style={{ width: '100%', display: 'block', background: '#221e1b', aspectRatio: '16 / 10', objectFit: 'cover' }} />
              </div>
            </div>
          ))}
        </div>

        <div className="cert-seal">
          <div className="cert-seal-head">
            <span className="label-mono">certificate details</span>
            <span className="status-pill mono">{fr1.id}</span>
          </div>
          <div className="cert-seal-body">
            <div className="kv-list">
              <div className="row"><span className="k">certificate id</span><span className="v mono">{fr1.id}</span></div>
              <div className="row"><span className="k">policy</span><span className="v mono">{fr1.policy}</span></div>
              <div className="row"><span className="k">task</span><span className="v">{fr1.task}</span></div>
              <div className="row"><span className="k">native rollout</span><span className="v text-ok">{fr1.nativeRollout}</span></div>
              <div className="row"><span className="k">perturbation</span><span className="v">{fr1.perturbation}</span></div>
              <div className="row"><span className="k">failure</span><span className="v text-risk">{fr1.failure}</span></div>
              <div className="row"><span className="k">minimality</span><span className="v">{fr1.minimality}</span></div>
              <div className="row"><span className="k">patch recipe</span><span className="v text-ok">{fr1.patchRecipe}</span></div>
              <div className="row"><span className="k">required control</span><span className="v">{fr1.requiredControl}</span></div>
            </div>
            <div style={{ marginTop: 18 }}>
              <button className="btn btn-secondary btn-sm" onClick={() => navigate('/demo/internal-traces')}>
                View internal trace →
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="label-mono" style={{ marginBottom: 12 }}>Other failure families</div>
      <div className="subgrid-cards">
        {others.map((c) => (
          <div className="card" key={c.id}>
            <div className="kicker-row" style={{ marginBottom: 10 }}>
              <span className="status-pill mono"><span className={`dot ${tone[c.tone].dot}`} /> {c.id}</span>
            </div>
            <div className="card-title">{c.title}</div>
            <div className="kv-list" style={{ marginTop: 12 }}>
              <div className="row"><span className="k">perturbation</span><span className="v">{c.perturbation}</span></div>
              <div className="row"><span className="k">failure</span><span className="v text-risk">{c.failure}</span></div>
              <div className="row"><span className="k">control</span><span className="v">{c.requiredControl}</span></div>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
