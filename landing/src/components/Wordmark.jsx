import { Link } from 'react-router-dom'

// Taco wordmark — an institutional diamond glyph + monospace lockup.
export default function Wordmark({ to = '/', sub }) {
  return (
    <Link to={to} className="wordmark" aria-label="Taco — The Autonomous Casualty Office">
      <span className="wordmark-glyph" aria-hidden="true">◈</span>
      <span className="wordmark-text">
        <span className="wordmark-name">taco</span>
        {sub && <span className="wordmark-sub">{sub}</span>}
      </span>
    </Link>
  )
}
