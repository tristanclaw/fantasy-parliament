# Security Review: Fantasy Parliament (Session 45-1 Refactor)

## Summary
I have reviewed `scraper.py` and `models.py` focusing on SSRF/Injection vulnerabilities, Data Integrity, and sensitive data exposure.

**Verdict:** ❌ **FAIL**

The code contains a critical logic flaw in `fetch_json` that breaks API requests with query parameters, leading to immediate data integrity failure (sync will silently fail). It must be fixed before deployment.

## Critical Findings

### 1. Data Integrity: Broken URL Construction in `fetch_json`
**Severity:** High (Functional Failure)
**Location:** `scraper.py:40-41`
```python
if not url.endswith('/'):
    url += '/'
```
**Issue:** This logic unconditionally appends a slash to the URL. If the URL contains query parameters (e.g., `.../politicians/?limit=1000`), it becomes `.../politicians/?limit=1000/`.
**Impact:** The OpenParliament API returns `404 Not Found` for these malformed URLs (confirmed via test).
- `sync_mps` fails completely (`?limit=1000` becomes `?limit=1000/`).
- `sync_votes` fails completely (`?session=45-1` becomes `?session=45-1/`).
**Remediation:**
Modify `fetch_json` to parse the URL or check for query parameters before appending the slash.
```python
if '?' not in url and not url.endswith('/'):
    url += '/'
```

### 2. Data Integrity: Pagination Logic
**Severity:** Medium
**Location:** `sync_votes`
**Issue:** The function only fetches the first page of results. If there are more than 20 votes (default page size) in the last 7 days, they will be missed.
**Remediation:** Implement pagination handling (`next` link in API response) to ensure all relevant votes are captured.

## Minor Issues / Warnings

1.  **URL Construction Hardening:**
    - `mp.slug` and `vote_url` are used directly in f-strings. While sourced from the trusted OpenParliament API, explicit URL encoding (`urllib.parse.quote`) is recommended for robustness.
    
2.  **Date Handling:**
    - `cleanup_old_data` removes bills if `date_introduced < cutoff` AND (`not passed` OR `passed < cutoff`). This logic is correct for a rolling window but relies on `date_passed` being accurately backfilled. Ensure `process_mp_data` robustly handles `date_passed` updates.

3.  **Database Migration:**
    - The direct `psycopg2` migration in `models.py` is unconventional but functional. Ensure the database user has schema alteration permissions.

## Recommendation
Reject the pull request until the `fetch_json` URL construction bug is fixed.
