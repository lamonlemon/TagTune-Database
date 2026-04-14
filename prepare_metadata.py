import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from ytmusicapi import YTMusic
from services.youtube_service import get_playlist_videos, get_video_description
from services.ytmusic_service import get_song_metadata, get_playlist_videos_ytmusic
from services.gemini_service import analyze_songs

yt = YTMusic()

PROCESSED_FILE = "processed_videos.txt"

def extract_original_youtube_id(description):
    if not description: return None
    lines = description.split('\n')
    for line in lines:
        lower_line = line.lower()
        # Trigger keywords: English, Korean, Japanese, or the presence of a shortened YouTube link
        keywords = ['original', '원본', '본가', 'orig', '原曲', 'ご本家', 'youtu.be']
        if any(kw in lower_line for kw in keywords):
            # More robust regex for various YouTube URL formats (watch, shorts, embed, youtu.be)
            match = re.search(r'(?:v=|v\/|embed\/|shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})', line)
            if match:
                return match.group(1)
    return None

def load_processed_ids():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_ids(video_ids):
    if not video_ids:
        print("Warning: No video IDs to save to processed_videos.txt")
        return
    with open(PROCESSED_FILE, "a") as f:
        for vid in video_ids:
            f.write(f"{vid}\n")
    print(f"Saved {len(video_ids)} video IDs to {PROCESSED_FILE}.")

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
        
        # Cover detection is now handled by AI instead of hardcoded keywords
            
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
    batch_size = 150
    all_ai_results = []
    
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
            "is_cover": ai_meta.get("is_cover", False),  # AI judges this
            "ai_group": ai_meta.get("group"),
            "ai_featuring": ai_meta.get("featuring", []),
            "ai_producer": ai_meta.get("producer", []),
            "ai_genre": ai_meta.get("genre", {}),
            "ai_language": ai_meta.get("language"),
            "confident": ai_meta.get("confident", ai_meta.get("confident", 0)),
            "cover_artists": ai_meta.get("cover_artists", []),
            "original_title": ai_meta.get("original_title"),
            "original_artist": ai_meta.get("original_artist"),
            "original_youtube_id": ai_meta.get("original_youtube_id"),
            "original_url": f"https://music.youtube.com/watch?v={ai_meta.get('original_youtube_id')}" if ai_meta.get("original_youtube_id") else None
        }

        if combined.get("is_cover") and not combined.get("original_youtube_id"):
            desc = get_video_description(song['video_id'])
            if desc:
                original_yt_id_from_desc = extract_original_youtube_id(desc)
                if original_yt_id_from_desc:
                    try:
                        orig_details = yt.get_song(original_yt_id_from_desc)
                        if orig_details:
                            vDetails = orig_details.get("videoDetails", {})
                            search_title = vDetails.get("title", "")
                            search_artist = vDetails.get("author", "")
                            if search_title and search_artist:
                                search_results = yt.search(f"{search_title} {search_artist}", filter="songs", limit=1)
                                if search_results:
                                    top_result = search_results[0]
                                    combined["original_youtube_id"] = top_result.get("videoId")
                                    combined["original_url"] = f"https://music.youtube.com/watch?v={top_result.get('videoId')}"
                                    combined["original_title"] = top_result.get("title", combined.get("original_title"))
                                    artists_list = top_result.get("artists", [])
                                    if artists_list:
                                        combined["original_artist"] = ", ".join([a.get("name", "") for a in artists_list])
                                else:
                                    combined["original_youtube_id"] = original_yt_id_from_desc
                                    combined["original_url"] = f"https://music.youtube.com/watch?v={original_yt_id_from_desc}"
                            else:
                                combined["original_youtube_id"] = original_yt_id_from_desc
                                combined["original_url"] = f"https://music.youtube.com/watch?v={original_yt_id_from_desc}"
                        else:
                            combined["original_youtube_id"] = original_yt_id_from_desc
                            combined["original_url"] = f"https://music.youtube.com/watch?v={original_yt_id_from_desc}"
                    except Exception as e:
                        print(f"Error parsing original id from desc: {e}")
                        combined["original_youtube_id"] = original_yt_id_from_desc
                        combined["original_url"] = f"https://music.youtube.com/watch?v={original_yt_id_from_desc}"

            # If still missing, fallback to AI provided title/artist search
            if not combined.get("original_youtube_id"):
                original_title = combined.get("original_title")
                original_artist = combined.get("original_artist")
                if original_title and original_artist:
                    try:
                        search_results = yt.search(f"{original_title} {original_artist}", filter="songs", limit=3)
                        if search_results:
                            original_video_id = search_results[0].get("videoId")
                            if original_video_id:
                                combined["original_youtube_id"] = original_video_id
                                combined["original_url"] = f"https://music.youtube.com/watch?v={original_video_id}"
                    except Exception as e:
                        print(f"ytmusicapi search failed for original: {e}")

        # Log if original song is missing in processed_videos.txt
        if combined.get("is_cover"):
            orig_id = combined.get("original_youtube_id")
            if orig_id and orig_id not in processed_ids:
                with open("cover_missing_original.log", "a", encoding="utf-8") as f:
                    f.write(f"[{combined['index']}] {combined['video_title']} (Cover) -> Original {orig_id} NOT found in processed_videos.txt\n")

        new_output.append(combined)

    # 4. Combine with existing and save
    final_output = existing_data + new_output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
    
    # Track all newly processed IDs
    newly_processed_ids = [s['video_id'] for s in songs_data]
    save_processed_ids(newly_processed_ids)
    print(f"Done! {len(new_output)} new songs added to {output_file}. Total: {len(final_output)}.")

if __name__ == "__main__":
    playlist_id = input("Enter Playlist ID: ").strip()
    if playlist_id:
        api_choice = input("Which API to use for playlist extraction? (youtube/ytmusic) [default: ytmusic]: ").strip().lower()
        if not api_choice:
            api_choice = "ytmusic"
        prepare_metadata(playlist_id, api_choice=api_choice)
