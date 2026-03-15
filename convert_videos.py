from ytmusicapi import YTMusic
import json
import time

yt = YTMusic()

def run_conversion():
    file_json = "songs_to_review.json"
    file_txt = "processed_videos.txt"
    
    with open(file_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    with open(file_txt, "r", encoding="utf-8") as f:
        processed_videos = [line.strip() for line in f if line.strip()]

    print(f"Found {len(data)} songs to review.")
    modifications = 0

    for idx, song in enumerate(data):
        vid = song.get("video_id")
        if not vid:
            continue
            
        try:
            details = yt.get_song(vid)
            videoDetails = details.get('videoDetails', {})
            mv_type = videoDetails.get('musicVideoType')
            
            # If it's an official music video or user generated content (not Audio Track Video)
            if mv_type != 'MUSIC_VIDEO_TYPE_ATV' and mv_type is not None:
                title = videoDetails.get('title') or song.get('video_title')
                author = videoDetails.get('author') or song.get('extracted_artist')
                
                query = f"{title} {author}"
                search_results = yt.search(query, filter="songs", limit=1)
                
                if search_results:
                    top_result = search_results[0]
                    new_vid = top_result.get('videoId')
                    
                    if new_vid and new_vid != vid:
                        print(f"[{song['index']}] Converting {vid} ({mv_type}) -> {new_vid} ({top_result.get('title')} - {', '.join([a.get('name', '') for a in top_result.get('artists', [])])})")
                        
                        # Update JSON
                        song["video_id"] = new_vid
                        song["url"] = f"https://music.youtube.com/watch?v={new_vid}"
                        
                        # Update txt (find and replace)
                        if vid in processed_videos:
                            txt_idx = processed_videos.index(vid)
                            processed_videos[txt_idx] = new_vid
                        
                        modifications += 1
                        print(f"Worked on {modifications}th song")
                        time.sleep(0.5) # simple rate limit
        except Exception as e:
            print(f"Error checking {vid}: {e}")

    if modifications > 0:
        with open(file_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        with open(file_txt, "w", encoding="utf-8") as f:
            for v in processed_videos:
                f.write(f"{v}\n")
        print(f"\nSuccessfully updated {modifications} links.")
    else:
        print("\nNo unoptimized video links found.")

if __name__ == "__main__":
    run_conversion()
