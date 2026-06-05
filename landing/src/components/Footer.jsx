import { Link } from 'react-router-dom'
import Wordmark from './Wordmark.jsx'

// Landing-section anchors resolved against the Vite base so they work from any
// page (including /research) and under the GitHub Pages subpath.
const base = import.meta.env.BASE_URL
const sec = (id) => `${base}#${id}`

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div>
          <Wordmark sub="the autonomous casualty office" />
          <p className="caption" style={{ marginTop: 12 }}>
            Pre-deployment certification for robot policies. Taco certifies that a
            specific robot policy version passed a scoped pre-deployment audit under
            defined operating conditions, not that an organization is generically safe.
          </p>
        </div>
        <div className="caption mono footer-links">
          <div className="label-mono" style={{ marginBottom: 8 }}>Product</div>
          <div>
            <a href={sec('product')}>Overview</a> · <a href={sec('pipeline')}>Pipeline</a> · <a href={sec('certification')}>Certification</a> · <a href={sec('evidence')}>Case study</a>
          </div>
          <div className="label-mono" style={{ marginTop: 16, marginBottom: 8 }}>Explore</div>
          <div>
            <Link to="/research">Research</Link> · <Link to="/demo">Dashboard</Link> · <Link to="/demo/binder">Binder</Link>
          </div>
          <div style={{ marginTop: 16 }}>© 2026 Taco</div>
        </div>
      </div>
    </footer>
  )
}
