import json

with open("test.json") as f:
    songs = json.load(f)

with open("ai_fixed.json") as f:
    ai = json.load(f)

for i in range(len(songs)):
    songs[i]["ai_group"] = ai[i]["group"]
    songs[i]["ai_featuring"] = ai[i]["featuring"]
    songs[i]["ai_producer"] = ai[i]["producer"]
    songs[i]["ai_genre"] = ai[i]["genre"]
    songs[i]["ai_language"] = ai[i]["language"]
    songs[i]["confident"] = ai[i]["confident"]

with open("merged.json", "w") as f:
    json.dump(songs, f, ensure_ascii=False, indent=2)