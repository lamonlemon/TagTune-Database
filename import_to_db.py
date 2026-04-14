import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

CHECKPOINT_FILE = "imported_checkpoint.txt"

def read_checkpoint():
    """Read the last successfully imported song index from the checkpoint file."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            content = f.read().strip()
            if content:
                return int(content)
    return 0

def write_checkpoint(index):
    """Write the last successfully imported song index to the checkpoint file."""
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(str(index))

def import_songs(json_file="songs_to_review.json"):
    if not os.path.exists(json_file):
        print(f"Error: {json_file} NOT found.")
        return

    print(f"Reading reviewed data from {json_file}...")
    with open(json_file, "r", encoding="utf-8") as f:
        songs_data = json.load(f)

    last_imported = read_checkpoint()
    if last_imported > 0:
        print(f"Resuming from checkpoint: last imported index = {last_imported}")

    # Filter out already-imported songs
    remaining = [s for s in songs_data if s.get('index', 0) > last_imported]

    if not remaining:
        print("All songs have already been imported. Nothing to do.")
        return

    print(f"Skipped {len(songs_data) - len(remaining)} already-imported songs. {len(remaining)} remaining.")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    for entry in remaining:
        song_index = entry.get('index', 0)
        try:
            # 1. Handle Artist
            if entry.get('is_cover') and entry.get('cover_artists'):
                artist_name = entry['cover_artists'][0]  # Main cover artist (channel owner)
            else:
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

            # 4. Determine original_song_id before insert
            orig_id = song_index
            if entry.get('is_cover'):
                original_url = entry.get('original_url')
                if original_url:
                    result = supabase.table('songs').select('song_index').eq('url', original_url).execute()
                    if result.data:
                        orig_id = result.data[0]['song_index']
                    else:
                        with open('cover_missing_original.log', 'a') as f:
                            f.write(f"[{song_index}] {entry.get('extracted_title')} → original not in DB: {original_url}\n")

            # 5. Insert Song (Supply song_index and original_song_id explicitly)
            song_payload = {
                'song_index': song_index,
                'title': entry.get('extracted_title'),
                'original_song_id': orig_id,
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

            # 6. Handle Genres (Only for original songs)
            if not entry.get('is_cover'):
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

            for cover_artist_name in entry.get('cover_artists', []):
                if cover_artist_name and cover_artist_name.strip():
                    ca_res = supabase.table('artists').upsert(
                        {'name': cover_artist_name}, on_conflict='name'
                    ).execute()
                    ca_id = ca_res.data[0]['artist_id']
                    supabase.table('song_featuring').upsert({
                        'song_id': db_song_index,
                        'artist_id': ca_id
                    }).execute()

            # Update checkpoint after successful import
            write_checkpoint(song_index)
            print(f"[{song_index}] Imported: {entry.get('extracted_title')}")
            
        except Exception as e:
            print(f"\n❌ Error importing song index {song_index} ({entry.get('extracted_title')}): {e}")
            print(f"Stopped. Re-run the script to resume from index {read_checkpoint()}.")
            return

    print(f"\n✅ All {len(remaining)} songs imported successfully!")

if __name__ == "__main__":
    import_songs()
