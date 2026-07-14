import { arrowD } from '../game/train.js'

// One bent arrow line, drawn inside the board's SVG (cell units: 1 = one cell).
// Cell (r,c) centre is (c + 0.5, r + 0.5). A wide transparent "hit" path makes
// the thin line easy to tap.

export default function ArrowPath({ arrow, blocked, onClick, aria }) {
  const d = arrowD(arrow)
  return (
    <g
      className={`arrow${blocked ? ' arrow--blocked' : ''}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      aria-label={aria}
      data-id={arrow.id}
      data-dir={arrow.dir}
      data-head={`${arrow.head[0]},${arrow.head[1]}`}
      data-cells={arrow.cells.map((x) => x.join('-')).join(' ')}
    >
      {onClick && (
        <path
          className="arrow__hit"
          d={d}
          fill="none"
          stroke="transparent"
          strokeWidth="0.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
      <path
        className="arrow__ink"
        d={d}
        fill="none"
        strokeWidth="0.09"
        strokeLinecap="round"
        strokeLinejoin="round"
        markerEnd="url(#arrowhead)"
      />
    </g>
  )
}

export function TrainPath({ train }) {
  return (
    <path
      className="train"
      d={train.d}
      style={{
        '--own': train.ownLen,
        '--total': train.total,
        '--dur': `${train.durMs}ms`,
      }}
    />
  )
}

// Shared arrowhead marker (place once per <svg>). Uses context-stroke so the
// head always matches its line's colour.
export function ArrowDefs() {
  return (
    <defs>
      <marker
        id="arrowhead"
        markerUnits="userSpaceOnUse"
        markerWidth="0.55"
        markerHeight="0.55"
        refX="0.1"
        refY="0.25"
        orient="auto"
      >
        <path d="M0,0 L0.5,0.25 L0,0.5 Z" fill="context-stroke" />
      </marker>
    </defs>
  )
}
