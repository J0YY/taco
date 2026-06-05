import { useOutletContext } from 'react-router-dom'
import { deriveCertStatus } from '../Dashboard.jsx'
import { tone } from '../../data/stub.js'

export default function ControlsPage() {
  const { controls, toggleControl } = useOutletContext()
  const cert = deriveCertStatus(controls)
  const anyDisabled = controls.some((c) => !c.enabled)

  return (
    <>
      <div className="page-head">
        <h2>Controls</h2>
        <p>Required runtime controls for the conditional certificate. Disabling a control excludes its failure family from the covered deployment scope.</p>
      </div>

      <div className="notice" style={{ borderLeftColor: cert.tone === 'warn' ? 'var(--warn)' : 'var(--risk)' }}>
        <span className={`dot ${tone[cert.tone].dot}`} />
        <span>
          Certification with current controls: <strong className={tone[cert.tone].text}>{cert.label}</strong>
          {anyDisabled && <>. Disabled-control failure families are excluded from the covered deployment scope.</>}
        </span>
      </div>

      <div className="card card-flush">
        {controls.map((c) => (
          <div className="control-row" key={c.id}>
            <div>
              <div className="cname">{c.name}</div>
              <div className="cdesc">{c.desc}</div>
              <div className="caption mono" style={{ marginTop: 6 }}>guards: {c.guards}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span className="caption mono" style={{ color: c.enabled ? 'var(--ok)' : 'var(--risk)' }}>
                {c.enabled ? 'enabled' : 'disabled'}
              </span>
              <button
                className={`toggle ${c.enabled ? 'on' : ''}`}
                role="switch"
                aria-checked={c.enabled}
                aria-label={`toggle ${c.name}`}
                onClick={() => toggleControl(c.id)}
              >
                <span className="knob" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
