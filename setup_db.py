import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

def populate_genres():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL or SUPABASE_SECRET_KEY not found in .env")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("Populating genres from genre_list.txt...")
    genres = []
    seen_ids = set()
    
    if not os.path.exists("genre_list.txt"):
        print("Error: genre_list.txt not found.")
        return

    with open("genre_list.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
                
            try:
                gid_str, name = line.split("=", 1)
                gid = int(gid_str)
                
                if gid in seen_ids:
                    continue
                seen_ids.add(gid)
                
                level = 1 if gid <= 50 else (2 if gid < 1000 else 3)
                genres.append({
                    "genre_id": gid,
                    "name": name.strip(),
                    "level": level
                })
            except ValueError:
                continue
    
    print(f"Parsed {len(genres)} unique genres. Inserting...")
    try:
        # Batch upsert genres
        batch_size = 340
        for i in range(0, len(genres), batch_size):
            batch = genres[i:i+batch_size]
            supabase.table("genres").upsert(batch).execute()
        print("Genres populated successfully.")
    except Exception as e:
        print(f"Error populating genres: {e}")

if __name__ == "__main__":
    populate_genres()
