import { REAL_TRACE as TRACE } from '../data/realTrace.js'

// Perfetto-style internal-trace viewer rendered as a single SVG so the
// warning/failure marker lines align across every lane.

const TONE = {
  ink: '#f7f5f0',
  body: '#aea69c',
  warn: '#d8b46a',
  risk: '#cf8f7a',
  ok: '#9db58f',
}

const W = 760
const GUTTER = 196
const PLOT_X0 = GUTTER + 14
const PLOT_W = W - PLOT_X0 - 24
const AXIS_H = 40
const ROW_H = 30
const ROW_GAP = 4

export default function TraceViewer({ compact = false }) {
  const rows = TRACE.rows
  const plotTop = AXIS_H
  const H = plotTop + rows.length * (ROW_H + ROW_GAP) + 16

  const tToX = (t) => PLOT_X0 + (t / TRACE.duration) * PLOT_W
  const warnX = tToX(TRACE.warningT)
  const failX = tToX(TRACE.failureT)

  const seriesPath = (series, rowTop) => {
    const n = series.length
    const innerH = ROW_H - 8
    return series.map((v, i) => {
      const x = PLOT_X0 + (i / (n - 1)) * PLOT_W
      const y = rowTop + 4 + (1 - v) * innerH
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
    }).join(' ')
  }

  const areaPath = (series, rowTop) => {
    const n = series.length
    const innerH = ROW_H - 8
    const base = rowTop + 4 + innerH
    let d = `M ${PLOT_X0} ${base}`
    series.forEach((v, i) => {
      const x = PLOT_X0 + (i / (n - 1)) * PLOT_W
      const y = rowTop + 4 + (1 - v) * innerH
      d += ` L ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    d += ` L ${PLOT_X0 + PLOT_W} ${base} Z`
    return d
  }

  return (
    <div className="trace-viewer">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="internal risk trace timeline">
        {/* axis ticks */}
        {[0, 0.5, 1, 1.5, 2, 2.5, 3].map((t) => {
          const x = tToX(t)
          return (
            <g key={t}>
              <line x1={x} y1={AXIS_H - 8} x2={x} y2={H - 10} stroke="#3f3a36" strokeWidth="0.5" opacity="0.5" />
              <text x={x} y={AXIS_H - 14} fontFamily="DM Mono, monospace" fontSize="9" fill="#aea69c" textAnchor="middle">
                {t.toFixed(1)}s
              </text>
            </g>
          )
        })}

        {/* warning + failure marker bands */}
        <line x1={warnX} y1={AXIS_H - 8} x2={warnX} y2={H - 10} stroke="#d8b46a" strokeWidth="1" strokeDasharray="4 3" opacity="0.85" />
        <line x1={failX} y1={AXIS_H - 8} x2={failX} y2={H - 10} stroke="#cf8f7a" strokeWidth="1.2" opacity="0.9" />
        <rect x={warnX} y={AXIS_H - 8} width={failX - warnX} height={H - 10 - (AXIS_H - 8)} fill="#d8b46a" opacity="0.06" />
        <text x={warnX + 4} y={AXIS_H - 24} fontFamily="DM Mono, monospace" fontSize="9" fill="#d8b46a">
          ▲ risk threshold crossed
        </text>
        <text x={failX - 4} y={AXIS_H - 24} fontFamily="DM Mono, monospace" fontSize="9" fill="#cf8f7a" textAnchor="end">
          physical failure ▼
        </text>

        {/* rows */}
        {rows.map((row, idx) => {
          const rowTop = plotTop + idx * (ROW_H + ROW_GAP)
          const color = TONE[row.tone] || TONE.body
          return (
            <g key={row.key}>
              {/* lane background */}
              <rect x={PLOT_X0} y={rowTop} width={PLOT_W} height={ROW_H} fill="#252118" opacity="0.5" />
              <line x1={0} y1={rowTop + ROW_H + ROW_GAP / 2} x2={W} y2={rowTop + ROW_H + ROW_GAP / 2} stroke="#3f3a36" strokeWidth="0.5" opacity="0.4" />

              {/* label */}
              <text x={14} y={rowTop + ROW_H / 2 + 3.5} fontFamily="DM Mono, monospace" fontSize="11" fill={row.tone === 'ink' ? '#f7f5f0' : '#c9c0ad'}>
                {row.label}
              </text>

              {row.kind === 'predicate' ? (
                <>
                  <path d={areaPath(row.series, rowTop)} fill={color} opacity="0.18" />
                  <path d={seriesPath(row.series, rowTop)} fill="none" stroke={color} strokeWidth="1.5" />
                  <text x={PLOT_X0 + PLOT_W - 4} y={rowTop + 12} fontFamily="DM Mono, monospace" fontSize="8" fill={color} textAnchor="end">
                    risk_predicate
                  </text>
                </>
              ) : row.kind === 'feature' ? (
                <path d={seriesPath(row.series, rowTop)} fill="none" stroke={color} strokeWidth="1.6" strokeLinejoin="round" />
              ) : (
                <>
                  <path d={areaPath(row.series, rowTop)} fill={color} opacity="0.16" />
                  <path d={seriesPath(row.series, rowTop)} fill="none" stroke={color} strokeWidth="1.6" />
                  {row.threshold != null && (
                    <line
                      x1={PLOT_X0} y1={rowTop + 4 + (1 - row.threshold) * (ROW_H - 8)}
                      x2={PLOT_X0 + PLOT_W} y2={rowTop + 4 + (1 - row.threshold) * (ROW_H - 8)}
                      stroke={color} strokeWidth="0.75" strokeDasharray="3 3" opacity="0.7"
                    />
                  )}
                </>
              )}
            </g>
          )
        })}
      </svg>

      {!compact && (
        <div className="trace-legend">
          <span><span className="dot dot-warn" /> internal risk threshold crossed at {TRACE.warningT.toFixed(2)}s</span>
          <span><span className="dot dot-risk" /> episode failed at {TRACE.failureT.toFixed(2)}s</span>
          <span className="mono text-mute">lead time {TRACE.leadLabel}</span>
        </div>
      )}
      {!compact && (
        <div className="label-mono" style={{ marginTop: 10, fontSize: 11, color: 'var(--text-mute)' }}>
          REAL captured internals · {TRACE.source}
        </div>
      )}
    </div>
  )
}
