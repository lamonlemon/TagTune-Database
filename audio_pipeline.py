import os
import json
import time
import subprocess
import urllib.parse
from dotenv import load_dotenv
from supabase import create_client, Client
import essentia.standard as es
import essentia
import numpy as np
import google.generativeai as genai

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
essentia.log.warningActive = False

# Load env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Checkpoint functions
CHECKPOINT_FILE = "audio_features_checkpoint.txt"
def get_processed_songs():
    if not os.path.exists(CHECKPOINT_FILE):
        return set()
    with open(CHECKPOINT_FILE, "r") as f:
        return set(int(line.strip()) for line in f if line.strip())

def mark_processed(song_id):
    with open(CHECKPOINT_FILE, "a") as f:
        f.write(f"{song_id}\n")

# Error logging
ERROR_FILE = "audio_features_errors.txt"
def log_error(song_id, msg):
    with open(ERROR_FILE, "a") as f:
        f.write(f"[{song_id}] {msg}\n")
    print(f"Error {song_id}: {msg}")

# Initialize models
print("Loading Essentia models...")
try:
    effnet = es.TensorflowPredictEffnetDiscogs(graphFilename="models/discogs-effnet-bs64-1.pb", output="PartitionedCall:1")
    dance_model = es.TensorflowPredict2D(graphFilename="models/danceability-discogs-effnet-1.pb", output="model/Softmax")
    acoustic_model = es.TensorflowPredict2D(graphFilename="models/mood_acoustic-discogs-effnet-1.pb", output="model/Softmax")

    musicnn = es.TensorflowPredictMusiCNN(graphFilename="models/msd-musicnn-1.pb", output="model/dense/BiasAdd")
    av_model = es.TensorflowPredict2D(graphFilename="models/deam-msd-musicnn-2.pb", output="model/Identity")
    print("All Essentia models loaded successfully")
except Exception as e:
    print(f"Warning: Could not load some Essentia models. Make sure they are in the models/ folder. Error: {e}")

