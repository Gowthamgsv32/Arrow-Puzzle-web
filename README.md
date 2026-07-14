# Arrow-Puzzle-web

A web-based Arrow Puzzle game, built with React and Vite.

## How to play

Each level draws a **shape** — heart, ball, star, apple, diamond — out of many
**thin bent arrow lines**. Every line is a self-avoiding polyline that turns 90°
at its corners, with an arrowhead at its head. Tap a line to **slide it off the
board like a train**, head-first along its own path — but only if the straight
path from its head to the edge is empty. If another line blocks that path,
nothing is released and you lose a heart. Lose all three hearts and the round is
over. Clear every line to advance to the next level (and the next shape).

Lines are generated **randomly and never overlap**, always fit inside the
level's shape, and every level is **guaranteed solvable** (and can never
dead-end). Your progress is saved locally so you resume where you left off.

## Getting started

```bash
npm install      # install dependencies
npm run dev      # start the dev server
npm run build    # build for production
npm run preview  # preview the production build
npm run lint     # run ESLint
npm test         # run the engine + generator unit tests (node:test)
```

The dev server runs at `http://localhost:5173` by default.

## Project structure

```
index.html            # app entry HTML
src/
  main.jsx            # React entry point
  App.jsx             # root component: state + animation orchestration
  App.css             # game styles
  index.css           # global styles
  game/
    constants.js      # directions
    engine.js         # pure rules: bent lines, release logic, win/lose
    generator.js      # random non-overlapping solvable line generator (masked)
    shapes.js         # silhouette masks (heart, ball, star, apple, diamond)
    train.js          # travel-path math for the slide-out animation
    *.test.js         # unit tests (zero-dependency, node:test)
  hooks/
    useGame.js        # React binding + localStorage progress
  components/
    HUD.jsx           # level, line count, hearts, shape name
    Arrow.jsx         # one thin bent line + arrowhead, drawn as an SVG path
    Board.jsx         # board SVG + train (slide-out) rendering
    Overlay.jsx       # win / lose modal
public/               # static assets
vite.config.js        # Vite configuration
eslint.config.js      # ESLint configuration
```

## Architecture notes

- **`game/engine.js`** is pure and framework-free — all rules live here and are
  covered by unit tests, so the logic is verifiable without a browser.
- **Solvability guarantee:** the generator grows each bent line over empty
  cells and only keeps it if its head's straight path to the edge is currently
  clear (of other lines *and* its own body). Removing the lines in reverse
  placement order is therefore always a valid solution, and because removing a
  line only ever *frees* cells, no play order can dead-end. A test proves this
  across 200 random boards.

## Deployment (GitHub Pages)

This project auto-deploys to GitHub Pages via GitHub Actions
(`.github/workflows/deploy.yml`) on every push to `main`.

**One-time setup:** in the repository, go to
**Settings → Pages → Build and deployment → Source** and select
**GitHub Actions**.

Once enabled, the live site is served at:

<https://gowthamgsv32.github.io/Arrow-Puzzle-web/>

The Vite `base` in `vite.config.js` is set to `/Arrow-Puzzle-web/` so asset
paths resolve correctly under the repository subpath.

## Tech stack

- [React 18](https://react.dev/)
- [Vite 5](https://vitejs.dev/)
- [ESLint 9](https://eslint.org/)
- [GitHub Pages](https://pages.github.com/) + GitHub Actions
