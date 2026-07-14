// Silhouette masks. Each shape is a predicate over normalized coordinates
// x,y in (-1, 1) (y points DOWN, matching grid rows). shapeMask() rasterizes a
// shape onto an N×N grid and returns the Set of allowed cell indices.

function pointInPoly(x, y, pts) {
  let inside = false
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i]
    const [xj, yj] = pts[j]
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) {
      inside = !inside
    }
  }
  return inside
}

const STAR = (() => {
  const pts = []
  for (let k = 0; k < 10; k++) {
    const rad = k % 2 === 0 ? 0.98 : 0.42
    const a = -Math.PI / 2 + (k * Math.PI) / 5
    pts.push([Math.cos(a) * rad, Math.sin(a) * rad])
  }
  return pts
})()

export const SHAPES = {
  ball: (x, y) => x * x + y * y <= 0.86 * 0.86,

  diamond: (x, y) => Math.abs(x) + Math.abs(y) <= 0.92,

  heart: (x, y) => {
    const X = x * 1.25
    const Y = -y * 1.25 + 0.35
    return Math.pow(X * X + Y * Y - 1, 3) - X * X * Y * Y * Y <= 0
  },

  star: (x, y) => pointInPoly(x, y, STAR),

  apple: (x, y) => {
    // stem
    if (Math.abs(x + 0.02) < 0.07 && y > -0.95 && y < -0.55) return true
    // two-lobed body with a small top dimple
    const inL = (x + 0.28) * (x + 0.28) + (y - 0.1) * (y - 0.1) <= 0.62 * 0.62
    const inR = (x - 0.28) * (x - 0.28) + (y - 0.1) * (y - 0.1) <= 0.62 * 0.62
    const dimple = x * x + (y + 0.82) * (y + 0.82) < 0.07
    return (inL || inR) && !dimple
  },
}

export const SHAPE_NAMES = ['heart', 'ball', 'star', 'apple', 'diamond']

/** Rasterize a shape onto an N×N grid -> Set of allowed cell indices (r*N+c). */
export function shapeMask(name, n) {
  const fn = SHAPES[name] || SHAPES.ball
  const cells = new Set()
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const x = ((c + 0.5) / n) * 2 - 1
      const y = ((r + 0.5) / n) * 2 - 1
      if (fn(x, y)) cells.add(r * n + c)
    }
  }
  return cells
}
