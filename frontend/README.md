# Frontend

React and Vite frontend. From this directory, run `npm ci`, optionally copy `.env.example` to `.env`, and then run `npm run dev`. The default URL is http://localhost:5173.

Set `VITE_API_URL` to the FastAPI base URL (default `http://localhost:8000`). The shared client attaches the stored JWT and normalizes HTTP/network errors. Authentication is handled by FastAPI; use seeded development accounts from `../backend/README.md`.

Pages with backend endpoints display API data. Timetables and features without backend support are labeled as unavailable for this phase. `src/data/mockData.js` remains as an unused legacy sample-data file and is not imported by application pages.
