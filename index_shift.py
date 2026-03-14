import json
import os

def fix_indices():
    file_json = "songs_to_review.json"
    file_txt = "processed_videos.txt"
    
    if not os.path.exists(file_json) or not os.path.exists(file_txt):
        print("Error: Required files not found.")
        return

    with open(file_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    with open(file_txt, "r", encoding="utf-8") as f:
        processed_videos = [line.strip() for line in f if line.strip()]

    # Sort data by 'index' to ensure ascending order
    data.sort(key=lambda x: x.get("index", 0))

    existing_indices = [song["index"] for song in data]
    max_index = max(existing_indices) if existing_indices else 0
    
    missing_indices = []
    # Collect missing indices
    all_indices_set = set(existing_indices)
    for i in range(1, max_index + 1):
        if i not in all_indices_set:
            missing_indices.append(i)

    if not missing_indices:
        print("No missing indices found. Everything is continuous.")
        return

    print(f"Found {len(missing_indices)} missing indices.")
    print(f"Missing indices: {missing_indices}")

    # Remove lines from processed_videos.txt corresponding to missing indices
    # We delete in reverse order to ensure that list indices of unprocessed items don't shift
    for i in sorted(missing_indices, reverse=True):
        list_idx = i - 1
        if 0 <= list_idx < len(processed_videos):
            removed = processed_videos.pop(list_idx)
            print(f"Removed line {i} (Video ID: {removed}) from processed_videos.txt")
        else:
            print(f"Warning: Missing index {i} is out of bounds for processed_videos.txt (length: {len(processed_videos)})")

    # Shift indices in JSON
    print("Shifting indices in songs_to_review.json...")
    for new_idx, song in enumerate(data, start=1):
        song["index"] = new_idx

    # Save JSON back
    with open(file_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Save processed_videos.txt back
    with open(file_txt, "w", encoding="utf-8") as f:
        for vid in processed_videos:
            f.write(f"{vid}\n")

    print(f"\nSuccessfully shifted all indices.")
    print(f"Total songs remaining: {len(data)}")
    print(f"Total processed videos running: {len(processed_videos)}")

if __name__ == "__main__":
    fix_indices()