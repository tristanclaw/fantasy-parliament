from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends, Query, Request, APIRouter
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pony.orm import db_session, select, desc
from models import MP, LeaderboardEntry, Registration, Subscriber, DailyScore, init_db, run_migrations, db
from scraper import run_sync, run_sync_mps_only
from committee_tiers import calculate_committee_score, COMMITTEE_TIERS, get_committee_tier, COMMITTEE_BASE_POINTS
import os
import asyncio
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta, date
import uuid
import re
import random
import secrets
from better_profanity import profanity
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime as dt
from urllib.parse import quote

load_dotenv()

app = FastAPI(title="Canadian Politics Fantasy League API")

# Get the directory where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

# Mount static files for the frontend
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

# Global Cache for MPs
MP_CACHE = {
    "data": [],
    "last_updated": None
}
CACHE_DURATION = timedelta(minutes=15)

# Special Teams Configuration
# Special teams - using valid MP slugs from database
# Note: Some leaders not in current MP list (e.g., Trudeau, Singh)
SPECIAL_TEAMS_CONFIG = {
    "all_party_leaders": {
        "name": "All Party Leaders",
        "slugs": [
            "mark-carney",
            "pierre-poilievre",
            "yves-francois-blanchet",
            "elizabeth-may",
            "jenny-kwan"
        ]
    },
    "all_whips": {
        "name": "All Whips",
        "slugs": [
            "mark-gerretsen",
            "elisabeth-briere",
            "chris-warkentin",
            "rob-moore",
            "yves-perron"
        ]
    },
    "deputy_pm_shadows": {
        "name": "Deputy PM Shadows",
        "slugs": [
            "steven-guilbeault",
            "melissa-lantsman",
            "don-davies",
            "yves-perron",
            "elizabeth-may"
        ]
    }
}

def get_cached_mps():
    now = datetime.now()
    if MP_CACHE["data"] and MP_CACHE["last_updated"] and (now - MP_CACHE["last_updated"] < CACHE_DURATION):
        return MP_CACHE["data"]
    
    print("CACHE: Refreshing MP cache from database...")
    with db_session:
        mps = MP.select().order_by(desc(MP.total_score))[:]
        # Convert to dicts inside the session to detach from ORM
        mp_dicts = [mp_to_dict(m) for m in mps]
        MP_CACHE["data"] = mp_dicts
        MP_CACHE["last_updated"] = now
        print(f"CACHE: Loaded {len(mp_dicts)} MPs.")
        return mp_dicts

# Configure CORS - must specify exact origins when credentials are allowed
# In production, set ALLOWED_ORIGINS env var (comma-separated)
# For development, allow localhost
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    origins = [o.strip() for o in env_origins.split(",")]
else:
    # Default to the known frontend production URL
    origins = [
        "https://fantasy-parliament.onrender.com",
        "http://localhost:3000",
        "http://localhost:5173" # Vite default
    ]
    # Fallback for dev if env not set - strictly speaking should not use * with credentials
    # but for this specific error case we are fixing, we want to ensure frontend works.
    # If we want strict security we would check if the request Origin is in this list.
    # FastAPI CORSMiddleware checks this automatically if we pass a list.

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("SYNC_API_KEY")

async def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="SYNC_API_KEY not configured on server")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.post("/migrate")
async def manual_migrate(api_key: str = Depends(verify_api_key)):
    print("ADMIN: Triggering manual migration...")
    db_url = os.getenv('INTERNAL_DATABASE_URL') or os.getenv('DATABASE_URL_INTERNAL') or os.getenv('DATABASE_URL')
    
    success = False
    msg = ""

    if db_url:
        dsn = db_url
        if dsn.startswith('postgres://'):
            dsn = dsn.replace('postgres://', 'postgresql://', 1)
        success, msg = run_migrations(dsn)
    else:
        # Construct kwargs from environment if using separate vars
        # This matches what we do in startup
        db_password = os.getenv('DB_PASSWORD')
        if not db_password:
             raise HTTPException(status_code=500, detail="DB_PASSWORD missing in environment")
             
        kwargs = {
            'user': os.getenv('DB_USER', 'postgres'),
            'password': db_password,
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'fantasy_politics'),
        }
        success, msg = run_migrations(None, **kwargs)

    if success:
        return {"status": "success", "message": msg}
    else:
        raise HTTPException(status_code=500, detail=msg)

