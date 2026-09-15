# Stock Market App — Architecture & Design Document

## 1. What This Application Is

A personal-use Python application to:
- Track live prices of stocks you choose
- Analyze historical price trends
- Predict future price movement using a simple ML model
- Track your own portfolio (what you bought, at what price, current profit/loss)

This is **not** a trading bot — it doesn't place trades automatically. It's a decision-support tool: it shows you data and estimates, you decide what to do with them.

---

## 2. Frontend vs Backend — In Plain Language

Every application has two halves, no matter how simple:

- **Frontend** = what *you* see and interact with. Buttons, tables, charts, text on screen. It has no "brain" — it just displays things and passes your clicks/inputs onward.
- **Backend** = the part that does the actual work. Fetching prices, doing math, running the ML model, reading/writing the database. It has no screen — it just processes data and hands results back.

Think of it like a restaurant: the frontend is the waiter (takes your order, brings your food) and the backend is the kitchen (actually cooks). The waiter doesn't cook; the kitchen doesn't take orders directly from you.

**Why split them at all, for a personal app?**
Even if you're the only user, keeping these separate means:
- You can change how data is *displayed* without touching how it's *calculated* (and vice versa).
- You can swap frontend later (CLI → dashboard → web app) without rewriting your prediction logic.
- Bugs are easier to isolate — "is this a display bug or a data bug?"

---

## 3. How They Connect (for THIS app specifically)

You chose a **full web app**: a browser-based frontend talking to a Python backend over HTTP. This is a real client-server split — the backend runs as its own server process (via FastAPI) exposing endpoints; the frontend is a separate set of files (HTML/CSS/JS) running in the browser that calls those endpoints with `fetch()`.

```
[ Browser (frontend) ]
        |
        |  HTTP request, e.g. GET /api/screener
        v
[ FastAPI backend server ]
        |
        |  calls into backend/screener.py, portfolio.py, etc.
        v
[ Backend logic + database ]
        |
        |  returns JSON
        v
[ Browser renders it as a table/chart ]
```

Concretely:
- Frontend calls `fetch("http://localhost:8000/api/screener")`
- FastAPI receives the request, calls `screener.run_daily_screen()` internally
- FastAPI converts the result to JSON and sends it back
- Frontend's JavaScript takes that JSON and builds the table/chart on the page

This is a bigger step than direct function calls (you now have two processes to run — the API server and something serving the frontend files), but it's what "more control" buys you: the frontend can run on your phone's browser, a teammate's laptop, anywhere — as long as it can reach the backend's address. It also means frontend and backend can be worked on, restarted, and deployed completely independently.

---

## 4. Frontend — What It Will Actually Show

Plain HTML + CSS + JavaScript, no build step required (no npm install needed to get started) — just files you open in a browser, calling the FastAPI backend.

| Screen/View | Shows |
|---|---|
| Live prices | Ticker, current price, day change % |
| Screener table | Sector name, global bias, RSI, Bollinger status, volume confirmed, verdict |
| Historical chart | Price line + moving average overlay |
| Prediction view | Predicted next-day/week direction + confidence |
| Portfolio view | Your holdings, buy price, current value, P&L |

---

## 5. Backend — The Modules You'll Build

| Module | Responsibility |
|---|---|
| `data_fetcher.py` | Talks to `yfinance` — gets live + historical prices |
| `database.py` | SQLite — stores your trades and cached historical data |
| `analysis.py` | Moving averages, returns, volatility calculations |
| `screener.py` | Sector/stock screening pipeline (global bias, ranking, timeframe alignment, indicators) |
| `predictor.py` | The ML model — trains on historical data, outputs predictions |
| `portfolio.py` | P&L math, holdings summary |
| `api.py` | **New** — FastAPI app. The only module the frontend ever talks to. Wraps all the modules above as HTTP endpoints. |

Each module should only do ONE job. `predictor.py` should never touch the database directly — it should receive data that `data_fetcher.py` or `database.py` already prepared. `api.py` doesn't contain any real logic itself — it just receives HTTP requests and calls the right backend function, the same way the frontend used to call functions directly. This keeps things "not difficult to understand or execute," which is exactly what you asked for.

---

## 6. Suggested Folder Structure

```
stock_app/
├── frontend/
│   ├── index.html             # the page structure
│   ├── style.css              # visual design
│   └── app.js                 # fetches from the API, renders tables/charts
├── backend/
│   ├── api.py                 # FastAPI app - the ONLY thing frontend talks to
│   ├── data_fetcher.py
│   ├── database.py
│   ├── analysis.py
│   ├── screener.py
│   ├── predictor.py
│   └── portfolio.py
├── data/
│   └── stock_data.db         # SQLite file
├── config.py                 # list of tickers you track, settings
└── requirements.txt
```

This structure means: frontend folder never contains calculation logic, backend folder never contains display/UI code. `api.py` is the single doorway between them — nothing in `frontend/` ever imports a `backend/` module directly, it only ever calls a URL. When something breaks, you know exactly which folder to look in.

---

## 7. Build Order (ties to the phase checklist)

1. `backend/data_fetcher.py` — get live prices working, print to terminal (no frontend yet)
2. `backend/database.py` + `backend/portfolio.py` — portfolio tracking
3. `backend/analysis.py` — historical trends
4. `frontend/dashboard.py` — Streamlit UI wrapping the above
5. `backend/predictor.py` — prediction, added last

Building backend-first, frontend-last means you always have something *working* (even if ugly) at every stage — you're never blocked waiting for the "whole thing" to be done before you see results.
