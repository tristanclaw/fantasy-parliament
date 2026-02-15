import asyncio
import os
import sys
import traceback
from dotenv import load_dotenv
from models import init_db, db
from scraper import run_sync

# Force stdout flushing
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

print("--- MANUAL SCRAPER RUN ---")

db_password = os.getenv('DB_PASSWORD')
if not db_password:
    print("ERROR: DB_PASSWORD not found.")
    sys.exit(1)

try:
    init_db(
        'postgres',
        user=os.getenv('DB_USER', 'postgres'),
        password=db_password,
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'fantasy_politics'),
        sslmode='require'
    )
    print("Database initialized.")
    
    print("Starting sync...")
    asyncio.run(run_sync())
    print("Sync finished.")

except Exception as e:
    print("\n!!! SCRAPER FAILURE !!!")
    traceback.print_exc()
