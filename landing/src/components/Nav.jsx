import { Link, useLocation } from 'react-router-dom'
import Wordmark from './Wordmark.jsx'
import MonitorIcon from './MonitorIcon.jsx'

const LANDING_LINKS = [
  ['Product', '#product'],
  ['Pipeline', '#pipeline'],
  ['Certification', '#certification'],
]
const RESEARCH_LINKS = [
  ['Explainer', '#explainer'],
  ['DreamAudit', '#dreamaudit'],
  ['Policies', '#policies'],
]

export default function Nav() {
  const { pathname } = useLocation()
  const onResearch = pathname.startsWith('/research')
  const links = onResearch ? RESEARCH_LINKS : LANDING_LINKS

  return (
    <header className="nav">
      <div className="nav-inner">
        <Wordmark sub="the autonomous casualty office" />
        <nav className="nav-links">
          {links.map(([label, href]) => (
            <a key={href} href={href} className="nav-link">{label}</a>
          ))}
        </nav>
        <div className="nav-right">
          {onResearch
            ? <Link to="/" className="btn btn-secondary btn-sm">Home</Link>
            : <Link to="/research" className="btn btn-secondary btn-sm">Research</Link>}
          <Link to="/demo" className="btn btn-primary btn-sm"><MonitorIcon size={14} /> Dashboard</Link>
        </div>
      </div>
    </header>
  )
}
