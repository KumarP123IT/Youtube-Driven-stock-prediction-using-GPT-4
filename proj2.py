import os
import openai
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

def fetch_top_videos_with_subtitles(api_key, query, max_results=3):
    """Fetches the top YouTube videos for a given query and filters those with subtitles."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.search().list(
        part='snippet',
        q=query,
        type='video',
        maxResults=max_results,
        order='relevance'
    )
    search_response = request.execute()

    video_ids = [item['id']['videoId'] for item in search_response['items']]

    # Filter videos with subtitles enabled
    filtered_video_ids = []
    for video_id in video_ids:
        video_request = youtube.videos().list(
            part="contentDetails",
            id=video_id
        )
        video_response = video_request.execute()
        if 'caption' in video_response['items'][0]['contentDetails'] and \
                video_response['items'][0]['contentDetails']['caption'] == 'true':
            filtered_video_ids.append(video_id)

    return filtered_video_ids

def fetch_youtube_transcript(video_id):
    """Fetches the transcript of a YouTube video."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = " ".join([entry['text'] for entry in transcript])
        return full_transcript
    except Exception as e:
        print(f"Error fetching transcript for video {video_id}: {e}")
        return ""

def predict_stock_price(transcripts):
    """Predicts the stock price based on multiple transcripts using OpenAI GPT model."""
    openai.api_key = os.getenv("OPENAI_API_KEY") 

    combined_transcript = " ".join(filter(None, transcripts))  # Combine all valid transcripts
    if not combined_transcript:
        print("No valid transcripts found for prediction.")
        return None

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": f"Based on the following transcripts, predict the stock price in 24 hours:\n{combined_transcript}\nProvide only a single numerical value as the prediction."}
            ],
            temperature=0.7
        )
        prediction = response['choices'][0]['message']['content'].strip()
        return float(prediction)
    except Exception as e:
        print(f"Error predicting stock price: {e}")
        return None

def analyze_asset(api_key, asset_name):
    """Analyze an asset by fetching top videos, transcripts, and predicting stock price."""
    print(f"Fetching top videos for '{asset_name}'...")
    video_ids = fetch_top_videos_with_subtitles(api_key, asset_name)

    if not video_ids:
        print("No videos found.")
        return

    transcripts = []
    for video_id in video_ids:
        print(f"Fetching transcript for video ID: {video_id}")
        transcript = fetch_youtube_transcript(video_id)
        if transcript:
            transcripts.append(transcript)

    if not transcripts:
        print("No transcripts available for the videos.")
        return

    print("\nPredicting stock price...")
    predicted_price = predict_stock_price(transcripts)
    if predicted_price is not None:
        print(f"Predicted Stock Price for '{asset_name}': {predicted_price:.2f}")
    else:
        print("Prediction failed.")

def main():
    # File containing asset names
    file_path = "assets.txt"

    # Step 1: Read asset names
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            asset_names = file.read().splitlines()
    else:
        print(f"Assets file not found: {file_path}")
        return

    # Step 2: Analyze each asset
    api_key = "" # your API key
    for asset_name in asset_names:
        print(f"\nAnalyzing asset: {asset_name}")
        analyze_asset(api_key, asset_name)

if __name__ == "__main__":
    main()
