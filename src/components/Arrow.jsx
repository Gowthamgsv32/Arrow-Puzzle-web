import { DIRS } from '../game/constants.js'
import { boundingBox } from '../game/engine.js'

// Renders one lengthy arrow (rounded shaft + arrowhead) positioned over the
// board. Coordinates are in *cell units*; the SVG viewBox matches the piece's
// bounding box so it scales uniformly with the square grid.
export default function Arrow({ arrow, rows, cols, blocked, onClick, aria }) {
  const { minR, minC, spanR, spanC } = boundingBox(arrow)
  const { dir } = arrow
  const [dr, dc] = DIRS[dir]

  // Head cell centre, expressed inside the bounding box (unit = 1 cell).
  const headX = arrow.c - minC + 0.5
  const headY = arrow.r - minR + 0.5

  // Shaft runs from the back of the tail cell up to the arrowhead's neck, so
  // even a length-1 arrow shows a proper shaft (no stray round nub).
  const back = arrow.len - 1 + 0.32
  const tailX = headX - dc * back
  const tailY = headY - dr * back
  const neckX = headX - dc * 0.1
  const neckY = headY - dr * 0.1

  // Arrowhead: an isosceles triangle around the tip, base perpendicular to dir.
  const tipX = headX + dc * 0.4
  const tipY = headY + dr * 0.4
  const px = -dr // perpendicular vector (rotate dir 90°)
  const py = dc
  const half = 0.4
  const baseX = headX - dc * 0.12
  const baseY = headY - dr * 0.12
  const p1 = `${tipX},${tipY}`
  const p2 = `${baseX + px * half},${baseY + py * half}`
  const p3 = `${baseX - px * half},${baseY - py * half}`

  const stroke = 0.44

  return (
    <button
      type="button"
      className={`arrow${blocked ? ' arrow--blocked' : ''}`}
      onClick={onClick}
      aria-label={aria}
      data-id={arrow.id}
      data-dir={arrow.dir}
      data-len={arrow.len}
      data-r={arrow.r}
      data-c={arrow.c}
      style={{
        left: `${(minC / cols) * 100}%`,
        top: `${(minR / rows) * 100}%`,
        width: `${(spanC / cols) * 100}%`,
        height: `${(spanR / rows) * 100}%`,
      }}
    >
      <svg
        className="arrow__svg"
        viewBox={`0 0 ${spanC} ${spanR}`}
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
      >
        <g className="arrow__ink">
          <line
            x1={tailX}
            y1={tailY}
            x2={neckX}
            y2={neckY}
            strokeWidth={stroke}
            strokeLinecap="round"
          />
          <polygon points={`${p1} ${p2} ${p3}`} />
        </g>
      </svg>
    </button>
  )
}
