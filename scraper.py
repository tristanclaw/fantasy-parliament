import httpx
import asyncio
from datetime import datetime, date, timedelta
from urllib.parse import quote
from pony.orm import db_session, select, desc, commit
from models import MP, DailyScore, db
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openparliament.ca"

PARTY_MAPPING = {
    "Conservative": "CPC",
    "Liberal": "Lib",
    "NDP": "NDP",
    "Bloc Québécois": "BQ",
    "Green Party": "GPC",
    "Independent": "Ind"
}

SEMAPHORE_LIMIT = 5

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
    return f"https://www.ourcommons.ca/Content/Parliamentarians/Images/OfficialMPPhotos/45/{last}{first}_{party_code}.jpg"

async def fetch_json(client, url):
    if '?' not in url and not url.endswith('/') and '&' not in url:
        url += '/'
    try:
        headers = {
            "Accept": "application/json",
            "User-Agent": "FantasyParliament/1.0 (contact@example.com)"
        }
        response = await client.get(url, params={"format": "json"}, headers=headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def save_mps_sync(objects):
    total_created = 0
    total_synced = 0
    page_slugs = set()
    with db_session:
        for mp_data in objects:
            party_info = mp_data.get('current_party')
            if not party_info:
                continue
                
            party_name = party_info.get('short_name', {}).get('en')
            riding_info = mp_data.get('current_riding')
            riding_name = riding_info.get('name', {}).get('en') if riding_info else None
            
            slug = mp_data['url'].strip('/').split('/')[-1]
            page_slugs.add(slug)
            name = mp_data['name']
            
            mp = MP.get(slug=slug)
            if not mp:
                mp = MP(name=name, slug=slug)
                total_created += 1
            
            mp.party = party_name
            mp.riding = riding_name
            mp.active = True # Ensure active if found

            api_image = mp_data.get('image')
            if api_image:
                mp.image_url = f"https://api.openparliament.ca{api_image}"
            else:
                mp.image_url = construct_image_url(name, party_name)
            
            total_synced += 1
    return total_synced, total_created, page_slugs

def mark_inactive_mps(seen_slugs):
    with db_session:
        # Find MPs that are currently active but not in seen_slugs
        # Note: In Pony, we iterate and check
        count = 0
        for mp in MP.select(lambda m: m.active == True):
            if mp.slug not in seen_slugs:
                mp.active = False
                count += 1
                print(f"MP Sync: Marked {mp.name} ({mp.slug}) as inactive")
    return count

async def sync_mps(client):
    url = f"{BASE_URL}/politicians/?limit=500"
    total_synced = 0
    total_created = 0
    all_seen_slugs = set()
    
    print(f"Scraper: Starting MP sync...")
    seen_urls = set()
    while url and url not in seen_urls:
        seen_urls.add(url)
        data = await fetch_json(client, url)
        if not data: break
        
        objects = data.get('objects', [])
        if not objects: break
        
        synced, created, page_slugs = await asyncio.to_thread(save_mps_sync, objects)
        total_synced += synced
        total_created += created
        all_seen_slugs.update(page_slugs)
            
        next_path = data.get('pagination', {}).get('next_url')
        url = f"{BASE_URL}{next_path}" if next_path else None
        
    print(f"Synced {total_synced} MPs ({total_created} new)")
    
    # Mark inactive
    inactive_count = await asyncio.to_thread(mark_inactive_mps, all_seen_slugs)
    print(f"Marked {inactive_count} MPs as inactive")

def update_scores_sync(target_date, mp_points, mp_breakdown):
    """
    Update DailyScore, total_score, and score_breakdown for MPs.
    mp_points: dict { slug: points }
    mp_breakdown: dict { slug: {speeches: n, votes: n, bills: n} }
    """
    updated_count = 0
    with db_session:
        # First ensure all relevant MPs have a DailyScore record for the date
        for slug, pts in mp_points.items():
            mp = MP.get(slug=slug)
            if not mp:
                continue
            
            score_record = DailyScore.get(mp=mp, date=target_date)
            if not score_record:
                DailyScore(
                    mp=mp,
                    mp_name=mp.name,
                    party=mp.party,
                    riding=mp.riding,
                    points_today=pts,
                    date=target_date
                )
            else:
                score_record.points_today = pts
            updated_count += 1
            
        # Recalculate total_score and score_breakdown for updated MPs
        for slug in mp_points.keys():
            mp = MP.get(slug=slug)
            if mp:
                # Total score from all daily scores
                total = sum(ds.points_today for ds in mp.daily_scores)
                mp.total_score = total
                
                # Calculate cumulative breakdown from all DailyScore records
                # For now, use the provided breakdown for today as a simple approach
                breakdown = mp_breakdown.get(slug, {"speeches": 0, "votes": 0, "bills": 0})
                mp.score_breakdown = breakdown

    return updated_count

async def sync_daily_activity(client, target_date):
    date_str = target_date.isoformat()
    print(f"Syncing activity for {date_str}...")
    
    mp_points = {} 
    mp_breakdown = {}  # Track counts separately

    def add_points(slug, pts, category):
        if slug not in mp_points:
            mp_points[slug] = 0
            mp_breakdown[slug] = {"speeches": 0, "votes": 0, "bills": 0}
        mp_points[slug] += pts
        mp_breakdown[slug][category] = mp_breakdown[slug].get(category, 0) + 1

    # 1. Speeches (1 pt)
    print("Fetching speeches...")
    speech_url = f"{BASE_URL}/speeches/?date={date_str}&limit=500"
    while speech_url:
        data = await fetch_json(client, speech_url)
        if not data: break
        
        for speech in data.get('objects', []):
            p_url = speech.get('politician_url')
            if p_url:
                slug = p_url.strip('/').split('/')[-1]
                add_points(slug, 1, 'speeches')
        
        next_path = data.get('pagination', {}).get('next_url')
        speech_url = f"{BASE_URL}{next_path}" if next_path else None

    # 2. Votes (1 pt)
    print("Fetching votes...")
    votes_url = f"{BASE_URL}/votes/?date={date_str}&limit=500"
    while votes_url:
        data = await fetch_json(client, votes_url)
        if not data: break
        
        vote_objects = data.get('objects', [])
        for vote in vote_objects:
            vote_url_api = vote.get('url') # e.g. /votes/44-1/123/
            if not vote_url_api: continue

            # Fetch ballots
            ballot_url = f"{BASE_URL}/votes/ballots/?vote={vote_url_api}&limit=500"
            while ballot_url:
                b_data = await fetch_json(client, ballot_url)
                if not b_data: break
                
                for ballot in b_data.get('objects', []):
                    p_url = ballot.get('politician_url')
                    if p_url:
                        slug = p_url.strip('/').split('/')[-1]
                        add_points(slug, 1, 'votes') # Attendance point

                b_next = b_data.get('pagination', {}).get('next_url')
                ballot_url = f"{BASE_URL}{b_next}" if b_next else None
        
        next_path = data.get('pagination', {}).get('next_url')
        votes_url = f"{BASE_URL}{next_path}" if next_path else None

    # 3. Bills Passed (2 pts)
    # Check bills that became law on target_date
    # OpenParliament API /bills/?law=True doesn't easily filter by date assented.
    # We fetch recently updated bills and check manually.
    print("Fetching recent bills for passed status...")
    bills_url = f"{BASE_URL}/bills/?limit=100" 
    while bills_url:
        data = await fetch_json(client, bills_url)
        if not data: break
        
        processed_count = 0
        for bill in data.get('objects', []):
            # Check if it is passed
            if bill.get('passed') is True:
                # Check date_assented if available
                passed_date_str = bill.get('date_assented')
                if passed_date_str and passed_date_str == date_str:
                     sponsor_url = bill.get('sponsor_politician_url')
                     if sponsor_url:
                         slug = sponsor_url.strip('/').split('/')[-1]
                         add_points(slug, 2, 'bills')
                         print(f"Awarded 2 points to {slug} for bill {bill.get('number')}")

        # Only check first page of recent bills
        break

    print(f"Saving scores for {len(mp_points)} MPs...")
    updated = await asyncio.to_thread(update_scores_sync, target_date, mp_points, mp_breakdown)
    print(f"Updated {updated} records.")

async def run_sync():
    client = httpx.AsyncClient(timeout=60.0)
    
    try:
        # Sync MPs roster
        await sync_mps(client)
        
        # Sync past 7 days for initial data backfill
        today = date.today()
        for days_ago in range(7):
            target_date = today - timedelta(days=days_ago)
            print(f"Syncing {target_date}...")
            await sync_daily_activity(client, target_date)

    except Exception as e:
        print(f"CRITICAL ERROR in run_sync: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.aclose()

async def run_sync_mps_only():
    client = httpx.AsyncClient(timeout=60.0)
    try:
        await sync_mps(client)
    except Exception as e:
        print(f"CRITICAL ERROR in run_sync_mps_only: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.aclose()


if __name__ == "__main__":
    # Local dev testing
    from models import db
    db.bind(provider='sqlite', filename='db.sqlite', create_db=True)
    db.generate_mapping(create_tables=True)
    asyncio.run(run_sync())
