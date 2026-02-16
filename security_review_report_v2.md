# Security & Architecture Review: Fantasy Parliament

**Date:** 2026-02-16
**Reviewer:** Security Engineer Agent
**Target:** `fantasy-parliament` (Canadian Politics Fantasy League)

## Executive Summary
The application contains a **critical functional disconnect** where frontend team changes are not synced to the backend, rendering the game's core loop broken. Security-wise, the app is relatively low-risk due to its stateless nature, but it lacks basic authentication and is vulnerable to spam.

## 1. Vulnerability Analysis

### A. Onboarding Flow (CSRF/XSS)
*   **CSRF:** The API (`POST /api/register`) lacks CSRF protection.
    *   *Impact:* Low. No persistent session (cookie-based auth) exists to hijack.
*   **XSS:**
    *   *Backend:* `sanitize_name` strips characters but does not HTML-escape.
    *   *Frontend:* React automatically escapes output. No `dangerouslySetInnerHTML` usage found.
    *   *Risk:* Low.

### B. API Authentication & Admin
*   **User Auth:** **Non-Existent.** `user_id` is ignored by the frontend; no login/recovery mechanism.
*   **Admin Auth:**
    *   Uses `verify_api_key` checking `x-api-key` header against `SYNC_API_KEY` env var.
    *   *Verdict:* Acceptable for MVP/internal use.
*   **CORS:** configured to allow `localhost` and `fantasy-parliament.onrender.com`. Safe.

### C. Environment Variables & Database
*   **Handling:** Secure. Uses `os.getenv` and `dotenv`. `.env` is git-ignored.
*   **Migrations:** `models.py` uses raw SQL via `psycopg2`.
    *   *Safety:* Table names are hardcoded (no user input), preventing SQL injection.

### D. External Interactions (`scraper.py`)
*   **API:** Queries public `api.openparliament.ca` via `httpx`.
*   **Safety:** No hardcoded keys. Data handling is standard.

### E. Critical Logic Flaw ("Ghost Team")
*   Frontend team edits are **never saved** to the backend.
*   Frontend tries to POST to non-existent `/leaderboard` endpoint.

## 2. Security Milestones

### Phase 1: Architecture Repair (Urgent)
*   **Goal:** Fix the "Ghost Team" issue.
*   **Tasks:**
    1.  Implement `PUT /api/team/{user_id}`.
    2.  Update frontend to store and use `user_id`.

### Phase 2: Authentication
*   **Goal:** User retention and security.
*   **Tasks:**
    1.  Implement Magic Link Auth (via MailerSend).
    2.  Issue JWTs for session management.

### Phase 3: Hardening
*   **Goal:** Anti-abuse.
    1.  **CAPTCHA:** Add Turnstile/hCaptcha to registration.
    2.  **Rate Limiting:** Upgrade from IP-based to Redis-backed.
    3.  **Headers:** Add `Content-Security-Policy`.

