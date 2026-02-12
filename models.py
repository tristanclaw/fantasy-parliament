from pony.orm import Database, Required, Optional, Set, PrimaryKey
from datetime import date, datetime

db = Database()

class MP(db.Entity):
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
    username = Required(str, unique=True)
    score = Required(int)
    updated_at = Required(datetime)

class Speech(db.Entity):
    mp = Required(MP)
    date = Required(date)
    content_url = Required(str)

class VoteAttendance(db.Entity):
    mp = Required(MP)
    vote_url = Required(str)
    attended = Required(bool)
    date = Required(date)

class Bill(db.Entity):
    number = Required(str)
    title = Required(str)
    sponsor = Required(MP)
    passed = Required(bool, default=False)
    date_introduced = Required(date)
    date_passed = Optional(date)

def run_migrations(dsn=None, **kwargs):
    """
    Run manual migrations using psycopg2 directly.
    This can be called at startup (safe mode) or via API.
    """
    import psycopg2
    
    print("Starting manual migrations...")
    try:
        if dsn:
            conn = psycopg2.connect(dsn, sslmode='require', connect_timeout=10)
        else:
            conn = psycopg2.connect(
                user=kwargs.get('user'),
                password=kwargs.get('password'),
                host=kwargs.get('host'),
                database=kwargs.get('database'),
                sslmode='require',
                connect_timeout=10
            )
        
        conn.autocommit = True
        with conn.cursor() as cur:
            # Migration 1: MP.total_score
            try:
                cur.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "total_score" INTEGER NOT NULL DEFAULT 0')
                print("Applied/Checked: MP.total_score")
            except Exception as e:
                print(f"Migration warning (MP.total_score): {e}")
            
            # Migration 2: MP.image_url
            try:
                cur.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "image_url" TEXT')
                print("Applied/Checked: MP.image_url")
            except Exception as e:
                print(f"Migration warning (MP.image_url): {e}")

            # Migration 3: Bill.date_passed
            try:
                cur.execute('ALTER TABLE "Bill" ADD COLUMN IF NOT EXISTS "date_passed" DATE')
                print("Applied/Checked: Bill.date_passed")
            except Exception as e:
                print(f"Migration warning (Bill.date_passed): {e}")
                
        conn.close()
        print("Direct Postgres migration successful")
        return True, "Migrations completed successfully"
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

    # Run manual migrations using psycopg2 directly before Pony binds
    # Only if provider is postgres
    if provider == 'postgres':
        # In safe_mode, we log errors but don't crash
        # In unsafe mode (e.g. manual trigger), we might want to propagate, 
        # but here we just rely on run_migrations return value if we were calling it directly.
        # Since init_db is usually startup, we default to safe behavior for migrations.
        
        success, msg = run_migrations(dsn, **kwargs)
        if not success:
            if safe_mode:
                print(f"WARNING: {msg} - Continuing startup in safe mode.")
            else:
                raise Exception(msg)

    # Bind Pony
    try:
        if dsn:
            print(f"init_db: Binding with URL...")
            # Ensure sslmode is required for Pony/psycopg2
            db.bind(provider='postgres', dsn=dsn, sslmode='require')
        else:
            # Pass through the original provider string (e.g. 'sqlite') if not a URL
            db.bind(provider=provider, **kwargs)

        db.generate_mapping(create_tables=True)
        print("PonyORM binding and mapping successful")
    except Exception as e:
        print(f"PonyORM binding failed: {e}")
        if not safe_mode:
            raise
