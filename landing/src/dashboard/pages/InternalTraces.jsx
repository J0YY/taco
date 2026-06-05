import { useNavigate } from 'react-router-dom'
import TraceViewer from '../../components/TraceViewer.jsx'
import { TRACE } from '../../data/stub.js'

export default function InternalTraces() {
  const navigate = useNavigate()
  return (
    <>
      <div className="page-head">
        <h2>Internal Traces</h2>
        <p>Activation-level profiler for FR-001. Recorded across native success, counterfactual failure, and mitigated replay. Shown: the counterfactual-failure window.</p>
      </div>

      <div className="kicker-row" style={{ marginBottom: 16 }}>
        <span className="status-pill mono"><span className="dot dot-risk" /> FR-001</span>
        <span className="caption mono">{TRACE.windowLabel}</span>
      </div>

      <TraceViewer />

      <div className="notice" style={{ marginTop: 20, borderLeftColor: 'var(--warn)' }}>
        <span className="dot dot-warn" />
        <span>Risk signature detected <strong>0.82s before physical failure</strong>. The target feature collapses while the memorized-trajectory feature rises. Internal risk crosses threshold before the wrong grasp.</span>
      </div>

      <div className="subgrid-cards" style={{ marginTop: 24 }}>
        <div className="card">
          <div className="label-mono" style={{ marginBottom: 12 }}>signature summary</div>
          <div className="kv-list">
            <div className="row"><span className="k">target_feature</span><span className="v text-risk">collapses 0.82s pre-failure</span></div>
            <div className="row"><span className="k">memorized_traj.</span><span className="v text-warn">rises into dominance</span></div>
            <div className="row"><span className="k">internal_risk</span><span className="v text-warn">crosses 0.50 at t=1.9s</span></div>
            <div className="row"><span className="k">predicate</span><span className="v text-risk">wrong_object_grasp @ 2.72s</span></div>
          </div>
        </div>
        <div className="card">
          <div className="label-mono" style={{ marginBottom: 12 }}>monitor performance</div>
          <div className="kv-list">
            <div className="row"><span className="k">lead time</span><span className="v">0.82s</span></div>
            <div className="row"><span className="k">intervention</span><span className="v text-ok">request second view</span></div>
            <div className="row"><span className="k">mitigated outcome</span><span className="v text-ok">wrong grasp avoided</span></div>
            <div className="row"><span className="k">required control</span><span className="v">occlusion risk monitor</span></div>
          </div>
          <div style={{ marginTop: 16 }}>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate('/demo/certification')}>View certificate →</button>
          </div>
        </div>
      </div>
    </>
  )
}
