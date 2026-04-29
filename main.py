#!/usr/bin/env python3
"""
News to Video Pipeline

This script fetches news articles and generates a video from them.
"""

import requests
from moviepy.editor import *
import os

def fetch_news(api_key, query="technology"):
    """Fetch news articles from NewsAPI."""
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    return response.json().get('articles', [])

def create_video_from_articles(articles, output_file="news_video.mp4"):
    """Create a video from news articles."""
    clips = []
    for article in articles[:5]:  # Limit to 5 articles
        title = article['title']
        description = article['description'] or ""
        text = f"{title}\n\n{description}"
        
        # Create text clip
        txt_clip = TextClip(text, fontsize=50, color='white', bg_color='black').set_duration(5)
        clips.append(txt_clip)
    
    # Concatenate clips
    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile(output_file, fps=24)

if __name__ == "__main__":
    # Replace with your NewsAPI key
    API_KEY = os.getenv("NEWS_API_KEY", "your_api_key_here")
    articles = fetch_news(API_KEY)
    create_video_from_articles(articles)