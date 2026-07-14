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

  const [flying, setFlying] = useState([]) // [{ id, r, c, dir }]
  const [blocked, setBlocked] = useState(null) // { r, c, id }
  const flyId = useRef(0)

  const handleCell = useCallback(
    (r, c) => {
      const { result, dir } = release(r, c)

      if (result === 'released') {
        const id = ++flyId.current
        setFlying((f) => [...f, { id, r, c, dir }])
        setTimeout(
          () => setFlying((f) => f.filter((a) => a.id !== id)),
          FLY_MS,
        )
      } else if (result === 'blocked') {
        const id = ++flyId.current
        setBlocked({ r, c, id })
        setTimeout(
          () => setBlocked((b) => (b && b.id === id ? null : b)),
          SHAKE_MS,
        )
      }
    },
    [release],
  )

  return (
    <div className="app">
      <div className="app__frame">
        <HUD
          level={game.level}
          arrows={game.arrows}
          lives={game.lives}
          onRestart={restart}
        />

        <div className="app__board-wrap">
          <Board
            game={game}
            flying={flying}
            blocked={blocked}
            onCell={handleCell}
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
