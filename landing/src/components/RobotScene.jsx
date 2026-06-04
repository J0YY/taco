// Schematic side-view of a manipulation cell: gantry rail, gripper, two objects
// (target mug + distractor), a plate. Three variants tell the FR-001 story.
// Deliberately diagrammatic — no cartoon mascots.

const C = {
  line: '#4d4641',
  faint: '#3f3a36',
  ink: '#f7f5f0',
  body: '#c9c0ad',
  mute: '#aea69c',
  ok: '#9db58f',
  warn: '#d8b46a',
  risk: '#cf8f7a',
  panel: '#221e1b',
}

function Grid() {
  const lines = []
  for (let x = 20; x < 320; x += 20) {
    lines.push(<line key={`v${x}`} x1={x} y1={0} x2={x} y2={200} stroke={C.faint} strokeWidth="0.5" opacity="0.4" />)
  }
  for (let y = 20; y < 200; y += 20) {
    lines.push(<line key={`h${y}`} x1={0} y1={y} x2={320} y2={y} stroke={C.faint} strokeWidth="0.5" opacity="0.4" />)
  }
  return <g>{lines}</g>
}

function Arm({ x, color = C.body }) {
  // gantry rail at top + vertical actuator + gripper jaws
  return (
    <g>
      <line x1="20" y1="34" x2="300" y2="34" stroke={C.line} strokeWidth="3" strokeLinecap="round" />
      <rect x={x - 9} y="30" width="18" height="9" fill={C.panel} stroke={C.line} strokeWidth="1" />
      <line x1={x} y1="39" x2={x} y2="92" stroke={color} strokeWidth="2.5" />
      <rect x={x - 11} y="92" width="22" height="9" fill={C.panel} stroke={color} strokeWidth="1.5" />
      <line x1={x - 8} y1="101" x2={x - 8} y2="116" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
      <line x1={x + 8} y1="101" x2={x + 8} y2="116" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
    </g>
  )
}

function Mug({ x, label, color, dim }) {
  return (
    <g opacity={dim ? 0.4 : 1}>
      <rect x={x - 13} y="150" width="26" height="22" rx="1.5" fill="none" stroke={color} strokeWidth="2" />
      <path d={`M ${x + 13} 154 q 9 2 9 9 q 0 7 -9 9`} fill="none" stroke={color} strokeWidth="2" />
      {label && (
        <text x={x} y="186" fontFamily="DM Mono, monospace" fontSize="8" fill={C.mute} textAnchor="middle">
          {label}
        </text>
      )}
    </g>
  )
}

function Plate({ x }) {
  return (
    <g>
      <ellipse cx={x} cy="174" rx="30" ry="6" fill="none" stroke={C.body} strokeWidth="1.5" />
      <ellipse cx={x} cy="172" rx="22" ry="4" fill="none" stroke={C.mute} strokeWidth="1" opacity="0.6" />
    </g>
  )
}

function Floor() {
  return <line x1="10" y1="180" x2="310" y2="180" stroke={C.line} strokeWidth="1" />
}

/**
 * variant: 'native' | 'failure' | 'mitigated'
 */
export default function RobotScene({ variant = 'native' }) {
  return (
    <svg viewBox="0 0 320 200" width="100%" role="img" aria-label={`replay scene: ${variant}`}>
      <rect x="0" y="0" width="320" height="200" fill={C.panel} />
      <Grid />
      <Floor />
      <Plate x="240" />

      {variant === 'native' && (
        <>
          {/* arm carries the correct (target) mug toward the plate */}
          <Arm x="200" color={C.ok} />
          <Mug x="200" label="target" color={C.ok} />
          <Mug x="90" label="distractor" color={C.body} dim />
          {/* motion arrow toward plate */}
          <path d="M 214 130 q 18 8 24 28" fill="none" stroke={C.ok} strokeWidth="1.5" strokeDasharray="3 3" />
          <path d="M 238 158 l 1 -8 l -6 4 z" fill={C.ok} />
        </>
      )}

      {variant === 'failure' && (
        <>
          {/* occlusion band over the target; arm reaches the distractor */}
          <Arm x="90" color={C.risk} />
          <Mug x="200" label="target" color={C.body} dim />
          <Mug x="90" label="distractor" color={C.risk} />
          <rect x="170" y="120" width="64" height="64" fill={C.warn} opacity="0.16" />
          <rect x="170" y="120" width="64" height="64" fill="none" stroke={C.warn} strokeWidth="1" strokeDasharray="4 3" opacity="0.7" />
          <text x="202" y="116" fontFamily="DM Mono, monospace" fontSize="7.5" fill={C.warn} textAnchor="middle">
            occlusion 31%
          </text>
          <path d="M 90 130 l 0 14" fill="none" stroke={C.risk} strokeWidth="1.5" strokeDasharray="3 3" />
          <path d="M 90 150 l -3 -7 l 6 0 z" fill={C.risk} />
        </>
      )}

      {variant === 'mitigated' && (
        <>
          {/* monitor fires; arm pauses above target, requests second view */}
          <Arm x="200" color={C.warn} />
          <Mug x="200" label="target" color={C.ok} />
          <Mug x="90" label="distractor" color={C.body} dim />
          <rect x="170" y="120" width="64" height="64" fill={C.warn} opacity="0.1" />
          <rect x="170" y="120" width="64" height="64" fill="none" stroke={C.warn} strokeWidth="1" strokeDasharray="4 3" opacity="0.5" />
          {/* second-view camera glyph */}
          <g>
            <rect x="262" y="60" width="22" height="14" rx="1.5" fill={C.panel} stroke={C.ok} strokeWidth="1.5" />
            <circle cx="273" cy="67" r="3.5" fill="none" stroke={C.ok} strokeWidth="1.5" />
            <path d="M 262 67 q -16 0 -42 48" fill="none" stroke={C.ok} strokeWidth="1.2" strokeDasharray="3 3" />
          </g>
          <text x="202" y="116" fontFamily="DM Mono, monospace" fontSize="7.5" fill={C.ok} textAnchor="middle">
            2nd view requested
          </text>
          {/* hold indicator */}
          <text x="200" y="132" fontFamily="DM Mono, monospace" fontSize="7" fill={C.warn} textAnchor="middle">
            ‖ hold
          </text>
        </>
      )}
    </svg>
  )
}
