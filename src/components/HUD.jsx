import { STARTING_LIVES } from '../game/constants.js'
import { shapeLabel } from '../game/generator.js'

function Hearts({ lives }) {
  return (
    <div className="hud__hearts" aria-label={`${lives} lives left`}>
      {Array.from({ length: STARTING_LIVES }, (_, i) => (
        <span
          key={i}
          className={`hud__heart${i < lives ? '' : ' hud__heart--lost'}`}
          aria-hidden="true"
        >
          {i < lives ? '❤️' : '🤍'}
        </span>
      ))}
    </div>
  )
}

export default function HUD({ level, arrows, lives, shape, onRestart }) {
  return (
    <header className="hud">
      <div className="hud__top">
        <button
          className="hud__icon-btn"
          onClick={onRestart}
          title="Restart level"
          aria-label="Restart level"
        >
          ↺
        </button>
        <h1 className="hud__level">Level {level}</h1>
        <span className="hud__badge">{shapeLabel(shape)}</span>
      </div>

      <div className="hud__stats">
        <span className="hud__arrows" title="Arrows left">
          <span aria-hidden="true">➤</span> {arrows}
        </span>
        <Hearts lives={lives} />
      </div>
    </header>
  )
}
