import { Link } from 'react-router-dom'
import Wordmark from './Wordmark.jsx'

const LINKS = [
  ['Product', '#product'],
  ['Pipeline', '#pipeline'],
  ['Certification', '#certification'],
  ['Evidence', '#evidence'],
]

export default function Nav() {
  return (
    <header className="nav">
      <div className="nav-inner">
        <Wordmark sub="the autonomous casualty office" />
        <nav className="nav-links">
          {LINKS.map(([label, href]) => (
            <a key={href} href={href} className="nav-link">{label}</a>
          ))}
          <Link to="/demo" className="nav-link">Demo</Link>
        </nav>
        <div className="nav-right">
          <Link to="/demo" className="btn btn-primary btn-sm">Open demo account</Link>
        </div>
      </div>
    </header>
  )
}
