import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  EMPTY,
  idx,
  boundingBox,
  headForwardCells,
  isReleasable,
  tryRelease,
  isSolvable,
} from './engine.js'

// Build a state from explicit arrows on a rows x cols board.
function build(rows, cols, arrowList) {
  const grid = new Array(rows * cols).fill(EMPTY)
  const arrows = {}
  for (const a of arrowList) {
    arrows[a.id] = a
    for (const [r, c] of a.cells) grid[idx(r, c, cols)] = a.id
  }
  return {
    rows,
    cols,
    grid,
    arrows,
    count: arrowList.length,
    lives: 3,
    status: 'playing',
    level: 1,
  }
}

// A bent line: (2,1)->(2,3) then up to (0,3). Head at (0,3) pointing U.
const bent = {
  id: 0,
  dir: 'U',
  head: [0, 3],
  cells: [
    [2, 1],
    [2, 2],
    [2, 3],
    [1, 3],
    [0, 3],
  ],
  verts: [
    [2, 1],
    [2, 3],
    [0, 3],
  ],
}

test('boundingBox spans the whole bent line', () => {
  assert.deepEqual(boundingBox(bent), { minR: 0, minC: 1, spanR: 3, spanC: 3 })
})

test('headForwardCells walks from the head to the edge', () => {
  // Head (0,3) pointing U is already on the top edge -> no cells ahead.
  assert.deepEqual(headForwardCells(bent, 5, 5), [])
  // Head (2,3) pointing R on 5x5 -> (2,4)
  assert.deepEqual(headForwardCells({ dir: 'R', head: [2, 3] }, 5, 5), [[2, 4]])
})

test('isReleasable checks only the cells ahead of the head', () => {
  const s = build(5, 5, [bent])
  assert.equal(isReleasable(s.grid, bent, 5, 5), true) // head on edge -> clear

  const blocker = { id: 1, dir: 'D', head: [1, 3], cells: [[1, 3]], verts: [[1, 3]] }
  // Put a one-cell line right above a rightward head to block it.
  const facing = {
    id: 2,
    dir: 'R',
    head: [4, 2],
    cells: [
      [4, 1],
      [4, 2],
    ],
    verts: [
      [4, 1],
      [4, 2],
    ],
  }
  const wall = { id: 3, dir: 'U', head: [4, 4], cells: [[4, 4]], verts: [[4, 4]] }
  const s2 = build(5, 5, [facing, wall, blocker])
  // facing head (4,2) R -> ahead (4,3),(4,4); (4,4) is wall -> blocked
  assert.equal(isReleasable(s2.grid, facing, 5, 5), false)
})

test('releasing a line clears all its cells and can win', () => {
  const s = build(5, 5, [bent])
  const { state, result, arrow } = tryRelease(s, 0)
  assert.equal(result, 'released')
  assert.equal(arrow.id, 0)
  for (const [r, c] of bent.cells) assert.equal(state.grid[idx(r, c, 5)], EMPTY)
  assert.equal(state.count, 0)
  assert.equal(state.status, 'won')
})

test('a blocked release costs a life and removes nothing', () => {
  const A = { id: 0, dir: 'R', head: [0, 0], cells: [[0, 0]], verts: [[0, 0]] }
  const B = { id: 1, dir: 'L', head: [0, 2], cells: [[0, 2]], verts: [[0, 2]] }
  const s = build(1, 3, [A, B]) // A ahead: (0,1),(0,2); (0,2) taken -> blocked
  s.lives = 2
  const { state, result } = tryRelease(s, 0)
  assert.equal(result, 'blocked')
  assert.equal(state.lives, 1)
  assert.equal(state.count, 2)
  assert.equal(state.status, 'playing')
})

test('losing the final life ends the game', () => {
  const A = { id: 0, dir: 'R', head: [0, 0], cells: [[0, 0]], verts: [[0, 0]] }
  const B = { id: 1, dir: 'L', head: [0, 2], cells: [[0, 2]], verts: [[0, 2]] }
  const s = build(1, 3, [A, B])
  s.lives = 1
  const { state, result } = tryRelease(s, 0)
  assert.equal(result, 'blocked')
  assert.equal(state.lives, 0)
  assert.equal(state.status, 'lost')
})

test('no interaction once the game is over', () => {
  const A = { id: 0, dir: 'R', head: [0, 0], cells: [[0, 0]], verts: [[0, 0]] }
  const s = build(1, 1, [A])
  s.status = 'won'
  assert.equal(tryRelease(s, 0).result, 'none')
})

test('isSolvable distinguishes jammed from clearable boards', () => {
  const jammed = build(1, 3, [
    { id: 0, dir: 'R', head: [0, 0], cells: [[0, 0]], verts: [[0, 0]] },
    { id: 1, dir: 'L', head: [0, 2], cells: [[0, 2]], verts: [[0, 2]] },
  ])
  assert.equal(isSolvable(jammed.grid, jammed.arrows, 1, 3), false)

  const easy = build(1, 3, [
    { id: 0, dir: 'L', head: [0, 0], cells: [[0, 0]], verts: [[0, 0]] },
    { id: 1, dir: 'R', head: [0, 2], cells: [[0, 2]], verts: [[0, 2]] },
  ])
  assert.equal(isSolvable(easy.grid, easy.arrows, 1, 3), true)
})
