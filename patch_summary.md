# Patch Summary: Daily Sync & Scraper Simplification

## Changes
1.  **Refactored `scraper.py`**:
    - Removed complex historical data fetching.
    - Implemented `sync_daily_activity` to fetch speeches, votes, and bills for a specific date.
    - **Speeches**: 1 point per speech.
    - **Votes**: 1 point per vote attendance.
    - **Bills**: 2 points per sponsored bill passed (checked via recent bills).
    - Stores results in `DailyScore` table.
    - Updates `MP.total_score` based on `DailyScore` sum.

2.  **Updated `models.py`**:
    - Added `DailyScore` model: `mp_name | party | riding | points_today | date`.
    - Commented out deprecated models: `Speech`, `VoteAttendance`, `Bill`.
    - Removed deprecated migrations for `Bill`.

3.  **Updated `main.py`**:
    - Added `DailyScore` to imports and usage in `diag_db`.
    - Added `schedule_daily_sync()` to run the scraper daily at 03:00 via APScheduler.
    - Removed references to deprecated models in diagnostics.

## Verification
- Code syntax checked.
- `scraper.py` logic follows new rules.
- `DailyScore` table will be created automatically by Pony ORM.
