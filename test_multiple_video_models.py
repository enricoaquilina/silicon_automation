#!/usr/bin/env python3
"""
Test Multiple Video Models - Simplified
- Test working video models with simple prompts
- Use upscaled images as input for animation
- Focus on models that work reliably
"""

import os
import asyncio
import base64
import aiohttp
from datetime import datetime
from typing import Dict, List, Any


class SimpleVideoTester:
    """Simple video model tester with working models"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
        self.api_url = "https://api.replicate.com/v1/predictions"
        
        # Working video models (verified)
        self.models = {
            "kling-v2.0": {
                "version": "03c47b845aed8a009e0f83a45be0a2100ca11a7077e667a33224a54e85b2965c",
                "description": "Kling v2.0 - 5s videos in 720p",
                "cost_per_video": 0.0005,  # $0.0001/s * 5s
                "input_params": {
                    "prompt": "required",
                    "start_image": "optional",
                    "duration": 5,
                    "aspect_ratio": "1:1"
                }
            },
            "minimax-video-01": {
                "version": "c8bcc4751328608bb75043b3af7bed4eabcf1a6c0a478d50a4cf57fa04bd5101",
                "description": "Minimax Video-01 (Hailuo) - 6s videos",
                "cost_per_video": 0.006,  # $0.001/s * 6s
                "input_params": {
                    "prompt": "required",
                    "first_frame_image": "optional"
                }
            }
        }
    
    def image_to_data_uri(self, image_path: str) -> str:
        """Convert image to data URI"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    async def test_model(self, model_key: str, image_path: str, simple_prompt: str) -> Dict[str, Any]:
        """Test a specific video model"""
        
        if model_key not in self.models:
            return {"success": False, "error": f"Model {model_key} not available"}
        
        model_config = self.models[model_key]
        
        print(f"🎬 Testing {model_key}: {model_config['description']}")
        
        # Convert image to data URI
        image_uri = self.image_to_data_uri(image_path)
        
        # Model-specific payload
        if model_key == "kling-v2.0":
            payload = {
                "version": model_config["version"],
                "input": {
                    "prompt": simple_prompt,
                    "start_image": image_uri,
                    "duration": 5,
                    "aspect_ratio": "1:1"
                }
            }
        elif model_key == "minimax-video-01":
            payload = {
                "version": model_config["version"],
                "input": {
                    "prompt": simple_prompt,
                    "first_frame_image": image_uri
                }
            }
        
        headers = {
            "Authorization": f"Token {self.replicate_token}",
            "Content-Type": "application/json"
        }
        
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Submit prediction
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 201:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Submission failed: {response.status} - {error_text}",
                            "model": model_key
                        }
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   ✅ Prediction submitted: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.api_url}/{prediction_id}"
                
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
                            
                            # Download video
                            if video_url:
                                output_filename = f"{model_key}_{os.path.splitext(os.path.basename(image_path))[0]}_{datetime.now().strftime('%H%M%S')}.mp4"
                                
                                async with session.get(video_url) as video_response:
                                    if video_response.status == 200:
                                        with open(output_filename, 'wb') as f:
                                            f.write(await video_response.read())
                                        
                                        size_mb = os.path.getsize(output_filename) / 1024 / 1024
                                        
                                        print(f"   🎉 SUCCESS! Downloaded: {output_filename} ({size_mb:.1f}MB, {elapsed:.1f}s)")
                                        
                                        return {
                                            "success": True,
                                            "model": model_key,
                                            "video_url": video_url,
                                            "output_file": output_filename,
                                            "size_mb": size_mb,
                                            "generation_time": elapsed,
                                            "cost": model_config["cost_per_video"],
                                            "prediction_id": prediction_id
                                        }
                                    else:
                                        return {
                                            "success": False,
                                            "error": f"Failed to download video: {video_response.status}",
                                            "model": model_key
                                        }
                            else:
                                return {
                                    "success": False,
                                    "error": "No video URL in response",
                                    "model": model_key
                                }
                        
                        elif status == 'failed':
                            error = result.get('error', 'Unknown error')
                            print(f"   ❌ FAILED: {error}")
                            return {
                                "success": False,
                                "error": error,
                                "model": model_key,
                                "generation_time": elapsed
                            }
                        
                        # Continue polling
                        await asyncio.sleep(5)
                        
                        # Timeout after 5 minutes
                        if elapsed > 300:
                            return {
                                "success": False,
                                "error": "Timeout after 5 minutes",
                                "model": model_key,
                                "generation_time": elapsed
                            }
        
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"   ❌ Exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "model": model_key,
                "generation_time": elapsed
            }


async def main():
    """Test multiple video models with simple prompts"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Find upscaled test images
    base_dir = "downloaded_verify_images/verify_C0xFHGOrBN7"
    test_images = []
    
    for model in ["recraft", "flux", "sdxl", "kandinsky"]:
        model_dir = os.path.join(base_dir, f"{model}_model", "upscaled_images")
        if os.path.exists(model_dir):
            images = [f for f in os.listdir(model_dir) if f.endswith("_upscaled.jpg")]
            if images:
                # Take first upscaled image from each model
                test_images.append(os.path.join(model_dir, images[0]))
    
    if not test_images:
        print(f"❌ No upscaled images found in {base_dir}")
        return
    
    print(f"🎬 VIDEO MODEL TESTING - SIMPLE APPROACH")
    print(f"Found {len(test_images)} upscaled test images")
    for img in test_images:
        print(f"   📸 {os.path.basename(img)}")
    print("=" * 60)
    
    # Simple test prompts
    simple_prompts = [
        "Gentle movement and subtle animation",
        "Flowing geometric patterns",
        "Soft glowing effects"
    ]
    
    tester = SimpleVideoTester(replicate_token)
    
    # Test each model with first image and first prompt
    test_image = test_images[0]  # Use recraft upscaled image
    test_prompt = simple_prompts[0]  # Use first simple prompt
    
    print(f"\\n🎯 Testing with:")
    print(f"   Image: {os.path.basename(test_image)}")
    print(f"   Prompt: {test_prompt}")
    print("=" * 40)
    
    results = []
    
    for model_key in tester.models.keys():
        print(f"\\n🚀 Testing {model_key}...")
        result = await tester.test_model(model_key, test_image, test_prompt)
        results.append(result)
        
        if result.get("success"):
            print(f"   ✅ {model_key}: Generated in {result['generation_time']:.1f}s (${result['cost']:.4f})")
        else:
            print(f"   ❌ {model_key}: {result.get('error', 'Unknown error')}")
    
    # Summary
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"\\n🎉 TESTING COMPLETE!")
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        total_cost = sum(r.get("cost", 0) for r in successful)
        avg_time = sum(r.get("generation_time", 0) for r in successful) / len(successful)
        print(f"💰 Total cost: ${total_cost:.4f}")
        print(f"⏱️ Average time: {avg_time:.1f}s")
        
        print(f"\\n📁 Generated videos:")
        for result in successful:
            if result.get("output_file"):
                print(f"   🎥 {result['output_file']} ({result['size_mb']:.1f}MB)")


if __name__ == "__main__":
    asyncio.run(main())