import { useCallback, useRef, useState } from 'react'
import './App.css'
import { useGame } from './hooks/useGame.js'
import HUD from './components/HUD.jsx'
import Board from './components/Board.jsx'
import Overlay from './components/Overlay.jsx'

const FLY_MS = 420
const SHAKE_MS = 380

function App() {
  const { game, release, restart, nextLevel } = useGame()

  const [flying, setFlying] = useState([]) // [{ key, arrow }]
  const [blocked, setBlocked] = useState(null) // arrow id
  const flyKey = useRef(0)
  const shakeToken = useRef(0)

  const handleArrow = useCallback(
    (id) => {
      const { result, arrow } = release(id)

      if (result === 'released') {
        const key = ++flyKey.current
        setFlying((f) => [...f, { key, arrow }])
        setTimeout(() => setFlying((f) => f.filter((a) => a.key !== key)), FLY_MS)
      } else if (result === 'blocked') {
        const token = ++shakeToken.current
        setBlocked(id)
        setTimeout(() => {
          if (shakeToken.current === token) setBlocked(null)
        }, SHAKE_MS)
      }
    },
    [release],
  )

  return (
    <div className="app">
      <div className="app__frame">
        <HUD
          level={game.level}
          arrows={game.count}
          lives={game.lives}
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
          Tap an arrow to fly it off the board. If the path is blocked, you lose
          a heart. Clear them all to win.
        </p>
      </div>
    </div>
  )
}

export default App
