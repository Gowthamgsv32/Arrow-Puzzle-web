import Arrow from './Arrow.jsx'

const DIR_WORD = { U: 'up', D: 'down', L: 'left', R: 'right' }

/**
 * Renders the board: all live arrows plus any that are currently flying off.
 *
 * @param {object}  props
 * @param {object}  props.game     current game state
 * @param {Array}   props.flying   [{ key, arrow }] arrows animating off-board
 * @param {?number} props.blocked  id of the arrow currently shaking, or null
 * @param {(id:number)=>void} props.onArrow
 */
export default function Board({ game, flying, blocked, onArrow }) {
  const { arrows, rows, cols } = game

  return (
    <div
      className="board"
      style={{ '--cols': cols, '--rows': rows }}
      role="group"
      aria-label="Arrow puzzle board"
    >
      {Object.values(arrows).map((arrow) => (
        <Arrow
          key={arrow.id}
          arrow={arrow}
          rows={rows}
          cols={cols}
          blocked={blocked === arrow.id}
          onClick={() => onArrow(arrow.id)}
          aria={`Arrow pointing ${DIR_WORD[arrow.dir]}, length ${arrow.len}`}
        />
      ))}

      {flying.map(({ key, arrow }) => (
        <span key={key} className={`fly fly--${arrow.dir}`} aria-hidden="true">
          <Arrow arrow={arrow} rows={rows} cols={cols} onClick={() => {}} />
        </span>
      ))}
    </div>
  )
}
