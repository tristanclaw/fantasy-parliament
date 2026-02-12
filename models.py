from pony.orm import Database, Required, Optional, Set, PrimaryKey, db_session
from datetime import date, datetime

db = Database()

class MP(db.Entity):
    _table_ = 'mp'
    name = Required(str)
    slug = Required(str, unique=True)
    party = Optional(str)
    riding = Optional(str)
    image_url = Optional(str)
    speeches = Set('Speech')
    votes = Set('VoteAttendance')
    sponsored_bills = Set('Bill', reverse='sponsor')
    total_score = Required(int, default=0)

class LeaderboardEntry(db.Entity):
    _table_ = 'leaderboardentry'
    username = Required(str, unique=True)
    score = Required(int)
    updated_at = Required(datetime)

class Speech(db.Entity):
    _table_ = 'speech'
    mp = Required(MP)
    date = Required(date)
    content_url = Required(str)

class VoteAttendance(db.Entity):
    _table_ = 'voteattendance'
    mp = Required(MP)
    vote_url = Required(str)
    attended = Required(bool)
    date = Required(date)

class Bill(db.Entity):
    _table_ = 'bill'
    number = Required(str)
    title = Required(str)
    sponsor = Required(MP)
    passed = Required(bool, default=False)
    date_introduced = Required(date)
    date_passed = Optional(date)

@db_session
def run_migrations(dsn=None, **kwargs):
    """
    Run manual migrations using psycopg2 directly.
    This can be called at startup (safe mode) or via API.
    """
    import psycopg2
    
    print("Starting manual migrations...")
    try:
        # Get raw connection from Pony
        provider = db.provider
        conn = provider.connect()
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Audit tables first to debug
            print("Auditing tables in public schema...")
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [t[0] for t in cur.fetchall()]
            print(f"Found tables: {tables}")

            # Force lowercase 'mp' check first
            for table in ['mp', 'MP']:
                if table in tables:
                    try:
                        print(f"Applying MP.total_score to table: {table}")
                        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "total_score" INTEGER NOT NULL DEFAULT 0')
                        print(f"Applied/Checked: {table}.total_score")
                    except Exception as e:
                        print(f"Migration warning ({table}.total_score): {e}")
            
            for table in ['mp', 'MP']:
                if table in tables:
                    try:
                        print(f"Applying MP.image_url to table: {table}")
                        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "image_url" TEXT')
                        print(f"Applied/Checked: {table}.image_url")
                        
                        # Verify column existence immediately
                        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'image_url'")
                        if cur.fetchone():
                            print(f"VERIFIED: {table}.image_url EXISTS")
                        else:
                            print(f"CRITICAL: {table}.image_url MISSING even after ALTER")
                    except Exception as e:
                        print(f"Migration warning ({table}.image_url): {e}")

            for table in ['bill', 'Bill']:
                if table in tables:
                    try:
                        print(f"Applying Bill.date_passed to table: {table}")
                        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "date_passed" DATE')
                        print(f"Applied/Checked: {table}.date_passed")
                    except Exception as e:
                        print(f"Migration warning ({table}.date_passed): {e}")
                
        # Pony handles closing or returning to pool
        print("Direct Postgres migration successful")
        return True, f"Migrations completed. Tables found: {tables}"
    except Exception as e:
        error_msg = f"Direct migration failed: {e}"
        print(error_msg)
        return False, error_msg

def init_db(provider_or_url='postgres', safe_mode=True, **kwargs):
    dsn = None
    provider = provider_or_url

    # Check if first arg is a URL
    if provider_or_url.startswith('postgres://') or provider_or_url.startswith('postgresql://'):
        provider = 'postgres'
        dsn = provider_or_url
        if dsn.startswith('postgres://'):
            dsn = dsn.replace('postgres://', 'postgresql://', 1)

    # Bind Pony first so run_migrations can use the provider
    try:
        if dsn:
            print(f"init_db: Binding with URL (len={len(dsn)})...")
            # Ensure sslmode is required for Pony/psycopg2
            if 'sslmode=' not in dsn:
                separator = '&' if '?' in dsn else '?'
                dsn += f"{separator}sslmode=require"
            db.bind(provider='postgres', dsn=dsn)
        else:
            # Pass through the original provider string (e.g. 'sqlite') if not a URL
            db.bind(provider=provider, **kwargs)

        db.generate_mapping(create_tables=True)
        print("PonyORM binding and mapping successful")
    except Exception as e:
        print(f"PonyORM binding failed: {e}")
        if not safe_mode:
            raise

    # Run manual migrations using psycopg2 directly via Pony connection
    if provider == 'postgres':
        success, msg = run_migrations(dsn, **kwargs)
        if not success:
            if safe_mode:
                print(f"WARNING: {msg} - Continuing startup in safe mode.")
            else:
                raise Exception(msg)
