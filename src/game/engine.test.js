import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  idx,
  forwardCells,
  isPathClear,
  countArrows,
  tryRelease,
  isSolvable,
} from './engine.js'

// 3x3 board helper — rows top→bottom, cols left→right.
const B = (rows) => rows.flat()

test('forwardCells walks to the edge in the given direction', () => {
  // (1,1) pointing Right on a 3x3 board -> only (1,2)
  assert.deepEqual(forwardCells(1, 1, 'R', 3, 3), [[1, 2]])
  // (1,1) pointing Up -> (0,1)
  assert.deepEqual(forwardCells(1, 1, 'U', 3, 3), [[0, 1]])
  // corner pointing off-board -> empty path
  assert.deepEqual(forwardCells(0, 0, 'U', 3, 3), [])
})

test('isPathClear detects blockers', () => {
  const board = B([
    [null, null, null],
    ['R', null, 'L'],
    [null, null, null],
  ])
  // 'R' at (1,0): path is (1,1),(1,2); (1,2) holds 'L' -> blocked
  assert.equal(isPathClear(board, 1, 0, 'R', 3, 3), false)
  // 'L' at (1,2): path is (1,1),(1,0); (1,0) holds 'R' -> blocked
  assert.equal(isPathClear(board, 1, 2, 'L', 3, 3), false)
})

test('tryRelease removes an unobstructed arrow and decrements the count', () => {
  const state = {
    board: B([
      [null, null, null],
      [null, null, 'R'],
      [null, null, null],
    ]),
    rows: 3,
    cols: 3,
    arrows: 1,
    lives: 3,
    status: 'playing',
  }
  const { state: next, result, dir } = tryRelease(state, 1, 2)
  assert.equal(result, 'released')
  assert.equal(dir, 'R')
  assert.equal(next.board[idx(1, 2, 3)], null)
  assert.equal(next.arrows, 0)
  assert.equal(next.status, 'won')
  assert.equal(next.lives, 3)
})

test('tryRelease on a blocked arrow costs a life', () => {
  const state = {
    board: B([
      [null, null, null],
      ['R', null, 'L'],
      [null, null, null],
    ]),
    rows: 3,
    cols: 3,
    arrows: 2,
    lives: 2,
    status: 'playing',
  }
  const { state: next, result } = tryRelease(state, 1, 0)
  assert.equal(result, 'blocked')
  assert.equal(next.lives, 1)
  assert.equal(next.arrows, 2) // nothing removed
  assert.equal(next.status, 'playing')
})

test('losing the last life ends the game', () => {
  const state = {
    board: B([['R', 'L', null]]),
    rows: 1,
    cols: 3,
    arrows: 2,
    lives: 1,
    status: 'playing',
  }
  const { state: next, result } = tryRelease(state, 0, 0)
  assert.equal(result, 'blocked')
  assert.equal(next.lives, 0)
  assert.equal(next.status, 'lost')
})

test('no interaction once the game is over', () => {
  const state = {
    board: B([['R']]),
    rows: 1,
    cols: 1,
    arrows: 1,
    lives: 0,
    status: 'lost',
  }
  const { result } = tryRelease(state, 0, 0)
  assert.equal(result, 'none')
})

test('countArrows and isSolvable on a hand-made board', () => {
  // Two arrows pointing at each other: R _ L is a deadlock (unsolvable).
  const jammed = B([['R', null, 'L']])
  assert.equal(countArrows(jammed), 2)
  assert.equal(isSolvable(jammed, 1, 3), false)

  // Both pointing outward is trivially solvable.
  const easy = B([['L', null, 'R']])
  assert.equal(isSolvable(easy, 1, 3), true)
})
