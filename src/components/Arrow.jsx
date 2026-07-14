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
        strokeWidth="0.13"
        strokeLinecap="round"
        strokeLinejoin="round"
        markerEnd="url(#snakehead)"
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

// Shared snake-head marker (place once per <svg>). Sits at the line's head and
// rotates to face the way the snake points, with eyes and a forked tongue.
export function ArrowDefs() {
  return (
    <defs>
      <marker
        id="snakehead"
        markerUnits="userSpaceOnUse"
        markerWidth="1.5"
        markerHeight="1.5"
        viewBox="-1 -1 2 2"
        refX="0"
        refY="0"
        orient="auto"
      >
        {/* forked tongue */}
        <path
          d="M0.5,0 L1.05,0 M1.05,0 L1.32,-0.17 M1.05,0 L1.32,0.17"
          stroke="#e23b3b"
          strokeWidth="0.09"
          fill="none"
          strokeLinecap="round"
        />
        {/* head */}
        <ellipse cx="0" cy="0" rx="0.74" ry="0.62" fill="#69c05a" stroke="#3f8f43" strokeWidth="0.09" />
        {/* eyes on both sides */}
        <circle cx="0.14" cy="-0.3" r="0.25" fill="#fff" />
        <circle cx="0.14" cy="0.3" r="0.25" fill="#fff" />
        <circle cx="0.24" cy="-0.3" r="0.12" fill="#1c2b1c" />
        <circle cx="0.24" cy="0.3" r="0.12" fill="#1c2b1c" />
      </marker>
    </defs>
  )
}
