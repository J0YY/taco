import { useOutletContext, useNavigate } from 'react-router-dom'
import { CERTIFICATE, tone } from '../../data/stub.js'
import { deriveCertStatus } from '../Dashboard.jsx'

export default function Certification() {
  const navigate = useNavigate()
  const { controls } = useOutletContext()
  const cert = deriveCertStatus(controls)
  const enabledCount = controls.filter((c) => c.enabled).length

  return (
    <>
      <div className="page-head">
        <h2>Certification</h2>
        <p>The primary Taco artifact: a policy-version certificate scoped to a deployment, conditional on required controls and re-audit triggers.</p>
      </div>

      <div className="cert-seal" style={{ marginBottom: 24 }}>
        <div className="cert-seal-head">
          <div>
            <div className="label-mono">Taco Policy-Version Certificate</div>
            <div className="display-sm" style={{ marginTop: 4 }}>{cert.label}</div>
          </div>
          <span className="cert-seal-stamp" style={{ color: tone[cert.tone].text.includes('warn') ? 'var(--warn)' : 'var(--risk)', borderColor: cert.tone === 'warn' ? 'var(--warn)' : 'var(--risk)' }}>
            {cert.tone === 'warn' ? 'conditional' : 'exclusion'}
          </span>
        </div>
        <div className="cert-seal-body">
          <div className="kv-list">
            <div className="row"><span className="k">status</span><span className={`v ${tone[cert.tone].text}`}>{cert.label}</span></div>
            <div className="row"><span className="k">policy</span><span className="v mono">{CERTIFICATE.policy}</span></div>
            <div className="row"><span className="k">organization</span><span className="v">{CERTIFICATE.organization}</span></div>
            <div className="row"><span className="k">deployment scope</span><span className="v">{CERTIFICATE.deploymentScope}</span></div>
            <div className="row"><span className="k">known failure families</span><span className="v">{CERTIFICATE.knownFailureFamilies}</span></div>
            <div className="row"><span className="k">required controls</span><span className="v">{enabledCount} / {CERTIFICATE.requiredControls} enabled</span></div>
            <div className="row"><span className="k">residual risk</span><span className="v text-warn">{CERTIFICATE.residualRisk}</span></div>
            <div className="row"><span className="k">certificate validity</span><span className="v">{CERTIFICATE.validity}</span></div>
          </div>
        </div>
      </div>

      <div className="section-block">
        <div className="label-mono" style={{ marginBottom: 12 }}>model-card / procurement snippet</div>
        <div className="terminal">
          <div className="terminal-bar"><span className="tcap" /><span className="tcap" /><span className="tcap" /><span style={{ marginLeft: 6 }}>model_card.md</span></div>
          <div className="terminal-body" style={{ lineHeight: 1.8, color: 'var(--body-strong)' }}>
            <div className="text-ok">Taco Audited — {cert.label}</div>
            <div style={{ marginTop: 8 }}>
              This robot policy was audited against visual occlusion, language override,
              and semantic distractor failure families. Required runtime controls must
              remain enabled. Re-audit required after policy updates or deployment-scope
              changes.
            </div>
          </div>
        </div>
      </div>

      <button className="btn btn-primary btn-sm" onClick={() => navigate('/demo/binder')}>View underwriting binder →</button>
    </>
  )
}
