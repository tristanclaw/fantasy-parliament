import httpx
import asyncio
from datetime import datetime, date, timedelta
from urllib.parse import quote
from pony.orm import db_session, select, delete, count
from models import MP, Speech, VoteAttendance, Bill, db
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://openparliament.ca/api/v1"

PARTY_MAPPING = {
    "Conservative": "CPC",
    "Liberal": "Lib",
    "NDP": "NDP",
    "Bloc Québécois": "BQ",
    "Green Party": "GPC",
    "Independent": "Ind"
}

def construct_image_url(name, party_name):
    parts = name.replace(".", "").split()
    if len(parts) >= 2:
        first = parts[0]
        last = "".join(parts[1:])
    else:
        first = name
        last = ""
        
    first = first.replace("-", "").replace("'", "")
    last = last.replace("-", "").replace("'", "")
    
    party_code = PARTY_MAPPING.get(party_name, "Ind")
    
    # Updated for 45th Parliament
    return f"https://www.ourcommons.ca/Content/Parliamentarians/Images/OfficialMPPhotos/45/{last}{first}_{party_code}.jpg"

async def fetch_json(url):
    async with httpx.AsyncClient() as client:
        if '?' not in url and not url.endswith('/'):
            url += '/'
        # Handle query params that might already be in URL
        try:
            # Always append format=json
            response = await client.get(url, params={"format": "json"}, headers={"Accept": "application/json"})
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

@db_session
def cleanup_old_data():
    cutoff_date = date.today() - timedelta(days=7)
    print(f"Cleaning up data older than {cutoff_date}")
    delete(s for s in Speech if s.date < cutoff_date)
    delete(v for v in VoteAttendance if v.date < cutoff_date)
    
    # Iterate to avoid decompilation issues with complex logic in Python 3.12
    # Select candidates for deletion (introduced > 7 days ago)
    bills_to_check = select(b for b in Bill if b.date_introduced < cutoff_date)
    for b in bills_to_check:
        # If it hasn't passed, or passed long ago, delete it
        if b.date_passed is None or b.date_passed < cutoff_date:
            b.delete()

@db_session
def calculate_all_scores():
    mps = select(m for m in MP)[:]
    cutoff_date = date.today() - timedelta(days=7)
    
    print("Recalculating scores...")
    for mp in mps:
        score = 0
        
        # Speeches: 1 point (active in last 7 days)
        # Since we prune, we can just count, but to be safe vs db drift, verify date
        score += count(s for s in mp.speeches if s.date >= cutoff_date) * 1
        
        # Votes: 2 points
        score += count(v for v in mp.votes if v.date >= cutoff_date) * 2
        
        # Bills:
        # +10 if introduced in last 7 days
        # +50 if passed in last 7 days
        for bill in mp.sponsored_bills:
            if bill.date_introduced >= cutoff_date:
                score += 10
            if bill.date_passed and bill.date_passed >= cutoff_date:
                score += 50
                
        mp.total_score = score
    print("Score recalculation complete.")

@db_session
async def sync_mps():
    url = f"{BASE_URL}/politicians/?limit=1000"
    total_synced = 0
    total_created = 0
    
    while url:
        print(f"Scraper: Fetching MPs from {url}")
        data = await fetch_json(url)
        if not data: 
            print("Scraper: No data returned from fetch_json")
            break
        
        objects = data.get('objects', [])
        print(f"Scraper: Found {len(objects)} objects in page")
        
        for mp_data in objects:
            party_info = mp_data.get('current_party')
            if not party_info:
                continue
                
            party_name = party_info.get('short_name', {}).get('en')
            
            riding_info = mp_data.get('current_riding')
            riding_name = riding_info.get('name', {}).get('en') if riding_info else None
            
            slug = mp_data['url'].strip('/').split('/')[-1]
            name = mp_data['name']
            
            mp = MP.get(slug=slug)
            if not mp:
                mp = MP(name=name, slug=slug)
                total_created += 1
            
            mp.party = party_name
            mp.riding = riding_name
            # Update image URL to ensuring latest session format
            mp.image_url = construct_image_url(name, party_name)
            
            total_synced += 1
            
        next_path = data.get('pagination', {}).get('next_url')
        if next_path:
             url = f"https://openparliament.ca{next_path}" if next_path.startswith('/') else next_path
        else:
             url = None
        
    print(f"Synced {total_synced} MPs ({total_created} new)")

