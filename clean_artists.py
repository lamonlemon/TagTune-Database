import json
import os

file_path = "songs_to_review.json"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

modified_count = 0

for song in data:
    artist = song.get("extracted_artist", "")
    if not artist:
        continue
    
    original_artist = artist
    
    if ',' in artist or '&' in artist:
        # Split by comma first, take the first element
        first_part = artist.split(',')[0].strip()
        # Then split by ampersand, take the first element
        first_part = first_part.split('&')[0].strip()
        
        if original_artist != first_part:
            print(f"[{song['index']}] '{original_artist}' -> '{first_part}'")
            song["extracted_artist"] = first_part
            modified_count += 1

if modified_count > 0:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Successfully updated {modified_count} songs.")
else:
    print("No changes needed.")
