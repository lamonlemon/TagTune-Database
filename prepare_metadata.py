import json
import os
from concurrent.futures import ThreadPoolExecutor
from services.youtube_service import get_playlist_videos
from services.ytmusic_service import get_song_metadata, get_playlist_videos_ytmusic
from services.gemini_service import analyze_songs

PROCESSED_FILE = "processed_videos.txt"

def load_processed_ids():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_ids(video_ids):
    with open(PROCESSED_FILE, "a") as f:
        for vid in video_ids:
            f.write(f"{vid}\n")

def prepare_metadata(playlist_id, api_choice="ytmusic", output_file="songs_to_review.json"):
    processed_ids = load_processed_ids()
    
    # Load existing data from the output file to append to it
    existing_data = []
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            print(f"Loaded {len(existing_data)} existing songs from {output_file}.")
        except Exception as e:
            print(f"Warning: Could not read {output_file}, starting fresh: {e}")

    # Determine next index
    next_index = max([item.get('index', 0) for item in existing_data], default=0) + 1
    
    print(f"Fetching videos from playlist: {playlist_id} using {api_choice.upper()} API...")
    if api_choice == "youtube":
        videos = get_playlist_videos(playlist_id)
    else:
        videos = get_playlist_videos_ytmusic(playlist_id)
    print(f"Found {len(videos)} videos.")

    # 1. Gather basic metadata for NEW videos only
    skipped_count = 0
    videos_to_process = []
    
    for video in videos:
        if video['video_id'] in processed_ids:
            skipped_count += 1
            continue
        
        # Pre-assign index
        video['assigned_index'] = next_index
        videos_to_process.append(video)
        next_index += 1

    def fetch_meta_for_video(vid_data):
        print(f"[{vid_data['assigned_index']}] Extracting metadata for: {vid_data['title']}...")
        try:
            yt_meta = get_song_metadata(vid_data['video_id'])
        except Exception as e:
            print(f"Error: {e}")
            yt_meta = None
        
        song_entry = {
            "index": vid_data['assigned_index'],
            "video_title": vid_data['title'],
            "url": vid_data['url'],
            "video_id": vid_data['video_id'],
            "extracted_title": yt_meta.get('title') if yt_meta else vid_data['title'],
            "extracted_artist": yt_meta.get('artist') if yt_meta else "Unknown",
            "album": yt_meta.get('album') if yt_meta else None,
            "release_year": yt_meta.get('year') if yt_meta else None,
            "is_cover": False
        }
        
        # Cover detection
        cover_keywords = ["cover", "커버", "remix", "리믹스", "live", "라이브", "歌ってみた", "カバー"]
        if any(kw in vid_data['title'].lower() for kw in cover_keywords):
            song_entry["is_cover"] = True
            
        return song_entry

    songs_data = []
    if videos_to_process:
        print(f"Extracting metadata for {len(videos_to_process)} songs using 8 threads...")
        with ThreadPoolExecutor(max_workers=8) as executor:
            # map preserves order
            songs_data = list(executor.map(fetch_meta_for_video, videos_to_process))

    print(f"Skipped {skipped_count} already processed songs.")
    if not songs_data:
        print("No new songs to process.")
        return

    # 2. Process through Gemini in batches
    batch_size = 155
    all_ai_results = []
    new_processed_vids = []
    
    for i in range(0, len(songs_data), batch_size):
        batch = songs_data[i:i+batch_size]
        # Pass both index and text to keep Gemini results synced
        ai_input_data = [
            {"index": s['index'], "text": f"{s['video_title']} - {s['extracted_artist']}"} 
            for s in batch
        ]
        
        print(f"Calling Gemini for batch {i//batch_size + 1}...")
        ai_results = analyze_songs(ai_input_data)
        all_ai_results.extend(ai_results)
        
        # Record successful extracted IDs
        new_processed_vids.extend([s['video_id'] for s in batch])

    # 3. Merge AI results back into main data
    ai_map = {}
    for item in all_ai_results:
        if isinstance(item, dict) and 'index' in item:
            try:
                ai_map[int(item['index'])] = item
            except (ValueError, TypeError):
                continue
    
    new_output = []
    for song in songs_data:
        idx = song['index']
        ai_meta = ai_map.get(idx, {})
        
        combined = {
            **song,
            "ai_group": ai_meta.get("group"),
            "ai_featuring": ai_meta.get("featuring", []),
            "ai_producer": ai_meta.get("producer", []),
            "ai_genre": ai_meta.get("genre", {}),
            "ai_language": ai_meta.get("language"),
            "confident": ai_meta.get("confident", 0)
        }
        new_output.append(combined)

    # 4. Combine with existing and save
    final_output = existing_data + new_output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
    
    save_processed_ids(new_processed_vids)
    print(f"Done! {len(new_output)} new songs added to {output_file}. Total: {len(final_output)}.")

if __name__ == "__main__":
    playlist_id = input("Enter Playlist ID: ").strip()
    if playlist_id:
        api_choice = input("Which API to use for playlist extraction? (youtube/ytmusic) [default: ytmusic]: ").strip().lower()
        if not api_choice:
            api_choice = "ytmusic"
        prepare_metadata(playlist_id, api_choice=api_choice)
