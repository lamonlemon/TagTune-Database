import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_playlist_videos(playlist_id):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    videos = []
    next_page_token = None
    
    while True:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            video_id = item['contentDetails']['videoId']
            title = item['snippet']['title']
            videos.append({
                'video_id': video_id,
                'title': title,
                'url': f"https://music.youtube.com/watch?v={video_id}"
            })
            
        next_page_token = response.get('nextPageToken')
        print(f"nextPageToken: {next_page_token}")
        if not next_page_token:
            break
            
    return videos

def get_video_description(video_id):
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        if response.get('items'):
            return response['items'][0]['snippet'].get('description', '')
    except Exception as e:
        print(f"Error fetching description for {video_id}: {e}")
    return ""

if __name__ == "__main__":
    # Test with a known playlist ID
    test_id = "RDCLAK5uy_lreHzXUqXcoHfNcdPKh-aL-h4k5fckfY4" # Example public playlist
    try:
        results = get_playlist_videos(test_id)
        print(f"Found {len(results)} videos.")
        for v in results[:5]:
            print(f"- {v['title']} ({v['video_id']})")
    except Exception as e:
        print(f"Error: {e}")
