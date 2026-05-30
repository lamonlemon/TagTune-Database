import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CHECKPOINT_FILE = "audio_db_checkpoint.txt"
ERROR_FILE = "audio_db_errors.txt"

def get_processed_ids():
    if not os.path.exists(CHECKPOINT_FILE):
        return set()
    with open(CHECKPOINT_FILE, "r") as f:
        return set(int(line.strip()) for line in f if line.strip())

def mark_processed(song_id):
    with open(CHECKPOINT_FILE, "a") as f:
        f.write(f"{song_id}\n")

def log_error(song_id, msg):
    with open(ERROR_FILE, "a") as f:
        f.write(f"[{song_id}] {msg}\n")
    print(f"Error {song_id}: {msg}")

def main():
    INPUT_FILE = "audio_features_output.json"
    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} not found.")
        return
        
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)
        
    processed = get_processed_ids()
    
    print(f"Found {len(data)} entries in {INPUT_FILE}.")
    
    for entry in data:
        song_id = entry['song_id']
        if song_id in processed:
            continue
            
        try:
            # Upsert song_audio_features
            features_payload = {
                "song_id": song_id,
                "tempo": entry['tempo'],
                "energy": entry['energy'],
                "valence": entry['valence'],
                "danceability": entry['danceability'],
                "acousticness": entry['acousticness']
            }
            res_feat = supabase.table("song_audio_features").upsert(features_payload).execute()
            
            # Upsert song_vectors
            vector_payload = {
                "song_id": song_id,
                "artist_vector": entry['artist_vector'],
                "audio_vector": entry['audio_vector']
            }
            res_vec = supabase.table("song_vectors").upsert(vector_payload).execute()
            
            mark_processed(song_id)
            print(f"Successfully inserted audio features and vector for song {song_id}. {len(entry['artist_vector'])}, {len(entry['audio_vector'])}")
            
        except Exception as e:
            log_error(song_id, str(e))

if __name__ == "__main__":
    main()
