import { Link } from 'react-router-dom'
import Wordmark from './Wordmark.jsx'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div>
          <Wordmark sub="the autonomous casualty office" />
          <p className="caption" style={{ marginTop: 12 }}>
            Pre-deployment certification for robot policies. Taco certifies that a
            specific robot policy version passed a scoped pre-deployment audit under
            defined operating conditions — not that an organization is generically safe.
          </p>
        </div>
        <div className="caption mono footer-links">
          <div>
            <a href="/#product">Product</a> · <a href="/#pipeline">Pipeline</a> · <a href="/#certification">Certification</a>
          </div>
          <div>
            <a href="/#evidence">Evidence</a> · <Link to="/demo/binder">Binder</Link> · <Link to="/demo">Demo</Link>
          </div>
          <div style={{ marginTop: 12 }}>© 2026 Taco</div>
        </div>
      </div>
    </footer>
  )
}
