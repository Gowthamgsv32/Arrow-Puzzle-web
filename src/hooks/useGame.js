import { useCallback, useRef, useState } from 'react'
import { tryRelease } from '../game/engine.js'
import { createGame } from '../game/generator.js'

const LEVEL_KEY = 'arrow-puzzle:level'

function loadLevel() {
  try {
    const raw = localStorage.getItem(LEVEL_KEY)
    const n = raw ? parseInt(raw, 10) : 1
    return Number.isFinite(n) && n >= 1 ? n : 1
  } catch {
    return 1
  }
}

function saveLevel(level) {
  try {
    localStorage.setItem(LEVEL_KEY, String(level))
  } catch {
    /* ignore storage failures (private mode, etc.) */
  }
}

/**
 * React binding around the pure engine. Exposes the current game state plus
 * actions. `release` returns the outcome so the UI can drive animations.
 */
export function useGame() {
  const [game, setGame] = useState(() => createGame(loadLevel()))
  // Mirror latest state so `release` reads fresh values without stale closures.
  const ref = useRef(game)
  ref.current = game

  const commit = useCallback((next) => {
    ref.current = next
    setGame(next)
  }, [])

  const release = useCallback(
    (id) => {
      const { state, result, arrow } = tryRelease(ref.current, id)
      if (result !== 'none') commit(state)
      return { result, arrow }
    },
    [commit],
  )

  const restart = useCallback(() => {
    commit(createGame(ref.current.level))
  }, [commit])

  const nextLevel = useCallback(() => {
    const level = ref.current.level + 1
    saveLevel(level)
    commit(createGame(level))
  }, [commit])

  return { game, release, restart, nextLevel }
}
