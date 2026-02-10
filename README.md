# Canadian Politics Fantasy League - Data Scraper

This is a Python-based data scraper and API for tracking MP performance based on OpenParliament.ca data.

## Stack
- FastAPI
- PostgreSQL
- Pony ORM
- HTTPX (Async API client)

## Scoring Logic
- **House Speech**: +1 point
- **Vote Attended**: +2 points
- **Bill Sponsored**: +10 points
- **Bill Passed**: +50 points (Royal Assent)

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` based on `.env.example`
3. Run the API: `uvicorn main:app --reload`
4. Trigger sync: `curl -X POST http://localhost:8000/sync`

## Daily Sync
To automate the daily sync, set up a cron job to call the `/sync` endpoint or run `scraper.py` directly.
