from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends, Query, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select, desc
from models import MP, LeaderboardEntry, Bill, Speech, VoteAttendance, Registration, init_db, run_migrations, db
from scraper import run_sync
import os
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta, date
import uuid
import re
import random

load_dotenv()

app = FastAPI(title="Canadian Politics Fantasy League API")

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
            "elizabeth-may"
        ]
    },
    "all_whips": {
        "name": "All Whips",
        "slugs": [
            "ruby-sahota",
            "john-nater",
            "don-davies",
            "claude-debellefeuille",
            "elizabeth-may"
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

@app.get("/admin/logs")
def get_admin_logs(api_key: str = Header(None)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    if os.path.exists("sync.log"):
        with open("sync.log", "r") as f:
            return {"logs": f.read()}
    return {"logs": "No log file found"}

async def run_sync_with_logging():
    import sys
    from io import StringIO
    
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    
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
        with open("sync.log", "w") as f:
            f.write(mystdout.getvalue())

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
    
def mp_to_dict(mp):
    return {
        "id": mp.id,
        "name": mp.name,
        "party": mp.party,
        "constituency": mp.riding,
        "score": mp.total_score,
        "slug": mp.slug,
        "image_url": mp.image_url
    }

@app.get("/diag/db")
@db_session
def diag_db():
    try:
        mp_count = MP.select().count()
        lb_count = LeaderboardEntry.select().count()
        bill_count = Bill.select().count()
        speech_count = Speech.select().count()
        vote_count = VoteAttendance.select().count()
        return {
            "status": "connected",
            "counts": {
                "mp": mp_count,
                "leaderboard": lb_count,
                "bill": bill_count,
                "speech": speech_count,
                "vote": vote_count
            },
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
def get_mps():
    print("DEBUG: Entering /mps endpoint")
    try:
        return get_cached_mps()
    except Exception as e:
        import traceback
        print(f"ERROR in /mps: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/scoreboard")
@db_session
def get_scoreboard():
    mps = MP.select().order_by(desc(MP.total_score))[:10]
    return [mp_to_dict(m) for m in mps]

class LeaderboardSubmission(BaseModel):
    username: str
    score: int

@app.get("/leaderboard")
@db_session
def get_leaderboard():
    entries = LeaderboardEntry.select().order_by(desc(LeaderboardEntry.score))[:50]
    return [{"username": e.username, "score": e.score, "updated_at": e.updated_at.isoformat()} for e in entries]

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
        random_mps = rng.sample(all_mps, min(4, len(all_mps)))
        random_team_score = sum(mp.total_score for mp in random_mps)
        
        results.append({
            "id": "random_weekly",
            "name": "Random Choice (Weekly)",
            "score": random_team_score,
            "mps": [mp_to_dict(mp) for mp in random_mps]
        })
    
    return results

@app.post("/leaderboard")
@db_session
def update_leaderboard(submission: LeaderboardSubmission):
    entry = LeaderboardEntry.get(username=submission.username)
    if entry:
        entry.score = submission.score
        entry.updated_at = datetime.now()
    else:
        LeaderboardEntry(username=submission.username, score=submission.score, updated_at=datetime.now())
    return {"status": "success"}

class RegistrationRequest(BaseModel):
    user_id: Optional[str] = None
    display_name: str
    team_name: Optional[str] = None
    email: str
    captain_mp_id: int
    team_mp_ids: List[int]

@app.post("/api/register")
@db_session
def register_user(registration: RegistrationRequest, request: Request):
    # Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    if Registration.select(lambda r: r.ip_address == client_ip).count() >= 3:
        raise HTTPException(status_code=429, detail="Too many registrations from this IP address")

    # 4. Input Validation & Sanitization
    display_name = registration.display_name.strip()
    if len(display_name) > 50:
        raise HTTPException(status_code=400, detail="Display name too long (max 50 chars)")
    
    team_name = registration.team_name.strip() if registration.team_name else None
    if team_name and len(team_name) > 100:
        raise HTTPException(status_code=400, detail="Team name too long (max 100 chars)")

    # 3. Email Validation
    email = registration.email.strip()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if Registration.get(email=email):
         raise HTTPException(status_code=400, detail="Email already registered")

    # 1. Gameplay Validation
    # Exactly 4 team members
    if len(registration.team_mp_ids) != 4:
        raise HTTPException(status_code=400, detail="Team must have exactly 4 MPs")
    
    # No duplicate MPs
    if len(set(registration.team_mp_ids)) != 4:
         raise HTTPException(status_code=400, detail="Duplicate MPs in team")

    # All MP IDs exist
    # Note: PonyORM select with 'in' list works fine for integers
    existing_mps = MP.select(lambda m: m.id in registration.team_mp_ids)
    if existing_mps.count() != 4:
         raise HTTPException(status_code=400, detail="One or more selected MPs do not exist")
         
    # Captain must be part of the team (enforces "Exactly 4 team members")
    if registration.captain_mp_id not in registration.team_mp_ids:
        raise HTTPException(status_code=400, detail="Captain must be part of the 4-member team")

    # Captain exists
    if not MP.get(id=registration.captain_mp_id):
        raise HTTPException(status_code=400, detail="Captain MP does not exist")

    # 2. Secure Identity
    # Ignore client-provided user_id and generate a secure UUID
    new_user_id = str(uuid.uuid4())

    # Create registration
    try:
        Registration(
            user_id=new_user_id,
            display_name=display_name,
            team_name=team_name,
            email=email,
            captain_mp_id=registration.captain_mp_id,
            team_mp_ids=registration.team_mp_ids,
            ip_address=client_ip,
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
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/sync")
async def trigger_sync(background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    background_tasks.add_task(run_sync)
    return {"message": "Sync started in background"}

@app.get("/health")
def health():
    return {"status": "ok"}

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
