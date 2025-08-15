#!/usr/bin/env python3
"""
AI Video Automation Pipeline
Automatically generates creative video prompts using OpenAI, 
creates videos with Gemini's Veo, and uploads to YouTube Shorts.
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
import aiohttp
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import google.generativeai as genai
from google import genai as google_genai
import openai
import time
import requests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# YouTube API scopes
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

class VideoAutomationPipeline:
    def __init__(self):
        self.openai_client = None
        self.gemini_client = None
        self.youtube_service = None
        self.setup_apis()
    
    def setup_apis(self):
        """Initialize API clients"""
        try:
            # OpenAI setup
            self.openai_client = openai.AsyncOpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
            
            # Gemini setup for Veo 3
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_client = google_genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            
            # YouTube setup
            self.youtube_service = self._get_youtube_service()
            
            logger.info("API clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize API clients: {e}")
            raise
    
    def _get_youtube_service(self):
        """Authenticate and return YouTube API service"""
        creds = None
        token_file = 'youtube_token.json'
        credentials_file = 'youtube_credentials.json'
        
        # Load existing token
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, YOUTUBE_SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    logger.warning("YouTube credentials file not found. YouTube upload will be disabled.")
                    return None
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, YOUTUBE_SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('youtube', 'v3', credentials=creds)
    
    async def generate_creative_prompt(self) -> str:
        """Generate a creative video prompt using OpenAI"""
        try:
            logger.info("Generating creative prompt with OpenAI...")
            
            system_prompt = """You are a creative video content generator. Generate a single, engaging video prompt for a short vertical video (under 60 seconds) that would work well for YouTube Shorts.

The prompt should be:
- Visually interesting and dynamic
- Suitable for vertical video format
- Engaging for social media audience
- Clear and specific enough for AI video generation
- Original and creative

Focus on topics like: nature, abstract art, futuristic concepts, satisfying visuals, or trending themes.

