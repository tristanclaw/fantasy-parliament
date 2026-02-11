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

def init_db(provider='postgres', user=None, password=None, host=None, database=None, **kwargs):
    params = {k: v for k, v in locals().items() if k != 'kwargs' and v is not None}
    params.update(kwargs)
    db.bind(**params)
    
    # Run manual migrations before generating mapping
    # This prevents Pony from crashing when columns are missing in existing tables
    try:
        from pony.orm import db_session
        with db_session:
            db.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "total_score" INTEGER NOT NULL DEFAULT 0')
            db.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "image_url" TEXT')
    except Exception as e:
        print(f"Migration warning (can be ignored if DB is fresh): {e}")
        
    db.generate_mapping(create_tables=True)
