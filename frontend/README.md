# Frontend

The web app of the Self Assessment Tool: upload a textbook, take the generated exam on camera, read the results. See the [root README](../README.md) for the full picture.

React 18, bootstrapped with Create React App, state in Redux, answers recorded through `react-webcam`.

## Screens

| Component | Role |
|---|---|
| `src/components/ExamCreator.js` | Upload the textbook PDF, wait for it to be digested |
| `src/components/exam.js` | Show each question, record the spoken answer, upload it with its timestamps |
| `src/components/ResponseDisplay.js` | Show the scored results and the material each question came from |
| `src/components/Loader.js` | Waiting state while the backend works |

## Running

```bash
npm install
npm start                 # http://localhost:3000
```

The backend address comes from the Redux store, which reads `REACT_APP_BACKEND_URL` at build time and otherwise falls back to the original deployment address:

```bash
REACT_APP_BACKEND_URL=http://localhost:8000 npm start
```

## Scripts

| Command | What it does |
|---|---|
| `npm start` | Development server |
| `npm run build` | Production bundle in `build/` |
| `npm test` | Test runner — the only test is CRA's default `App.test.js` |

Nothing here calls the facial-expression model: the webcam is used only to record the answer, and the analysis happens server-side.
