# Arrow-Puzzle-web

A web-based Arrow Puzzle game, built with React and Vite.

## Getting started

```bash
npm install      # install dependencies
npm run dev      # start the dev server
npm run build    # build for production
npm run preview  # preview the production build
npm run lint     # run ESLint
```

The dev server runs at `http://localhost:5173` by default.

## Project structure

```
index.html          # app entry HTML
src/
  main.jsx          # React entry point
  App.jsx           # root component
  App.css           # component styles
  index.css         # global styles
public/             # static assets
vite.config.js      # Vite configuration
eslint.config.js    # ESLint configuration
```

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