def load_genres():
    genres = {}
    if os.path.exists("genre_list.txt"):
        with open("genre_list.txt", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    gid, gname = line.strip().split("=", 1)
                    genres[int(gid)] = gname
    return genres

GENRES_MAP = load_genres()

def extract_features(audio_path):
    audio_16k = es.MonoLoader(filename=audio_path, sampleRate=16000)()
    audio_44k = es.MonoLoader(filename=audio_path)()
    bpm, _, _, _, _ = es.RhythmExtractor2013()(audio_44k)
    
    emb_effnet = effnet(audio_16k)
    dance_preds = dance_model(emb_effnet)
    acoustic_preds = acoustic_model(emb_effnet)
    
    emb_musicnn = musicnn(audio_16k)
    av_preds = av_model(emb_musicnn)
    
    # We take the mean of the first class probability. 
    # Usually index 0 or 1 represents the target class. 
    danceability = float(np.mean(dance_preds[:, 0]))
    acousticness = float(np.mean(acoustic_preds[:, 0]))
    
    # DEAM output is [valence, arousal], range 1~9
    av_mean = np.mean(av_preds, axis=0)
    valence = round((float(av_mean[0]) - 1) / 8, 3) if len(av_mean) > 0 else 0.5
    energy  = round((float(av_mean[1]) - 1) / 8, 3) if len(av_mean) > 1 else 0.5
    
    audio_vec = np.mean(emb_musicnn, axis=0)
    audio_norm = np.linalg.norm(audio_vec)
    if audio_norm > 0:
        audio_vec = audio_vec / audio_norm

    return {
        "tempo": float(bpm),
        "energy": energy,
        "valence": valence,
        "danceability": danceability,
        "acousticness": acousticness,
        "audio_vector": audio_vec.tolist()
    }

def get_embedding(text):
    result = genai.embed_content(
        model="gemini-embedding-2",
        content=text
    )
    return result['embedding']

def download_audio(video_id, output_path):
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "--audio-quality", "128K",
        "-o", output_path,
        url
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise Exception(f"yt-dlp failed: {res.stderr.decode()}")

def main():
    try:
        start_line = int(input("Enter start line number: "))
        end_line = int(input("Enter end line number: "))
    except ValueError:
        print("Invalid input")
        return

    # Read processed_videos.txt
    if not os.path.exists("processed_videos.txt"):
        print("processed_videos.txt not found")
        return
        
    with open("processed_videos.txt", "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        
    if start_line < 1: start_line = 1
    if end_line > len(lines): end_line = len(lines)
    
    target_video_ids = lines[start_line-1 : end_line]
    processed_songs = get_processed_songs()
    OUTPUT_FILE = "audio_features_output.json"
    
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w") as f:
            f.write("[]")
            
    for idx, video_id in enumerate(target_video_ids):
        print(f"\nProcessing {video_id} ({idx+1}/{len(target_video_ids)})...")
        song_index = video_id # fallback
        temp_mp3 = f"temp_{video_id}.mp3"
        
        try:
            # 1. Look up song_index from Supabase
            res = supabase.table("songs").select("song_index, artist_id").ilike("url", f"%{video_id}%").execute()
            if not res.data:
                print(f"Warning: video_id {video_id} not found in Supabase songs table. Skipping.")
                continue
                
            song_index = res.data[0]['song_index']
            artist_id = res.data[0]['artist_id']
            
            if song_index in processed_songs:
                print(f"Song {song_index} already processed, skipping.")
                continue
                
            # 2. Fetch artist name
            artist_res = supabase.table("artists").select("name").eq("artist_id", artist_id).execute()
            artist_name = "Unknown"
            if artist_res.data:
                artist_name = artist_res.data[0]['name']
                
            # Fetch genres for the song
            genre_res = supabase.table("song_genres").select("primary_genre_id, sub_genre_id, micro_genre_id").eq("song_id", song_index).execute()
            genres_list = []
            if genre_res.data:
                row = genre_res.data[0]
                for gid_field in ["primary_genre_id", "sub_genre_id", "micro_genre_id"]:
                    gid = row.get(gid_field)
                    if gid and int(gid) in GENRES_MAP:
                        genres_list.append(GENRES_MAP[int(gid)])
                        
            genres_str = " ".join(genres_list)
            text_prompt = f"{artist_name}, {genres_str}".replace("  ", " ").strip()
                
            # 3. Download audio
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)
                
            print("Downloading audio...")
            download_audio(video_id, temp_mp3)
            
            # 4. Extract audio features
            print("Extracting audio features...")
            features = extract_features(temp_mp3)
            
            # 5. Generate embedding
            print(f"Generating embedding for text: '{text_prompt}'...")
            gemini_vec = get_embedding(text_prompt)
            
            # Convert to numpy and normalize
            g_vec = np.array(gemini_vec)
            g_norm = np.linalg.norm(g_vec)
            if g_norm > 0:
                g_vec = g_vec / g_norm
            
            # 6. Save result
            output_entry = {
                "song_id": song_index,
                "tempo": round(features["tempo"], 3),
                "energy": round(features["energy"], 3),
                "valence": round(features["valence"], 3),
                "danceability": round(features["danceability"], 3),
                "acousticness": round(features["acousticness"], 3),
                "artist_vector": g_vec.tolist(),
                "audio_vector": features["audio_vector"]
            }
            
            with open(OUTPUT_FILE, "r") as f:
                current_data = json.load(f)
            current_data.append(output_entry)
            with open(OUTPUT_FILE, "w") as f:
                json.dump(current_data, f, indent=2)
                
            # 7. Checkpoint
            mark_processed(song_index)
            
            # 8. Clean up
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)
            print(f"Successfully processed {video_id} (song_id: {song_index})")
            
            # Rate limit ~100 calls/min
            time.sleep(0.5)
            
        except Exception as e:
            log_error(song_index, str(e))
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)

if __name__ == "__main__":
    main()
