import { useCallback, useRef, useState } from 'react'
import './App.css'
import { useGame } from './hooks/useGame.js'
import { computeTrain } from './game/train.js'
import HUD from './components/HUD.jsx'
import Board from './components/Board.jsx'
import Overlay from './components/Overlay.jsx'

const SHAKE_MS = 380

function App() {
  const { game, release, restart, nextLevel } = useGame()

  const [flying, setFlying] = useState([]) // [{ key, train }]
  const [blocked, setBlocked] = useState(null) // arrow id
  const flyKey = useRef(0)
  const shakeToken = useRef(0)

  const handleArrow = useCallback(
    (id) => {
      const rows = game.rows
      const cols = game.cols
      const { result, arrow } = release(id)

      if (result === 'released') {
        const key = ++flyKey.current
        const train = computeTrain(arrow, rows, cols)
        setFlying((f) => [...f, { key, train }])
        setTimeout(() => setFlying((f) => f.filter((a) => a.key !== key)), train.durMs)
      } else if (result === 'blocked') {
        const token = ++shakeToken.current
        setBlocked(id)
        setTimeout(() => {
          if (shakeToken.current === token) setBlocked(null)
        }, SHAKE_MS)
      }
    },
    [release, game.rows, game.cols],
  )

  return (
    <div className="app">
      <div className="app__frame">
        <HUD
          level={game.level}
          arrows={game.count}
          lives={game.lives}
          shape={game.shape}
          onRestart={restart}
        />

        <div className="app__board-wrap">
          <Board
            game={game}
            flying={flying}
            blocked={blocked}
            onArrow={handleArrow}
          />
          <Overlay
            status={game.status}
            level={game.level}
            onNext={nextLevel}
            onRestart={restart}
          />
        </div>

        <p className="app__hint">
          Tap a snake to send it slithering off the board. If its path is
          blocked, you lose a heart. Clear them all to win.
        </p>
      </div>
    </div>
  )
}

export default App
