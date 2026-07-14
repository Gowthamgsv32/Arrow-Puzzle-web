import { useState } from 'react'
import './App.css'

const ARROWS = ['↑', '→', '↓', '←']

function App() {
  const [count, setCount] = useState(0)

  const arrow = ARROWS[count % ARROWS.length]

  return (
    <main className="app">
      <header className="app__header">
        <h1 className="app__title">
          <span className="app__arrow" aria-hidden="true">
            {arrow}
          </span>
          Arrow Puzzle
        </h1>
        <p className="app__subtitle">React app base is ready.</p>
      </header>

      <section className="app__card">
        <button className="app__button" onClick={() => setCount((c) => c + 1)}>
          Rotate arrow ({count})
        </button>
        <p className="app__hint">
          Edit <code>src/App.jsx</code> to start building the puzzle.
        </p>
      </section>
    </main>
  )
}

export default App
