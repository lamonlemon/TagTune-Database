import json
import os

def merge_gemini():
    songs_file = "songs_to_review.json"
    gemini_file = "gemini_output.json"
    
    if not os.path.exists(songs_file) or not os.path.exists(gemini_file):
        print("Error: Required JSON files are missing.")
        return
        
    print(f"Loading {songs_file} and {gemini_file}...")
    
    with open(songs_file, "r", encoding="utf-8") as f:
        songs = json.load(f)
        
    with open(gemini_file, "r", encoding="utf-8") as f:
        gemini_data = json.load(f)
        
    ai_map = {item["index"]: item for item in gemini_data if "index" in item}
    
    merged_count = 0
    for song in songs:
        idx = song.get("index")
        if idx in ai_map:
            ai_meta = ai_map[idx]
            song["is_cover"] = ai_meta.get("is_cover", False)
            song["ai_group"] = ai_meta.get("group")
            song["ai_featuring"] = ai_meta.get("featuring", [])
            song["ai_producer"] = ai_meta.get("producer", [])
            song["ai_genre"] = ai_meta.get("genre", {})
            song["ai_language"] = ai_meta.get("language")
            song["confident"] = ai_meta.get("confident", 0)
            song["cover_artists"] = ai_meta.get("cover_artists", [])
            song["original_title"] = ai_meta.get("original_title")
            song["original_artist"] = ai_meta.get("original_artist")
            
            merged_count += 1
            
    with open(songs_file, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully merged {merged_count} outputs from {gemini_file} into {songs_file}!")

if __name__ == "__main__":
    merge_gemini()
