# backend/api.py
# The ONLY module the frontend ever calls. It contains no real logic itself —
# it just receives HTTP requests and forwards them to the right backend module,
# then converts the result to JSON.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend import screener

app = FastAPI(title="Stock Market App API")

# Allows the frontend (served from a different local port, e.g. file:// or
# localhost:5500) to call this API from the browser. Without this, browsers
# block the request as a security default (CORS).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for local personal use; tighten if ever deployed publicly
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """Quick check that the server is up. Visit http://localhost:8000/api/health"""
    return {"status": "ok"}


@app.get("/api/screener")
def get_screener_results():
    """
    Runs the full screening pipeline (global bias -> sector ranking ->
    timeframe alignment -> indicator validation) and returns it as JSON.
    This can be slow (multiple network calls to Yahoo Finance) — the frontend
    should show a loading state while waiting.
    """
    try:
        df = screener.run_daily_screen()
        if df.empty:
            return {"bias": None, "results": []}
        bias = df.iloc[0]["global_bias"] if "global_bias" in df.columns else None
        return {"bias": bias, "results": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn backend.api:app --reload --port 8000