@admin_router.post("/sync")
async def manual_sync(background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    print("ADMIN: Triggering manual sync...")
    background_tasks.add_task(run_sync_with_logging)
    return {"message": "Sync started in background via Admin"}

@admin_router.post("/sync-mps")
async def manual_sync_mps(background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    print("ADMIN: Triggering manual MP roster sync...")
    # We can use the same logging wrapper but call a different function, 
    # but for simplicity let's just create a quick wrapper or reuse logic if possible.
    # Since run_sync_with_logging is hardcoded to run_sync(), let's define a new task or just call it directly if it's fast.
    # Given it fetches 500 records, it might take a few seconds. Background is safer.
    
    async def _sync_mps_task():
        try:
            print("BACKGROUND: Starting MP roster sync...")
            await run_sync_mps_only()
            print("BACKGROUND: MP roster sync finished.")
        except Exception as e:
            print(f"BACKGROUND ERROR: {e}")

    background_tasks.add_task(_sync_mps_task)
    return {"message": "MP Roster sync started in background"}

@admin_router.get("/logs")
def get_admin_logs(api_key: str = Depends(verify_api_key)):
    if os.path.exists("sync.log"):
        with open("sync.log", "r") as f:
            return {"logs": f.read()}
    return {"logs": "No log file found"}

async def run_sync_with_logging():
    import sys
    
    # helper to write to both stdout and file
    class DualWriter:
        def __init__(self, filename):
            self.file = open(filename, "a", buffering=1) # line buffered
            self.stdout = sys.stdout
        
        def write(self, message):
            self.stdout.write(message)
            self.file.write(message)
            
        def flush(self):
            self.stdout.flush()
            self.file.flush()
            
        def close(self):
            self.file.close()

    # Backup original stdout
    old_stdout = sys.stdout
    writer = DualWriter("sync.log")
    sys.stdout = writer
    
    try:
        print(f"BACKGROUND: Starting sync at {datetime.now()}...")
        await run_sync()
        print(f"BACKGROUND: Sync finished successfully at {datetime.now()}.")
    except Exception as e:
        import traceback
        print(f"BACKGROUND ERROR: Sync failed: {e}")
        traceback.print_exc()
    finally:
        sys.stdout = old_stdout
        writer.close()

app.include_router(admin_router)

@app.on_event("startup")
async def startup():
    print("STARTUP: Initializing...")
    
    db_url = os.getenv('INTERNAL_DATABASE_URL') or os.getenv('DATABASE_URL_INTERNAL') or os.getenv('DATABASE_URL')
    if db_url:
        print(f"STARTUP: Using {'INTERNAL_DATABASE_URL' if os.getenv('INTERNAL_DATABASE_URL') else 'DATABASE_URL_INTERNAL' if os.getenv('DATABASE_URL_INTERNAL') else 'DATABASE_URL'}...")
        init_db(db_url)
    else:
        db_password = os.getenv('DB_PASSWORD')
        if not db_password:
            print("STARTUP ERROR: DB_PASSWORD missing")
            raise ValueError("DB_PASSWORD environment variable is required")
            
        print(f"STARTUP: Connecting to {os.getenv('DB_HOST')}...")
        init_db(
            'postgres',
            user=os.getenv('DB_USER', 'postgres'),
            password=db_password,
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'fantasy_politics'),
            sslmode='require'
        )
    print("STARTUP: Database initialized successfully")
    
    # Start scheduler for weekly emails (only on Render production)
    if os.getenv("RENDER"):
        try:
            schedule_weekly_emails()
            schedule_daily_sync()
            schedule_leaderboard_updates()
            scheduler.start()
            print("SCHEDULER: Started")
        except Exception as e:
            print(f"SCHEDULER ERROR: {e}")
    
def mp_to_dict(mp):
    try:
        committee_score = calculate_committee_score(mp.committees) if mp.committees else {"total": 0, "breakdown": {}}
        return {
            "id": mp.id,
            "name": mp.name,
            "party": mp.party,
            "constituency": mp.riding,
            "score": mp.total_score + committee_score.get("total", 0),
            "slug": mp.slug,
            "image_url": mp.image_url,
            "committees": mp.committees,
            "score_breakdown": mp.score_breakdown,
            "committee_score": committee_score,
            "committee_tiers": {(c if isinstance(c, str) else c.get("name", "")): get_committee_tier(c if isinstance(c, str) else c.get("name", "")) for c in (mp.committees or [])}
        }
    except Exception as e:
        print(f"ERROR in mp_to_dict: {e}")
        # Return basic fields only if extended fields fail
        return {
            "id": mp.id,
            "name": mp.name,
            "party": mp.party,
            "constituency": mp.riding,
            "score": getattr(mp, 'total_score', 0),
            "slug": mp.slug,
            "image_url": getattr(mp, 'image_url', None),
            "committees": getattr(mp, 'committees', None),
            "score_breakdown": getattr(mp, 'score_breakdown', None)
        }

@app.get("/mps/search")
def search_mps(q: Optional[str] = Query(None)):
    print(f"DEBUG: Entering /mps/search with q='{q}'")
    try:
        # Use cached data to avoid DB hits on every search
        all_mps = get_cached_mps()
        
        if q:
            search_term = q.strip().lower()
            print(f"DEBUG: Searching for term: '{search_term}'")
            
            results = [
                m for m in all_mps 
                if search_term in m['name'].lower() or 
                   (m['party'] and search_term in m['party'].lower()) or 
                   (m['constituency'] and search_term in m['constituency'].lower())
            ]
            print(f"DEBUG: Search found {len(results)} results")
            return results
        
        # If no query, return all (already ordered by score in cache)
        return all_mps
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in /mps/search: {e}")
        print(error_trace)
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": error_trace})

@app.get("/mps/{mp_id}")
@db_session
def get_mp(mp_id: int):
    print(f"DEBUG: get_mp called with mp_id={mp_id}, type={type(mp_id)}")
    try:
        # Use select().first() instead of get() to avoid potential Pony ORM edge cases
        mp = MP.select(lambda m: m.id == mp_id).first()
        print(f"DEBUG: MP query result: {mp}")
        if not mp:
            print(f"DEBUG: MP not found for id={mp_id}")
            raise HTTPException(status_code=404, detail="MP not found")
        
        result = mp_to_dict(mp)
        print(f"DEBUG: mp_to_dict result: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in /mps/{{mp_id}}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/diag/env")
def diag_env():
    """Debug endpoint to check environment variables."""
    return {
        "MAILERSEND_API_KEY_SET": bool(MAILERSEND_API_KEY),
        "MAILERSEND_API_KEY_PREFIX": MAILERSEND_API_KEY[:20] + "..." if MAILERSEND_API_KEY else None,
        "MAILERSEND_FROM_EMAIL": MAILERSEND_FROM_EMAIL,
    }

@app.get("/admin/test-email")
def test_email(email: str = "tristan@claude.ai"):
    """Test sending a single email."""
    result = send_score_email(email, "Test User", [3552])
    return {"success": result, "email": email}
@app.get("/diag/db")
@db_session
def diag_db():
    try:
        mp_count = MP.select().count()
        lb_count = LeaderboardEntry.select().count()
        ds_count = DailyScore.select().count()
        reg_count = Registration.select().count()
        sub_count = Subscriber.select().count()
        
        # Check registration columns
        from models import db
        cols = []
        try:
            if db.provider_name == 'postgres':
                result = db.select("SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = 'registration'")
                cols = [{"column": r[0], "nullable": r[1]} for r in result]
        except:
            pass

        last_scores = [
            {"mp": s.mp_name, "date": str(s.date), "points": s.points_today} 
            for s in DailyScore.select().order_by(desc(DailyScore.date))[:5]
        ]
        
        return {
            "status": "connected",
            "counts": {
                "mp": mp_count,
                "leaderboard": lb_count,
                "daily_scores": ds_count,
                "registrations": reg_count,
                "subscribers": sub_count
            },
            "registration_schema": cols,
            "last_scores": last_scores,
            "database": str(db.provider_name)
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/mps")
def get_mps(ids: str = None):
    print("DEBUG: Entering /mps endpoint")
    try:
        if ids:
            # Filter by IDs
            id_list = [int(x.strip()) for x in ids.split(',') if x.strip().isdigit()]
            with db_session:
                mps = [MP.get(id=mid) for mid in id_list if MP.get(id=mid)]
                return [mp_to_dict(mp) for mp in mps if mp]
        return get_cached_mps()
    except Exception as e:
        import traceback
        print(f"ERROR in /mps: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scoreboard")
@db_session
def get_scoreboard():
    # Get all MPs and sort by computed score (including committee bonus)
    all_mps = MP.select()
    scored_mps = []
    for mp in all_mps:
        committee_pts = calculate_committee_score(mp.committees).get("total", 0) if mp.committees else 0
        total = mp.total_score + committee_pts
        scored_mps.append((total, mp))
    
    # Sort by total score descending
    scored_mps.sort(key=lambda x: x[0], reverse=True)
    top_mps = [mp for _, mp in scored_mps[:10]]
    return [mp_to_dict(m) for m in top_mps]

@app.get("/leaderboard")
@db_session
def get_leaderboard():
    entries = LeaderboardEntry.select().order_by(desc(LeaderboardEntry.score))[:50]
    return [{"username": e.username, "score": e.score, "updated_at": e.updated_at.isoformat()} for e in entries]

@app.get("/committees")
def get_committee_tiers_info():
    """Return committee tier information and scoring rules"""
    return {
        "tiers": COMMITTEE_TIERS,
        "base_points": COMMITTEE_BASE_POINTS,
        "role_multipliers": {
            "Chair": 1.5,
            "Vice-Chair": 1.25,
            "Member": 1.0
        }
    }

@app.get("/leaderboard/party")
@db_session
def get_party_leaderboard():
    """Rank parties by their top 5 MPs' combined scores"""
    parties = {}
    
    # Get all MPs
    mps = MP.select()
    for mp in mps:
        party = mp.party or "Independent"
        if party not in parties:
            parties[party] = []
        parties[party].append({"name": mp.name, "score": mp.total_score, "id": mp.id})
    
    # Calculate top 5 for each party
    results = []
    for party, mp_list in parties.items():
        mp_list.sort(key=lambda x: x["score"], reverse=True)
        top_5 = mp_list[:5]
        total_score = sum(m["score"] for m in top_5)
        results.append({
            "party": party,
            "score": total_score,
            "mp_count": len(mp_list),
            "top_5": top_5
        })
    
    # Sort by total score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

@app.get("/special")
@db_session
def get_special_leaderboards():
    results = []
    
    # Static special teams - query DB directly
    for key, config in SPECIAL_TEAMS_CONFIG.items():
        team_mps = []
        total_score = 0
        for slug in config["slugs"]:
            mp = MP.get(slug=slug)
            if mp:
                team_mps.append(mp_to_dict(mp))
                total_score += mp.total_score
        if team_mps:
            # Sort MPs by score descending within the team
            team_mps.sort(key=lambda x: x['score'], reverse=True)
            results.append({
                "id": key,
                "name": config["name"],
                "score": total_score,
                "mps": team_mps
            })
    
    # Random Choice (Weekly)
    all_mps = list(MP.select())
    if all_mps:
        today = date.today()
        seed_val = f"{today.year}-{today.isocalendar()[1]}"
        rng = random.Random(seed_val)
        random_mps = rng.sample(all_mps, min(5, len(all_mps)))
        random_team_score = sum(mp.total_score for mp in random_mps)
        
        results.append({
            "id": "random_weekly",
            "name": "Random Choice (Weekly)",
            "score": random_team_score,
            "mps": [mp_to_dict(mp) for mp in random_mps]
        })
    
    return results

def calculate_leaderboard_background():
    """Background task to calculate user scores from their team MPs."""
    print("LEADERBOARD: Starting background calculation...")
    try:
        with db_session:
            # Fetch all registrations (users)
            registrations = Registration.select()
            
            # Cache MP scores to avoid repeated queries
            mp_scores = {mp.id: mp.total_score for mp in MP.select()}
            
            updated_count = 0
            for reg in registrations:
                total_score = 0
                for mp_id in reg.team_mp_ids:
                    # mp_id might be string in JSON, ensure int
                    mp_score = mp_scores.get(int(mp_id), 0)
                    total_score += mp_score
                
                # Update or create LeaderboardEntry
                # Use display_name as username
                entry = LeaderboardEntry.get(username=reg.display_name)
                if entry:
                    if entry.score != total_score:
                        entry.score = total_score
                        entry.updated_at = datetime.now()
                        updated_count += 1
                else:
                    LeaderboardEntry(username=reg.display_name, score=total_score, updated_at=datetime.now())
                    updated_count += 1
            
            print(f"LEADERBOARD: Updated {updated_count} entries.")
    except Exception as e:
        print(f"LEADERBOARD ERROR: {e}")
        import traceback
        traceback.print_exc()

@app.post("/admin/recalc-leaderboard")
async def trigger_leaderboard_recalc(background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """Manually trigger leaderboard recalculation."""
    background_tasks.add_task(calculate_leaderboard_background)
    return {"status": "success", "message": "Leaderboard recalculation started in background"}

class RegistrationRequest(BaseModel):
    user_id: Optional[str] = None
    display_name: str
    team_name: Optional[str] = None
    email: Optional[str] = None
    captain_mp_id: int
    team_mp_ids: List[int]
    same_party_as_captain: bool = False

@app.post("/api/register")
@db_session
def register_user(registration: RegistrationRequest, request: Request):
    # Rate Limiting
    # Use X-Forwarded-For header for real IP behind proxy (e.g. Render)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    if Registration.select(lambda r: r.ip_address == client_ip).count() >= 50:
        raise HTTPException(status_code=429, detail="Too many registrations from this IP address")

    # 4. Input Validation & Sanitization
    display_name = registration.display_name.strip()
    if len(display_name) > 50:
        raise HTTPException(status_code=400, detail="Display name too long (max 50 chars)")
    
    team_name = registration.team_name.strip() if registration.team_name else None
    if team_name and len(team_name) > 100:
        raise HTTPException(status_code=400, detail="Team name too long (max 100 chars)")

    # 3. Email Validation (optional)
    # Generate user_id first for placeholder email
    new_user_id = str(uuid.uuid4())
    email = registration.email.strip() if registration.email else f"user_{new_user_id}@placeholder.local"
    
    # 1. Gameplay Validation
    # At least 1 team member (captain required)
    if len(registration.team_mp_ids) < 1:
        raise HTTPException(status_code=400, detail="Team must have at least 1 MP")
    
    if len(registration.team_mp_ids) > 5:
        raise HTTPException(status_code=400, detail="Team can have at most 5 MPs (1 captain + 4 members)")
    
    # No duplicate MPs
    if len(set(registration.team_mp_ids)) != len(registration.team_mp_ids):
         raise HTTPException(status_code=400, detail="Duplicate MPs in team")

    # All MP IDs exist
    # Note: PonyORM select with 'in' list works fine for integers
    existing_mps = MP.select(lambda m: m.id in registration.team_mp_ids)
    if existing_mps.count() != len(registration.team_mp_ids):
         raise HTTPException(status_code=400, detail="One or more selected MPs do not exist")
         
    # Captain must be part of the team 
    if registration.captain_mp_id not in registration.team_mp_ids:
        raise HTTPException(status_code=400, detail="Captain must be part of your team")

    # Captain exists
    if not MP.get(id=registration.captain_mp_id):
        raise HTTPException(status_code=400, detail="Captain MP does not exist")

    # 2. Secure Identity
    # Ignore client-provided user_id and generate a secure UUID (already done above for email)

    # Create registration
    try:
        Registration(
            user_id=new_user_id,
            display_name=display_name,
            team_name=team_name or "",
            email=email or "",
            captain_mp_id=registration.captain_mp_id,
            team_mp_ids=registration.team_mp_ids,
            ip_address=client_ip or "",
            registered_at=datetime.utcnow()
        )
        # Placeholder for mailing list integration
        print(f"MAILING LIST: Added {email} to mailing list.")
        
        return {
            "status": "success", 
            "message": "Registration successful",
            "user_id": new_user_id 
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Registration error: {e}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# ============================================
# Email Subscription API
# ============================================

# Initialize profanity filter
profanity.load_censor_words()

# MailerSend configuration
MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")
MAILERSEND_FROM_EMAIL = "test@test-pzkmgq7yj0yl059v.mlsender.net"  # Verified test domain

class SubscribeRequest(BaseModel):
    name: str
    email: str
    selected_mps: List[int]

def sanitize_name(name: str) -> str:
    """Sanitize display name: max 30 chars + profanity filter."""
    # Character limit
    if len(name) > 30:
        raise HTTPException(status_code=400, detail="Display name too long (max 30 characters)")
    
    # Profanity filter
    if profanity.contains_profanity(name):
        raise HTTPException(status_code=400, detail="Display name contains inappropriate content")
    
    return name.strip()

def calculate_team_score(mp_ids: List[int]) -> int:
    """Calculate total score for a list of MP IDs."""
    with db_session:
        mps = MP.select(lambda m: m.id in mp_ids)
        return sum(mp.total_score for mp in mps)

def send_score_email(email: str, name: str, mp_ids: List[int]) -> bool:
    """Send weekly score email via MailerSend."""
    if not MAILERSEND_API_KEY:
        print(f"MAILERSEND: API key not configured, skipping email to {email}")
        return False
    
    try:
        import mailersend
        from mailersend import emails
        
        # Calculate team score
        team_score = calculate_team_score(mp_ids)
        
        # Get leaderboard benchmark
        with db_session:
            leader = LeaderboardEntry.select().order_by(desc(LeaderboardEntry.score)).first()
            leader_score = leader.score if leader else 0
        
        # Get top 3 from scoreboard
        with db_session:
            top_mps = MP.select().order_by(desc(MP.total_score))[:3]
            top_names = ", ".join([m.name for m in top_mps])
        
        # Email content
        subject = f"Your Fantasy Parliament Score: {team_score} points"
        body = f"""Hello {name},

Your Fantasy Parliament team scored: {team_score} points this week.

{'You are ahead of the Party Leaders benchmark!' if team_score > leader_score else f'Party Leaders benchmark: {leader_score} points'}

Top MPs this week: {top_names}

Keep picking wisely!

- Fantasy Parliament Team
"""
        
        # Send email using MailerSend
        print(f"MAILERSEND: Attempting to send to {email} with key={MAILERSEND_API_KEY[:20]}... and from={MAILERSEND_FROM_EMAIL}")
        mailer = emails.NewMailer(MAILERSEND_API_KEY)
        mailer.set_mail_from([MAILERSEND_FROM_EMAIL], {"name": "Fantasy Parliament"})
        mailer.add_mail_to([email])
        mailer.set_subject(subject)
        mailer.set_text_content(body)
        
        response = mailer.send()
        
        print(f"MAILERSEND: Response: {response.status_code} - {response.text}")
        
        if response.status_code in [200, 202]:
            print(f"MAILERSEND: Email sent successfully to {email}")
            return True
        else:
            print(f"MAILERSEND: Failed to send email to {email}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"MAILERSEND ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.post("/subscribe")
@db_session
def subscribe(request: SubscribeRequest):
    """Add a new subscriber."""
    # Validate email
    email = request.email.strip()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Check if already subscribed (Generic response)
    existing = Subscriber.get(email=email)
    if existing:
        # Return success to prevent enumeration
        return {"status": "success", "message": "If this email is valid, you'll receive a confirmation"}
    
    # Sanitize name (character limit + profanity)
    sanitized_name = sanitize_name(request.name)
    
    # Validate MP IDs exist
    if request.selected_mps:
        existing_mps = MP.select(lambda m: m.id in request.selected_mps)
        if existing_mps.count() != len(request.selected_mps):
            raise HTTPException(status_code=400, detail="One or more selected MPs do not exist")
    
    # Generate secure unsubscribe token
    token = secrets.token_urlsafe(32)

    # Create subscriber
    try:
        Subscriber(
            name=sanitized_name,
            email=email,
            selected_mps=request.selected_mps,
            unsubscribe_token=token,
            created_at=datetime.utcnow()
        )
        print(f"SUBSCRIBER: Added {email} to subscriptions")
        
        # In a real app, we would send a confirmation email here with the unsubscribe link:
        # link = f"https://.../unsubscribe?token={token}"
        
        return {"status": "success", "message": "Subscribed successfully"}
    except Exception as e:
        print(f"Subscribe error: {e}")
        raise HTTPException(status_code=500, detail="Subscription failed")

@app.delete("/unsubscribe")
@db_session
def unsubscribe(token: str):
    """Remove a subscriber by secure token."""
    subscriber = Subscriber.get(unsubscribe_token=token)
    if not subscriber:
        # Return 404 or generic success - 404 is fine for invalid token
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    email = subscriber.email
    subscriber.delete()
    print(f"SUBSCRIBER: Unsubscribed {email} via token")
    return {"status": "success", "message": "Unsubscribed successfully"}

@app.get("/subscribers")
@db_session
def list_subscribers(api_key: str = Header(None)):
    """Admin endpoint to list subscribers (email only)."""
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    subscribers = Subscriber.select()
    return {
        "count": subscribers.count(),
        "subscribers": [{"name": s.name, "email": s.email, "created_at": s.created_at.isoformat()} for s in subscribers]
    }

# ============================================
# Cron Endpoint for Weekly Score Emails
# ============================================

@app.post("/cron/weekly-score-emails")
@db_session
def trigger_weekly_emails(api_key: str = Header(None)):
    """Trigger weekly score emails to all subscribers."""
    # Skip API key check if called internally (scheduler passes None)
    if api_key is not None and api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    subscribers = Subscriber.select()
    count = 0
    failed = 0
    
    for sub in subscribers:
        success = send_score_email(sub.email, sub.name, sub.selected_mps)
        if success:
            count += 1
        else:
            failed += 1
    
    return {
        "status": "completed",
        "sent": count,
        "failed": failed,
        "total": subscribers.count()
    }

# Initialize scheduler for weekly emails
scheduler = AsyncIOScheduler()

def schedule_weekly_emails():
    """Schedule weekly emails (runs on Render)."""
    # Schedule to run every Saturday at 10:00
    scheduler.add_job(
        trigger_weekly_emails, 
        'cron', 
        day_of_week='sat', 
        hour=10, 
        minute=0,
        id='weekly_emails'
    )
    print("SCHEDULER: Weekly email job scheduled for Sundays at 18:00")

def schedule_daily_sync():
    """Schedule daily sync job."""
    scheduler.add_job(
        run_sync_with_logging, 
        'cron', 
        hour=3, 
        minute=0,
        id='daily_sync'
    )
    print("SCHEDULER: Daily sync job scheduled for 03:00")

def schedule_leaderboard_updates():
    """Schedule leaderboard calculation every hour."""
    scheduler.add_job(
        calculate_leaderboard_background,
        'interval',
        minutes=60,
        id='leaderboard_calc'
    )
    print("SCHEDULER: Leaderboard calculation scheduled every 60 minutes")

@app.post("/admin/sync-now")
async def sync_now(api_key: str = Depends(verify_api_key)):
    """Run sync synchronously and return result immediately."""
    import io
    import sys
    
    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()
    
    try:
        await run_sync()
        output = mystdout.getvalue()
        return {"status": "success", "logs": output}
    except Exception as e:
        import traceback
        output = mystdout.getvalue() + "\n" + traceback.format_exc()
        return {"status": "error", "logs": output}
    finally:
        sys.stdout = old_stdout

@app.post("/admin/update-committees")
async def update_committees(request: Request, api_key: str = Depends(verify_api_key)):
    """Update MP committee assignments from JSON payload."""
    body = await request.body()
    import json
    try:
        committee_data = json.loads(body)
    except:
        return {"status": "error", "message": "Invalid JSON body"}
    
    if not isinstance(committee_data, list):
        return {"status": "error", "message": "Expected array of {slug, committees}"}
    
    updated = 0
    with db_session:
        for item in committee_data:
            mp = MP.get(slug=item.get("slug"))
            if mp:
                mp.committees = item.get("committees", [])
                updated += 1
    
    return {"status": "success", "updated": updated}

@app.post("/admin/test-sync")
async def test_sync(api_key: str = Depends(verify_api_key)):
    """Test sync with just one MP"""
    import httpx
    
    client = httpx.AsyncClient(timeout=30.0)
    semaphore = asyncio.Semaphore(5)
    
    start_date = date.today() - timedelta(days=7)
    start_date_str = start_date.isoformat()
    
    # Test with Pierre Poilievre
    mp_slug = "pierre-poilievre"
    
    try:
        print(f"TEST: Fetching speeches for {mp_slug}")
        speech_resp = await client.get(
            f"https://api.openparliament.ca/speeches/?politician={quote(mp_slug)}&date__gte={start_date_str}",
            headers={"Accept": "application/json"}
        )
        speech_data = speech_resp.json()
        
        print(f"TEST: Fetching bills for {mp_slug}")
        bill_resp = await client.get(
            f"https://api.openparliament.ca/bills/?sponsor_politician={quote(mp_slug)}",
            headers={"Accept": "application/json"}
        )
        bill_data = bill_resp.json()
        
        speech_count = len(speech_data.get('objects', [])) if speech_data else 0
        bill_count = len(bill_data.get('objects', [])) if bill_data else 0
        
        print(f"TEST: Speech count: {speech_count}")
        print(f"TEST: Bill count: {bill_count}")
        
        return {"status": "ok", "speech_count": speech_count, "bill_count": bill_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await client.aclose()

@app.get("/health")
def health():
    return {"status": "ok"}

# Also serve root
@app.get("/")
async def serve_root():
    """Serve the SPA index.html at root"""
    return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

# Admin endpoint to seed random scores for testing
@app.post("/admin/seed-scores")
@db_session
def seed_scores(api_key: str = Depends(verify_api_key)):
    """Seed random scores for all MPs (for testing)."""
    import random
    mps = MP.select()
    count = 0
    for mp in mps:
        mp.total_score = random.randint(0, 100)
        count += 1
    return {"status": "ok", "updated": count}

# ============================================
# SPA Routing - Serve React Frontend
# ============================================
from fastapi.responses import FileResponse
import os


@app.get("/mps/{mp_id}/scores")
@db_session
def get_mp_scores(mp_id: int):
    """Get daily score history for an MP"""
    try:
        mp = MP.select(lambda m: m.id == mp_id).first()
        if not mp:
            raise HTTPException(status_code=404, detail="MP not found")
        
        scores = [
            {"date": str(ds.date), "points": ds.points_today}
            for ds in mp.daily_scores.order_by(DailyScore.date)
        ]
        
        return {
            "mp_id": mp_id,
            "mp_name": mp.name,
            "total_score": mp.total_score,
            "scores": scores
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/{path:path}")
async def serve_spa(path: str):
    """Serve React SPA for all non-API routes."""
    # Check if it's an API route that wasn't caught
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Try to serve static file
    static_path = os.path.join("frontend/dist", path)
    if os.path.isfile(static_path):
        return FileResponse(static_path)
    
    # Fallback to index.html for SPA routing
    return FileResponse(os.path.join("frontend/dist", "index.html"))

@app.post("/admin/bulk-import-scores")
async def bulk_import_scores(scores: List[dict], api_key: str = Depends(verify_api_key)):
    """Bulk import daily scores"""
    from pony.orm import db_session, commit
    from datetime import datetime
    
    imported = 0
    with db_session():
        for s in scores:
            mp = MP.get(slug=s.get('mp_slug'))
            if not mp:
                continue
            
            score_date = datetime.strptime(s['date'], '%Y-%m-%d').date()
            
            existing = DailyScore.get(mp=mp, date=score_date)
            if not existing:
                DailyScore(
                    mp=mp,
                    mp_name=s.get('mp_name', mp.name),
                    party=s.get('party', mp.party),
                    riding=s.get('riding', mp.riding),
                    points_today=s.get('points', 0),
                    date=score_date
                )
            else:
                existing.points_today = s.get('points', 0)
            
            # Recalculate total
            total = sum(ds.points_today for ds in mp.daily_scores)
            mp.total_score = total
            
            imported += 1
        commit()
    
    return {"imported": imported}

@app.post("/admin/recalculate-scores")
async def recalculate_scores(api_key: str = Depends(verify_api_key)):
    """Recalculate all MP total scores from daily_scores"""
    from pony.orm import db_session, commit, select
    
    updated = 0
    with db_session():
        mps = select(mp for mp in MP)[:]
        for mp in mps:
            # Calculate total from all daily_scores
            total = sum(ds.points_today for ds in mp.daily_scores)
            mp.total_score = total
            updated += 1
        commit()
    
    return {"updated": updated}

@app.post("/admin/populate-breakdowns")
async def populate_breakdowns(api_key: str = Depends(verify_api_key)):
    """Populate score_breakdown for all MPs from daily_scores"""
    from pony.orm import db_session, commit, select
    
    updated = 0
    with db_session():
        mps = select(mp for mp in MP)[:]
        for mp in mps:
            breakdown = {"speeches": 0, "votes": 0, "bills": 0}
            for ds in mp.daily_scores:
                breakdown["speeches"] += ds.points_today
            
            mp.score_breakdown = breakdown
            updated += 1
        commit()
    
    return {"updated": updated}

