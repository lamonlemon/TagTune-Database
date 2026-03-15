from ytmusicapi import YTMusic
import json

yt = YTMusic("browser.json")
video_id = "CgCVZdcKcqY"
song_id = "r6Eei81SuqE"

def print_info(vid):
    print(f"Info for {vid}:")
    try:
        details = yt.get_song(vid)
        videoDetails = details.get('videoDetails', {})
        print(f"  Title: {videoDetails.get('title')}")
        print(f"  Author: {videoDetails.get('author')}")
        print(f"  musicVideoType: {videoDetails.get('musicVideoType')}")
        
    except Exception as e:
        print(f"Error: {e}")

print_info(video_id)
print_info(song_id)

# Also test watch playlist
def watch_info(vid):
    try:
        w = yt.get_watch_playlist(videoId=vid)
        tracks = w.get('tracks', [])
        if tracks:
            t = tracks[0]
            print(f"Watch playlist type for {vid}: {t.get('resultType')} / {t.get('trackType')} / {t.get('length')}")
    except Exception as e:
        print(f"Error watch: {e}")

watch_info(video_id)
watch_info(song_id)