@db_session
async def process_mp_data(mp, yesterday_str):
    # 1. Speeches
    speech_data = await fetch_json(f"{BASE_URL}/debates/?politician={quote(mp.slug)}&date={yesterday_str}")
    if speech_data:
        for obj in speech_data.get('objects', []):
            if not Speech.exists(content_url=obj['url']):
                Speech(mp=mp, date=date.fromisoformat(yesterday_str), content_url=obj['url'])

    # 2. Bills
    bill_data = await fetch_json(f"{BASE_URL}/bills/?sponsor={quote(mp.slug)}")
    if bill_data:
        for b in bill_data.get('objects', []):
            bill = Bill.get(number=b['number'])
            
            # Determine introduced date
            intro_date_str = b.get('introduced') or yesterday_str
            intro_date = date.fromisoformat(intro_date_str)
            
            if not bill:
                bill = Bill(number=b['number'], 
                           title=b['name']['en'], 
                           sponsor=mp, 
                           date_introduced=intro_date)
            else:
                # Update introduced date if needed (e.g. data correction)
                bill.date_introduced = intro_date
            
            # Check if status indicates Royal Assent
            status_text = str(b.get('status', {}).get('en', ''))
            if 'Royal Assent' in status_text:
                if not bill.passed:
                    bill.passed = True
                    # If we just discovered it passed, and we assume it happened recently (yesterday or today),
                    # set date_passed. Ideally API gives this date, but 'introduced' is the only top-level date.
                    # We'll default to yesterday for scoring purposes if it's a new discovery.
                    bill.date_passed = date.fromisoformat(yesterday_str)
                elif bill.passed and not bill.date_passed:
                    # Backfill if missing
                    bill.date_passed = date.fromisoformat(yesterday_str)

async def sync_votes(yesterday_str):
    # Use session 45-1 explicitly as requested
    votes_url = f"{BASE_URL}/votes/?session=45-1"
    
    while votes_url:
        votes_data = await fetch_json(votes_url)
        if not votes_data: break
        
        objects = votes_data.get('objects', [])
        if not objects: break
        
        for v_data in objects:
            vote_date = v_data.get('date')
            if not vote_date: continue
            
            v_date_obj = date.fromisoformat(vote_date)
            # If we encounter a vote older than our window (with some buffer), and assuming desc sort, we could stop.
            # But to be safe and thorough as requested, we just skip.
            # Optimization: if we are WAY past (e.g. 14 days), break to avoid scraping years of history.
            if v_date_obj < date.today() - timedelta(days=14):
                 # Assuming sorted by date desc, we can stop here.
                 votes_url = None
                 break

            if v_date_obj < date.today() - timedelta(days=7):
                continue
    
            vote_url = v_data['url'] # e.g. /votes/45-1/66/
            
            # Fetch ballots with pagination
            ballot_url = f"{BASE_URL}/votes/ballots/?vote={vote_url}"
            while ballot_url:
                ballot_data = await fetch_json(ballot_url)
                if not ballot_data: break
            
                with db_session:
                    for ballot in ballot_data.get('objects', []):
                        p_url = ballot.get('politician_url')
                        if not p_url: continue
                        
                        slug = p_url.strip('/').split('/')[-1]
                        mp = MP.get(slug=slug)
                        if mp:
                            if not VoteAttendance.exists(mp=mp, vote_url=vote_url):
                                VoteAttendance(mp=mp, vote_url=vote_url, attended=True, date=v_date_obj)
                
                # Pagination for ballots
                b_next = ballot_data.get('pagination', {}).get('next_url')
                if b_next:
                    ballot_url = f"https://openparliament.ca{b_next}" if b_next.startswith('/') else b_next
                else:
                    ballot_url = None

        # Pagination for votes
        if votes_url: # Only if we didn't break early
            v_next = votes_data.get('pagination', {}).get('next_url')
            if v_next:
                votes_url = f"https://openparliament.ca{v_next}" if v_next.startswith('/') else v_next
            else:
                votes_url = None

async def run_sync():
    yesterday = date.today() - timedelta(days=1)
    yesterday_str = yesterday.isoformat()
    
    print("Starting MP sync...")
    await sync_mps()
    
    with db_session:
        mps = select(m for m in MP)[:]
    
    print("Processing individual MP data...")
    # Process MPs
    for i, mp in enumerate(mps):
        await process_mp_data(mp, yesterday_str)
        if i % 10 == 0:
            await asyncio.sleep(0.1) 
    
    print("Syncing votes...")
    await sync_votes(yesterday_str)
    
    print("Cleaning up old data...")
    cleanup_old_data()
    
    print("Calculating scores...")
    calculate_all_scores()
    print("Sync complete.")

if __name__ == "__main__":
    from models import db
    # init_db is optimized for Postgres; using direct bind for SQLite to avoid arg conflicts
    db.bind(provider='sqlite', filename='db.sqlite', create_db=True)
    db.generate_mapping(create_tables=True)
    asyncio.run(run_sync())
