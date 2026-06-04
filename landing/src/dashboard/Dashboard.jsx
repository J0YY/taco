import { useState } from 'react'
import { Routes, Route, NavLink, useOutletContext, Outlet, Navigate } from 'react-router-dom'
import Wordmark from '../components/Wordmark.jsx'
import { ACCOUNT, CONTROLS } from '../data/stub.js'

import Overview from './pages/Overview.jsx'
import Policies from './pages/Policies.jsx'
import AuditRuns from './pages/AuditRuns.jsx'
import FailureEvidence from './pages/FailureEvidence.jsx'
import InternalTraces from './pages/InternalTraces.jsx'
import ControlsPage from './pages/Controls.jsx'
import Certification from './pages/Certification.jsx'
import Binder from './pages/Binder.jsx'

const NAV = [
  ['Overview', ''],
  ['Policies', 'policies'],
  ['Audit Runs', 'audit-runs'],
  ['Failure Evidence', 'failure-evidence'],
  ['Internal Traces', 'internal-traces'],
  ['Controls', 'controls'],
  ['Certification', 'certification'],
  ['Binder', 'binder'],
]

// Certification degrades when any required control is disabled.
export function deriveCertStatus(controls) {
  const allOn = controls.every((c) => c.enabled)
  return allOn
    ? { label: 'Conditional Pass', tone: 'warn' }
    : { label: 'Pass with Exclusion', tone: 'risk' }
}

function Shell() {
  const ctx = useOutletContext()
  const cert = deriveCertStatus(ctx.controls)
  return (
    <div className="dash">
      <aside className="dash-side">
        <div className="dash-side-head">
          <Wordmark to="/" sub="audit console" />
        </div>
        <nav className="dash-nav">
          {NAV.map(([label, path]) => (
            <NavLink key={path} to={`/demo/${path}`} end={path === ''}
              className={({ isActive }) => (isActive ? 'active' : '')}>
              <span>{label}</span>
              {label === 'Certification' && (
                <span className="badge">{cert.tone === 'warn' ? 'cond.' : 'excl.'}</span>
              )}
              {label === 'Failure Evidence' && <span className="badge">3</span>}
            </NavLink>
          ))}
        </nav>
        <div className="dash-side-foot">
          <NavLink to="/" className="caption mono" style={{ display: 'block' }}>← back to taco.site</NavLink>
        </div>
      </aside>

      <div className="dash-main">
        <header className="dash-header">
          <div>
            <h1>{ACCOUNT.name}</h1>
            <div className="caption" style={{ marginTop: 2 }}>{ACCOUNT.kind}</div>
            <div style={{ marginTop: 10 }}>
              <span className="status-pill"><span className="dot dot-ok" /> Org status: {ACCOUNT.orgStatus}</span>
            </div>
          </div>
          <div className="dash-header-stats">
            <div className="dash-stat"><div className="k text-mute caption">Active certifications</div><div className="v">{ACCOUNT.activeCertifications}</div></div>
            <div className="dash-stat"><div className="k text-mute caption">Pending audits</div><div className="v">{ACCOUNT.pendingAudits}</div></div>
            <div className="dash-stat"><div className="k text-mute caption">Remediation required</div><div className="v text-risk">{ACCOUNT.remediationRequired}</div></div>
          </div>
        </header>
        <main className="dash-content">
          <Outlet context={ctx} />
        </main>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [controls, setControls] = useState(CONTROLS)
  const toggleControl = (id) =>
    setControls((cs) => cs.map((c) => (c.id === id ? { ...c, enabled: !c.enabled } : c)))
  const ctx = { controls, toggleControl }

  return (
    <Routes>
      <Route element={<OutletProvider ctx={ctx} />}>
        <Route element={<Shell />}>
          <Route index element={<Overview />} />
          <Route path="policies" element={<Policies />} />
          <Route path="audit-runs" element={<AuditRuns />} />
          <Route path="failure-evidence" element={<FailureEvidence />} />
          <Route path="internal-traces" element={<InternalTraces />} />
          <Route path="controls" element={<ControlsPage />} />
          <Route path="certification" element={<Certification />} />
          <Route path="binder" element={<Binder />} />
          <Route path="*" element={<Navigate to="/demo" replace />} />
        </Route>
      </Route>
    </Routes>
  )
}

// Thin wrapper so nested routes share the controls context via Outlet.
function OutletProvider({ ctx }) {
  return <Outlet context={ctx} />
}
