# Arrow-Puzzle-web

A web-based Arrow Puzzle game, built with React and Vite.

## How to play

The board is packed with **lengthy arrows** — each is a straight piece one or
more cells long with an arrowhead at its leading end, pointing up, down, left,
or right. Tap an arrow to fly the whole piece off the board **in the direction
it points** — but only if every cell ahead of its arrowhead, up to the edge, is
empty. If another arrow blocks that path, nothing is released and you lose a
heart. Lose all three hearts and the round is over. Clear every arrow to
advance to the next level.

Every generated level is **guaranteed solvable** (and can never dead-end), and
your progress is saved locally so you resume where you left off.

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
    engine.js         # pure rules: multi-cell arrows, release logic, win/lose
    generator.js      # guaranteed-solvable level generator + difficulty scaling
    *.test.js         # unit tests (zero-dependency, node:test)
  hooks/
    useGame.js        # React binding + localStorage progress
  components/
    HUD.jsx           # level, arrow count, hearts
    Arrow.jsx         # one lengthy arrow (rounded shaft + head), drawn as SVG
    Board.jsx         # positions arrows + fly-off / blocked rendering
    Overlay.jsx       # win / lose modal
public/               # static assets
vite.config.js        # Vite configuration
eslint.config.js      # ESLint configuration
```

## Architecture notes

- **`game/engine.js`** is pure and framework-free — all rules live here and are
  covered by unit tests, so the logic is verifiable without a browser.
- **Solvability guarantee:** the generator builds each board by placing arrows
  one at a time, only where the forward path is currently clear. Removing them
  in reverse placement order is therefore always a valid solution, and because
  removing an arrow only ever *clears* other paths, no play order can dead-end.
  A test proves this across 200 random boards.

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
