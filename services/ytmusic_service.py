from ytmusicapi import YTMusic
import json
import os

# Initialize YTMusic with browser.json if available
if os.path.exists("../browser.json"):
    yt = YTMusic("../browser.json")
else:
    yt = YTMusic()

def get_song_metadata(video_id):
    """
    Tries to get Artist, Title, Album, Year from YTMusic.
    Uses get_song for base metadata and search for album/year.
    """
    try:
        # 1. Get base info via get_song
        song_details = yt.get_song(video_id)
        video_details = song_details.get('videoDetails', {})
        
        # User requested: use title and author from videoDetails
        metadata = {
            'title': video_details.get('title'),
            'artist': video_details.get('author'), # This is usually the channel/uploader name
            'album': None,
            'year': None
        }

        # 2. Use search to find more precise metadata if possible
        search_query = f"{metadata['title']} {metadata['artist']}"
        search_results = yt.search(search_query, filter="songs", limit=1)
        
        if search_results:
            result = search_results[0]
            # If the search result title is similar, use its album info
            # Usually search results are more structured
            metadata['album'] = result.get('album', {}).get('name')
            # Extract year if available in search result
            album_id = result.get('album', {}).get('id')
            if album_id:
                album_info = yt.get_album(album_id)
                metadata['year'] = album_info.get('year', "None")
            
        return metadata
    except Exception as e:
        print(f"Error fetching metadata for {video_id}: {e}")
        return None

def get_playlist_videos_ytmusic(playlist_id):
    """
    Fetches video IDs and titles from a YouTube Music playlist.
    """
    try:
        # limit=None retrieves all tracks in the playlist
        playlist = yt.get_playlist(playlist_id, limit=None)
        videos = []
        for track in playlist.get('tracks', []):
            if track.get('videoId'):
                videos.append({
                    'video_id': track['videoId'],
                    'title': track['title'],
                    'url': f"https://music.youtube.com/watch?v={track['videoId']}"
                })
        return videos
    except Exception as e:
        print(f"Error fetching YTMusic playlist {playlist_id}: {e}")
        return []


if __name__ == "__main__":
    # Test with a known video ID
    test_id = "q-FP6bSqyy4" # Jung Kook - Seven
    print(get_song_metadata(test_id))
