import { ARROW_GLYPH } from '../game/constants.js'

/**
 * Renders the grid of arrows plus transient "flying" overlays.
 *
 * @param {object} props
 * @param {object} props.game       current game state
 * @param {Array}  props.flying     [{ id, r, c, dir }] arrows animating off-board
 * @param {?object} props.blocked   { r, c, id } cell currently shaking, or null
 * @param {(r:number,c:number)=>void} props.onCell
 */
export default function Board({ game, flying, blocked, onCell }) {
  const { board, rows, cols } = game

  return (
    <div
      className="board"
      style={{ '--cols': cols, '--rows': rows }}
      role="grid"
      aria-label="Arrow puzzle board"
    >
      {board.map((dir, i) => {
        const r = Math.floor(i / cols)
        const c = i % cols
        const isBlocked = blocked && blocked.r === r && blocked.c === c
        if (!dir) {
          return <div key={i} className="cell cell--empty" role="gridcell" />
        }
        return (
          <button
            key={i}
            role="gridcell"
            className={`cell cell--arrow cell--${dir}${
              isBlocked ? ' cell--blocked' : ''
            }`}
            onClick={() => onCell(r, c)}
            aria-label={`Arrow pointing ${dirWord(dir)} at row ${r + 1}, column ${
              c + 1
            }`}
          >
            <span className="cell__glyph" aria-hidden="true">
              {ARROW_GLYPH[dir]}
            </span>
          </button>
        )
      })}

      {/* Overlay layer: arrows that have just been released fly off-board. */}
      {flying.map(({ id, r, c, dir }) => (
        <span
          key={id}
          className={`fly fly--${dir}`}
          style={{
            left: `${(c / cols) * 100}%`,
            top: `${(r / rows) * 100}%`,
            width: `${100 / cols}%`,
            height: `${100 / rows}%`,
          }}
          aria-hidden="true"
        >
          {ARROW_GLYPH[dir]}
        </span>
      ))}
    </div>
  )
}

function dirWord(dir) {
  return { U: 'up', D: 'down', L: 'left', R: 'right' }[dir]
}
