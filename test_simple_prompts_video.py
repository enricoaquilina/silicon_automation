#!/usr/bin/env python3
"""
Test Video Models with Simple Prompts Only
- Use the exact simple prompts that worked
- Test with upscaled images as input
- Focus on working models: Kling v2.0 and Minimax
"""

import os
import asyncio
import base64
import aiohttp
from datetime import datetime
from typing import Dict, Any


async def test_video_with_simple_prompt(model_name: str, version: str, 
                                      image_path: str, simple_prompt: str) -> Dict[str, Any]:
    """Test video generation with simple prompt"""
    
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        return {"success": False, "error": "No API token"}
    
    # Convert image to data URI
    with open(image_path, 'rb') as f:
        image_data = f.read()
    image_b64 = base64.b64encode(image_data).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{image_b64}"
    
    # Model-specific payloads
    if model_name == "kling-v2.0":
        payload = {
            "version": version,
            "input": {
                "prompt": simple_prompt,
                "start_image": data_uri,
                "duration": 5,
                "aspect_ratio": "1:1"
            }
        }
    elif model_name == "minimax-video-01":
        payload = {
            "version": version,
            "input": {
                "prompt": simple_prompt,
                "first_frame_image": data_uri
            }
        }
    else:
        return {"success": False, "error": f"Unknown model: {model_name}"}
    
    headers = {
        "Authorization": f"Token {replicate_token}",
        "Content-Type": "application/json"
    }
    
    print(f"🎬 Testing {model_name}")
    print(f"   📝 Prompt: '{simple_prompt}'")
    print(f"   📸 Image: {os.path.basename(image_path)}")
    
    start_time = datetime.now()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Submit prediction
            async with session.post("https://api.replicate.com/v1/predictions", 
                                  json=payload, headers=headers) as response:
                if response.status != 201:
                    error_text = await response.text()
                    print(f"   ❌ Submission failed: {response.status} - {error_text}")
                    return {"success": False, "error": f"Submission failed: {response.status}"}
                
                result = await response.json()
                prediction_id = result['id']
                print(f"   ✅ Prediction submitted: {prediction_id}")
            
            # Poll for completion
            get_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
            
            while True:
                async with session.get(get_url, headers=headers) as response:
                    result = await response.json()
                    status = result['status']
                    elapsed = (datetime.now() - start_time).total_seconds()
                    
                    if status == 'succeeded':
                        video_urls = result['output']
                        if isinstance(video_urls, list):
                            video_url = video_urls[0] if video_urls else None
                        else:
                            video_url = video_urls
                        
                        if video_url:
                            # Download video
                            output_filename = f"{model_name}_{simple_prompt.replace(' ', '_')[:20]}_{datetime.now().strftime('%H%M%S')}.mp4"
                            
                            async with session.get(video_url) as video_response:
                                if video_response.status == 200:
                                    with open(output_filename, 'wb') as f:
                                        f.write(await video_response.read())
                                    
                                    size_mb = os.path.getsize(output_filename) / 1024 / 1024
                                    
                                    print(f"   🎉 SUCCESS! {output_filename} ({size_mb:.1f}MB, {elapsed:.1f}s)")
                                    
                                    return {
                                        "success": True,
                                        "model": model_name,
                                        "prompt": simple_prompt,
                                        "video_file": output_filename,
                                        "size_mb": size_mb,
                                        "generation_time": elapsed,
                                        "video_url": video_url
                                    }
                        
                        return {"success": False, "error": "No video URL in response"}
                    
                    elif status == 'failed':
                        error = result.get('error', 'Unknown error')
                        print(f"   ❌ FAILED after {elapsed:.1f}s: {error}")
                        return {"success": False, "error": error, "time": elapsed}
                    
                    # Continue polling
                    if elapsed < 300:  # 5 minute timeout
                        await asyncio.sleep(5)
                    else:
                        print(f"   ⏰ Timeout after {elapsed:.1f}s")
                        return {"success": False, "error": "Timeout", "time": elapsed}
        
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"   ❌ Exception after {elapsed:.1f}s: {e}")
        return {"success": False, "error": str(e), "time": elapsed}


async def main():
    """Test video models with simple prompts that work"""
    
    print(f"🎬 VIDEO GENERATION - SIMPLE PROMPTS ONLY")
    print("=" * 50)
    
    # Find test image
    test_image = "downloaded_verify_images/verify_C0xFHGOrBN7/recraft_model/upscaled_images/C0xFHGOrBN7_recraft_fixed_recraft_v1_upscaled.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return
    
    # Simple prompts that work
    simple_prompts = [
        "gentle movement and subtle animation",
        "soft motion",
        "gentle flow",
        "subtle movement"
    ]
    
    # Models to test
    models = {
        "kling-v2.0": "03c47b845aed8a009e0f83a45be0a2100ca11a7077e667a33224a54e85b2965c",
        "minimax-video-01": "c8bcc4751328608bb75043b3af7bed4eabcf1a6c0a478d50a4cf57fa04bd5101"
    }
    
    results = []
    
    # Test each model with the first simple prompt that worked
    test_prompt = simple_prompts[0]  # "gentle movement and subtle animation"
    
    print(f"\\n🎯 Testing with working prompt: '{test_prompt}'")
    print(f"📸 Using image: {os.path.basename(test_image)}")
    print("=" * 50)
    
    for model_name, version in models.items():
        print(f"\\n🚀 Testing {model_name}...")
        result = await test_video_with_simple_prompt(model_name, version, test_image, test_prompt)
        results.append(result)
        
        # Wait between tests to avoid rate limiting
        await asyncio.sleep(2)
    
    # Summary
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"\\n🎉 TESTING COMPLETE!")
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    
    if successful:
        print(f"\\n📁 Successfully generated videos:")
        for result in successful:
            print(f"   🎥 {result['video_file']} ({result['size_mb']:.1f}MB, {result['generation_time']:.1f}s)")
    
    if failed:
        print(f"\\n❌ Failed attempts:")
        for result in failed:
            print(f"   ⚠️ {result.get('model', 'Unknown')}: {result.get('error', 'Unknown error')}")
    
    # If successful, test with other simple prompts
    if successful:
        print(f"\\n🔄 Testing other simple prompts...")
        for prompt in simple_prompts[1:2]:  # Test one more prompt
            print(f"\\n🎯 Testing prompt: '{prompt}'")
            
            # Test with best performing model
            best_model = successful[0]['model']
            best_version = models[best_model]
            
            result = await test_video_with_simple_prompt(best_model, best_version, test_image, prompt)
            if result.get("success"):
                print(f"   ✅ Additional success: {result['video_file']}")


if __name__ == "__main__":
    asyncio.run(main())