#!/usr/bin/env python3
"""
Simple Video Model Test
- Test one video model at a time
- Use Kling v2.0 which the user confirmed works
"""

import os
import asyncio
import base64
import aiohttp
from datetime import datetime


async def test_kling_v2():
    """Test Kling v2.0 model"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Find test image
    test_image = "downloaded_verify_images/verify_C0xFHGOrBN7/recraft_model/upscaled_images/C0xFHGOrBN7_recraft_fixed_recraft_v1_upscaled.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return
    
    print(f"🎬 KLING V2.0 VIDEO TEST")
    print(f"Test Image: {os.path.basename(test_image)}")
    print("=" * 50)
    
    # Convert image to data URI
    with open(test_image, 'rb') as f:
        image_data = f.read()
    image_b64 = base64.b64encode(image_data).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{image_b64}"
    
    # Create prompt
    prompt = """SiliconSentiments digital art transformation: Abstract geometric design with futuristic elements
    
STYLE: Futuristic digital illustration, technological aesthetics, geometric patterns
MOVEMENT: Gentle geometric transformations, flowing data particles, pulsing elements
CAMERA: Smooth cinematic movement, subtle effects
QUALITY: High-definition, crisp details
MOOD: Innovative, technological, artistic"""
    
    # API payload
    payload = {
        "version": "03c47b845aed8a009e0f83a45be0a2100ca11a7077e667a33224a54e85b2965c",
        "input": {
            "prompt": prompt,
            "start_image": data_uri,
            "duration": 5,
            "aspect_ratio": "1:1"
        }
    }
    
    headers = {
        "Authorization": f"Token {replicate_token}",
        "Content-Type": "application/json"
    }
    
    print(f"🚀 Submitting Kling v2.0 prediction...")
    
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
                        video_urls = result['output']
                        print(f"   🎉 SUCCESS! Video generation complete")
                        print(f"   🎥 Video URL: {video_urls}")
                        
                        # Download video
                        if isinstance(video_urls, list) and video_urls:
                            video_url = video_urls[0]
                        else:
                            video_url = video_urls
                        
                        output_file = f"kling_v2_test_{datetime.now().strftime('%H%M%S')}.mp4"
                        async with session.get(video_url) as video_response:
                            if video_response.status == 200:
                                with open(output_file, 'wb') as f:
                                    f.write(await video_response.read())
                                
                                size_mb = os.path.getsize(output_file) / 1024 / 1024
                                print(f"   💾 Downloaded: {output_file} ({size_mb:.1f}MB)")
                            else:
                                print(f"   ❌ Failed to download video: {video_response.status}")
                        
                        return True
                        
                    elif status == 'failed':
                        error = result.get('error', 'Unknown error')
                        print(f"   ❌ FAILED: {error}")
                        return False
                    
                    await asyncio.sleep(5)  # Check every 5 seconds
                    
                    # Timeout after 5 minutes
                    if elapsed > 300:
                        print(f"   ⏰ Timeout after 5 minutes")
                        return False
                        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_kling_v2())