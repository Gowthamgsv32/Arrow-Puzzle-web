// One bent arrow line, drawn inside the board's SVG (cell units: 1 = one cell).
// Cell (r,c) centre is (c + 0.5, r + 0.5). A wide transparent "hit" path makes
// the thin line easy to tap.

function pathD(verts) {
  return verts.map(([r, c], i) => `${i ? 'L' : 'M'}${c + 0.5},${r + 0.5}`).join(' ')
}

export default function ArrowPath({ arrow, blocked, onClick, aria }) {
  const d = pathD(arrow.verts)
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
          strokeWidth="0.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
      <path
        className="arrow__ink"
        d={d}
        fill="none"
        strokeWidth="0.12"
        strokeLinecap="round"
        strokeLinejoin="round"
        markerEnd="url(#arrowhead)"
      />
    </g>
  )
}

// Shared arrowhead marker (place once per <svg>). Uses context-stroke so the
// head always matches its line's colour (navy / hover / red).
export function ArrowDefs() {
  return (
    <defs>
      <marker
        id="arrowhead"
        markerUnits="userSpaceOnUse"
        markerWidth="0.7"
        markerHeight="0.7"
        refX="0.12"
        refY="0.3"
        orient="auto"
      >
        <path d="M0,0 L0.58,0.3 L0,0.6 Z" fill="context-stroke" />
      </marker>
    </defs>
  )
}
