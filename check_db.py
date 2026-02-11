import os
import sys
import traceback
from dotenv import load_dotenv
from models import init_db, db
from pony.orm import db_session

# Force stdout flushing
sys.stdout.reconfigure(line_buffering=True)

print("--- DIAGNOSTIC START ---")
load_dotenv()

db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('DB_NAME', 'fantasy_politics')

print(f"Environment check:")
print(f"  DB_USER: {db_user}")
print(f"  DB_HOST: {db_host}")
print(f"  DB_NAME: {db_name}")
print(f"  DB_PASSWORD: {'***' if db_password else 'MISSING'}")

if not db_password:
    print("ERROR: DB_PASSWORD not found in environment.")
    sys.exit(1)

try:
    print("Initializing database connection...")
    init_db(
        provider='postgres',
        user=db_user,
        password=db_password,
        host=db_host,
        database=db_name,
        sslmode='require'  # Enforce SSL
    )
    print("Database bound successfully.")

    print("Verifying schema access...")
    with db_session:
        # Check if table exists by trying a raw count
        cnt = db.select("count(*) from \"MP\"")
        print(f"Connection verified. MP count: {cnt[0]}")

    print("--- DIAGNOSTIC SUCCESS ---")

except Exception as e:
    print("\n!!! DIAGNOSTIC FAILURE !!!")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)