Return ONLY the video prompt, nothing else."""

            user_prompt = f"Generate a creative video prompt for today ({datetime.now().strftime('%Y-%m-%d')}). Make it unique and engaging."
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.8
            )
            
            prompt = response.choices[0].message.content.strip()
            logger.info(f"Generated prompt: {prompt}")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to generate prompt with OpenAI: {e}")
            # Fallback prompt
            fallback_prompts = [
                "A mesmerizing timelapse of clouds forming and dissolving over a mountain range at sunset",
                "Abstract flowing liquid metal with rainbow reflections in slow motion",
                "A futuristic city with flying cars and neon lights, cinematic view",
                "Underwater scene with bioluminescent jellyfish dancing in the deep ocean",
                "Close-up of colorful paint drops falling into water in super slow motion"
            ]
            import random
            return random.choice(fallback_prompts)
    
    async def generate_video_with_veo3(self, prompt: str) -> Optional[str]:
        """Generate video using Gemini's Veo 3 model"""
        try:
            logger.info(f"Generating video with Veo 3 using prompt: {prompt}")
            
            # Optimize prompt for vertical video (YouTube Shorts)
            optimized_prompt = f"Vertical 9:16 aspect ratio video: {prompt}. High quality, engaging, suitable for social media shorts."
            
            # Use Veo 3 Fast for cost-effectiveness ($0.40/sec vs $0.75/sec)
            model = 'veo-3.0-fast-generate-preview'  # or 'veo-3.0-generate-preview' for higher quality
            
            logger.info(f"Starting Veo 3 generation with model: {model}")
            
            # Generate video with Veo 3
            response = self.gemini_client.models.generate_content(
                model=model,
                contents=[optimized_prompt]
            )
            
            # Wait for generation to complete
            logger.info("Video generation started, waiting for completion...")
            
            # Poll for completion (Veo 3 can take 11 seconds to 6 minutes)
            max_wait_time = 600  # 10 minutes max wait
            check_interval = 15  # Check every 15 seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                try:
                    # Check if video is ready
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content.parts:
                            # Video is ready, download it
                            video_part = candidate.content.parts[0]
                            if hasattr(video_part, 'file_data'):
                                return await self._download_video(video_part.file_data)
                    
                    # Wait before next check
                    logger.info(f"Video still processing... ({elapsed_time}s elapsed)")
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
                    
                except Exception as poll_error:
                    logger.warning(f"Error checking video status: {poll_error}")
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
            
            logger.error("Video generation timed out")
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate video with Veo 3: {e}")
            
            # Check for specific error types
            if "quota" in str(e).lower():
                logger.error("Veo 3 quota exceeded. Consider upgrading your plan or trying later.")
            elif "billing" in str(e).lower():
                logger.error("Billing not enabled. Please enable billing in Google Cloud Console.")
            elif "permission" in str(e).lower():
                logger.error("API access denied. Check your API key and permissions.")
            
            return None
    
    async def _download_video(self, file_data) -> Optional[str]:
        """Download generated video from Google's servers"""
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"veo3_video_{timestamp}.mp4"
            video_path = os.path.join(tempfile.gettempdir(), video_filename)
            
            # Download video file
            if hasattr(file_data, 'uri'):
                # Direct URI download
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_data.uri) as response:
                        if response.status == 200:
                            async with aiofiles.open(video_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(1024):
                                    await f.write(chunk)
                            logger.info(f"Video downloaded successfully: {video_path}")
                            return video_path
            
            elif hasattr(file_data, 'data'):
                # Direct binary data
                async with aiofiles.open(video_path, 'wb') as f:
                    await f.write(file_data.data)
                logger.info(f"Video saved successfully: {video_path}")
                return video_path
            
            logger.error("No valid video data found in response")
            return None
            
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            return None
    
    async def upload_to_youtube(self, video_path: str, title: str, description: str) -> Optional[str]:
        """Upload video to YouTube as Shorts"""
        if not self.youtube_service:
            logger.warning("YouTube service not available. Skipping upload.")
            return None
        
        try:
            logger.info(f"Uploading video to YouTube: {video_path}")
            
            # YouTube Shorts specifications
            body = {
                'snippet': {
                    'title': title[:100],  # YouTube title limit
                    'description': f"{description}\n\n#Shorts #AIGenerated #VideoArt",
                    'tags': ['shorts', 'ai', 'generated', 'art', 'creative'],
                    'categoryId': '22',  # People & Blogs
                    'defaultLanguage': 'en',
                    'defaultAudioLanguage': 'en'
                },
                'status': {
                    'privacyStatus': 'public',  # Can be 'private', 'unlisted', or 'public'
                    'selfDeclaredMadeForKids': False
                }
            }
            
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/mp4'
            )
            
            request = self.youtube_service.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = request.execute()
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"Video uploaded successfully: {video_url}")
            return video_url
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to upload to YouTube: {e}")
            return None
    
    async def run_pipeline(self):
        """Run the complete automation pipeline"""
        try:
            logger.info("Starting video automation pipeline...")
            
            # Step 1: Generate creative prompt
            prompt = await self.generate_creative_prompt()
            
            # Step 2: Generate video with Veo 3
            video_path = await self.generate_video_with_veo3(prompt)
            
            if not video_path:
                logger.warning("Video generation failed or not available. Pipeline stopped.")
                return False
            
            # Step 3: Upload to YouTube
            title = f"AI Generated: {prompt[:50]}..."
            description = f"Created with AI: {prompt}"
            
            video_url = await self.upload_to_youtube(video_path, title, description)
            
            if video_url:
                logger.info(f"Pipeline completed successfully! Video: {video_url}")
                return True
            else:
                logger.error("Pipeline failed at YouTube upload step")
                return False
                
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return False

async def main():
    """Main function to run the pipeline"""
    try:
        pipeline = VideoAutomationPipeline()
        success = await pipeline.run_pipeline()
        
        if success:
            logger.info("Video automation completed successfully!")
        else:
            logger.error("Video automation failed!")
            
    except Exception as e:
        logger.error(f"Main execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
