import os
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build

def get_video_description(video_id):
    # Load environment variables from .env
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key:
        print("Error: YOUTUBE_API_KEY not found in .env file.")
        return

    try:
        # Build the YouTube service
        youtube = build("youtube", "v3", developerKey=api_key)
        
        # Request video details
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        
        if not response.get("items"):
            print(f"Error: No video found with ID {video_id}")
            return
            
        # Extract description
        snippet = response["items"][0]["snippet"]
        title = snippet.get("title", "No Title")
        description = snippet.get("description", "No description available.")
        
        print("\n" + "="*50)
        print(f"TITLE: {title}")
        print("="*50)
        print(description)
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    # Check if video ID is provided as a command line argument
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
    else:
        # Otherwise, prompt the user for input
        video_id = input("Enter YouTube Video ID: ").strip()
        
    if video_id:
        # Handle full URLs if the user pastes them
        if "v=" in video_id:
            video_id = video_id.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_id:
            video_id = video_id.split("youtu.be/")[1].split("?")[0]
            
        get_video_description(video_id)
    else:
        print("No Video ID provided.")

if __name__ == "__main__":
    main()
