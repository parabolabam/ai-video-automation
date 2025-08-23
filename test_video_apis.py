#!/usr/bin/env python3
"""
Test script for video generation APIs
"""

import asyncio
import os
from dotenv import load_dotenv
from features.kie.video_apis import VideoGenerationAPI

load_dotenv()

async def test_video_apis():
    """Test different video generation providers"""
    test_prompt = "A beautiful sunset over a mountain landscape, cinematic view"
    
    # Test available providers
    providers = ['kie']
    
    for provider in providers:
        print(f"\n{'='*60}")
        print(f"Testing {provider.upper()} API")
        print('='*60)
        
        # Check if API key exists
        api_key_env = f"{provider.upper()}_API_KEY"
        if not os.getenv(api_key_env):
            print(f"⚠️  {api_key_env} not found - skipping {provider}")
            continue
        
        try:
            # Initialize API
            api = VideoGenerationAPI(provider)
            
            print("Using Kie provider")
            
            # Test video generation (short timeout for testing)
            print(f"🎬 Testing video generation with {provider}...")
            print(f"📝 Prompt: {test_prompt}")
            
            # For testing, we'll use a shorter duration and timeout
            video_path = await api.generate_video(test_prompt, duration=5, quality="standard")
            
            if video_path:
                print(f"✅ SUCCESS: Video generated at {video_path}")
                
                # Show file info
                if os.path.exists(video_path):
                    size = os.path.getsize(video_path)
                    print(f"📁 File size: {size:,} bytes")
                else:
                    print("⚠️  File path returned but file doesn't exist")
            else:
                print(f"❌ FAILED: No video generated")
                
        except ValueError as e:
            print(f"❌ SETUP ERROR: {e}")
        except Exception as e:
            print(f"❌ API ERROR: {e}")
    
    print(f"\n{'='*60}")
    print("Test completed!")
    print('='*60)

async def test_single_provider(provider: str):
    """Test a single provider"""
    test_prompt = "A cat playing with a ball of yarn, close-up view"
    
    print(f"Testing {provider.upper()} API")
    print(f"Prompt: {test_prompt}")
    
    try:
        api = VideoGenerationAPI(provider)
        print("Using Kie provider")
        
        video_path = await api.generate_video(test_prompt, duration=5, quality="fast")
        
        if video_path:
            print(f"✅ Success: {video_path}")
        else:
            print("❌ Failed to generate video")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific provider
        provider = sys.argv[1].lower()
        asyncio.run(test_single_provider(provider))
    else:
        # Test all providers
        print("🧪 Testing all available video generation APIs...")
        print("⏳ This may take several minutes...")
        asyncio.run(test_video_apis())