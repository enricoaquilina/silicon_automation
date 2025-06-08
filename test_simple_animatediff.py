#!/usr/bin/env python3
"""
Test AnimateDiff - Simple Approach
- Use AnimateDiff which we know works
- Very simple prompts
- Basic parameters only
"""

import os
import asyncio
import aiohttp
from datetime import datetime


async def test_animatediff_simple():
    """Test AnimateDiff with minimal parameters"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    print(f"🎬 ANIMATEDIFF SIMPLE TEST")
    print("=" * 40)
    
    # Very simple prompt
    simple_prompt = "a beautiful woman smiling"
    
    # Basic AnimateDiff payload
    payload = {
        "version": "beecf59c4aee8d81bf04f0381033dfa10dc16e845b4ae00d281e2fa377e48a9f",
        "input": {
            "prompt": simple_prompt,
            "num_inference_steps": 25,
            "guidance_scale": 7.5,
            "num_frames": 16
        }
    }
    
    headers = {
        "Authorization": f"Token {replicate_token}",
        "Content-Type": "application/json"
    }
    
    print(f"🚀 Testing AnimateDiff...")
    print(f"Prompt: {simple_prompt}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Submit prediction
            async with session.post("https://api.replicate.com/v1/predictions", 
                                  json=payload, headers=headers) as response:
                if response.status != 201:
                    error_text = await response.text()
                    print(f"❌ Submission failed: {response.status} - {error_text}")
                    return
                
                result = await response.json()
                prediction_id = result['id']
                print(f"   ✅ Prediction submitted: {prediction_id}")
            
            # Poll for results
            get_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
            start_time = datetime.now()
            
            while True:
                async with session.get(get_url, headers=headers) as response:
                    result = await response.json()
                    status = result['status']
                    elapsed = (datetime.now() - start_time).total_seconds()
                    
                    print(f"   📊 Status: {status} ({elapsed:.1f}s elapsed)")
                    
                    if status == 'succeeded':
                        video_url = result['output']
                        print(f"   🎉 SUCCESS! Video generation complete")
                        print(f"   🎥 Video URL: {video_url}")
                        
                        # Download video
                        output_file = f"animatediff_simple_{datetime.now().strftime('%H%M%S')}.mp4"
                        async with session.get(video_url) as video_response:
                            if video_response.status == 200:
                                with open(output_file, 'wb') as f:
                                    f.write(await video_response.read())
                                
                                size_mb = os.path.getsize(output_file) / 1024 / 1024
                                print(f"   💾 Downloaded: {output_file} ({size_mb:.1f}MB)")
                                return True
                            else:
                                print(f"   ❌ Failed to download video: {video_response.status}")
                        
                        return True
                        
                    elif status == 'failed':
                        error = result.get('error', 'Unknown error')
                        print(f"   ❌ FAILED: {error}")
                        return False
                    
                    await asyncio.sleep(5)
                    
                    # Timeout after 5 minutes
                    if elapsed > 300:
                        print(f"   ⏰ Timeout after 5 minutes")
                        return False
                        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_with_image_input():
    """Test AnimateDiff with image input (if supported)"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    print(f"\\n🎬 ANIMATEDIFF WITH IMAGE INPUT TEST")
    print("=" * 50)
    
    # Try text-to-video first, then see if image input works
    await test_animatediff_simple()


if __name__ == "__main__":
    asyncio.run(test_with_image_input())