import ArrowPath, { ArrowDefs, TrainPath } from './Arrow.jsx'

const DIR_WORD = { U: 'up', D: 'down', L: 'left', R: 'right' }

/**
 * Renders the board: all live bent-line arrows in one SVG, plus any that are
 * releasing (sliding out along their own path like a train).
 *
 * @param {object}  props
 * @param {object}  props.game     current game state
 * @param {Array}   props.flying   [{ key, train }] arrows animating off-board
 * @param {?number} props.blocked  id of the arrow currently shaking, or null
 * @param {(id:number)=>void} props.onArrow
 */
export default function Board({ game, flying, blocked, onArrow }) {
  const { arrows, rows, cols } = game

  return (
    <div className="board" style={{ '--cols': cols, '--rows': rows }}>
      <svg
        className="board__svg"
        viewBox={`0 0 ${cols} ${rows}`}
        role="group"
        aria-label="Arrow puzzle board"
      >
        <ArrowDefs />
        {Object.values(arrows).map((arrow) => (
          <ArrowPath
            key={arrow.id}
            arrow={arrow}
            blocked={blocked === arrow.id}
            onClick={() => onArrow(arrow.id)}
            aria={`Snake facing ${DIR_WORD[arrow.dir]}, length ${arrow.cells.length}`}
          />
        ))}
        {flying.map(({ key, train }) => (
          <TrainPath key={key} train={train} />
        ))}
      </svg>
    </div>
  )
}
