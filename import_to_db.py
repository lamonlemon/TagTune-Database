import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

def import_songs(json_file="songs_to_review.json"):
    if not os.path.exists(json_file):
        print(f"Error: {json_file} NOT found.")
        return

    print(f"Reading reviewed data from {json_file}...")
    with open(json_file, "r", encoding="utf-8") as f:
        songs_data = json.load(f)

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    for entry in songs_data:
        try:
            # 1. Handle Artist
            artist_name = entry.get('extracted_artist', 'Unknown')
            artist_res = supabase.table('artists').upsert({'name': artist_name}, on_conflict='name').execute()
            artist_id = artist_res.data[0]['artist_id']

            # 2. Handle Group
            group_id = None
            group_name = entry.get('ai_group')
            if group_name and group_name.lower() != "null" and group_name.strip() != "":
                group_res = supabase.table('groups').upsert({'name': group_name}, on_conflict='name').execute()
                group_id = group_res.data[0]['group_id']

            # 3. Handle Album
            album_id = None
            album_title = entry.get('album')
            if album_title and album_title.lower() != "none":
                album_res = supabase.table('albums').upsert({
                    'title': album_title,
                    'artist_id': artist_id
                }, on_conflict='title, artist_id').execute()
                album_id = album_res.data[0]['album_id']

            # 4. Insert Song (Primary Key 'song_index' is SERIAL, so it auto-increments in DB)
            song_payload = {
                'title': entry.get('extracted_title'),
                'artist_id': artist_id,
                'album_id': album_id,
                'group_id': group_id,
                'release_year': entry.get('release_year'),
                'url': entry.get('url'),
                'language': entry.get('ai_language')
            }
            
            # Using 'url' to handle conflicts (prevents double-entry for same song)
            song_res = supabase.table('songs').upsert(song_payload, on_conflict='url').execute()
            # This 'db_song_index' is the actual unique ID from Supabase
            db_song_index = song_res.data[0]['song_index']

            # 5. Handle original_song_id (If it's an original song, it points to itself)
            # For covers, you would manually update this to point to the original song's DB ID.
            if not entry.get('is_cover'):
                supabase.table('songs').update({'original_song_id': db_song_index}).eq('song_index', db_song_index).execute()

            # 6. Handle Genres
            ai_genres = entry.get('ai_genre', {})
            if ai_genres and isinstance(ai_genres, dict):
                # Ensure all required genre IDs are present
                p_id = ai_genres.get('primary')
                s_id = ai_genres.get('sub')
                m_id = ai_genres.get('micro')
                
                if p_id:
                    supabase.table('song_genres').upsert({
                        'song_id': db_song_index,
                        'primary_genre_id': p_id,
                        'sub_genre_id': s_id,
                        'micro_genre_id': m_id
                    }).execute()

            # 7. Handle Featuring & Producers
            # These artists are also added to the 'artists' table first
            for feat_name in entry.get('ai_featuring', []):
                if feat_name and feat_name.strip():
                    feat_res = supabase.table('artists').upsert({'name': feat_name}, on_conflict='name').execute()
                    feat_id = feat_res.data[0]['artist_id']
                    supabase.table('song_featuring').upsert({'song_id': db_song_index, 'artist_id': feat_id}).execute()

            for prod_name in entry.get('ai_producer', []):
                if prod_name and prod_name.strip():
                    prod_res = supabase.table('artists').upsert({'name': prod_name}, on_conflict='name').execute()
                    prod_id = prod_res.data[0]['artist_id']
                    supabase.table('song_producers').upsert({'song_id': db_song_index, 'artist_id': prod_id}).execute()

            print(f"Imported/Updated: {entry.get('extracted_title')}")
            
        except Exception as e:
            print(f"Error importing song {entry.get('extracted_title')}: {e}")

if __name__ == "__main__":
    import_songs()
