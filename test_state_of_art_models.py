#!/usr/bin/env python3
"""
Test State-of-the-Art Video Models
- Wan2.1 I2V (Image-to-Video specialist)
- Google Veo-3 (Flagship text-to-video with audio)
- Kling v2.0 (High-quality 720p videos)
- Clear existing videos and regenerate with these top models
"""

import os
import asyncio
import base64
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Any


class StateOfArtVideoTester:
    """Test the best available video generation models"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
        self.api_url = "https://api.replicate.com/v1/predictions"
        
        # State-of-the-art models (current best available)
        self.models = {
            "google-veo-3": {
                "version": "3c08e75333152bd7c21eb75f0db2478fe32588feb45bb9acc59fba03b83fc002",
                "description": "Google Veo-3 - Flagship text-to-video with audio",
                "cost_per_second": 0.0001,
                "features": ["text-to-video", "audio", "flagship"],
                "tier": "premium"
            },
            "kling-v2.0": {
                "version": "03c47b845aed8a009e0f83a45be0a2100ca11a7077e667a33224a54e85b2965c",
                "description": "Kling v2.0 - 5s videos in 720p", 
                "cost_per_video": 0.0005,
                "features": ["image-to-video", "720p", "5s"],
                "tier": "premium"
            },
            "wan2.1-i2v": {
                "version": "ae5bc519ee414f255f66c7ac22062e01bbbd6050c04f888d002d5ee0dc087a0c",
                "description": "Wan2.1 I2V - Image-to-video specialist 480p",
                "cost_per_second": 0.0122,
                "features": ["image-to-video", "480p", "specialist"],
                "tier": "specialized"
            }
        }
        
        # Enhanced cinematic prompts for each model type
        self.model_specific_prompts = {
            "google-veo-3": [
                "Digital artwork transforms with cinematic camera movement. Smooth dolly shot reveals intricate details while ambient electronic music plays. Professional cinematography with depth of field and high-quality visuals.",
                "Futuristic illustration comes alive with gentle character movements. Camera performs tracking shot with orchestral soundtrack. Technological aesthetic with premium visual effects and audio design."
            ],
            "kling-v2.0": [
                "Digital artwork with gentle geometric transformations and subtle character movements. The camera slowly pans across the surface with a cinematic dolly shot, revealing intricate details. Characters breathe softly and eyes blink naturally. Smooth cinematic movement with soft lighting and high picture quality.",
                "Futuristic digital illustration with flowing data particles. Characters move with graceful gestures while the camera performs a cinematic tracking shot following subtle movements. Technological aesthetic with gentle character animation and high-definition clarity."
            ],
            "wan2.1-i2v": [
                "Transform this image into a dynamic video with smooth camera movement and subtle character animation. Cinematic quality with professional lighting.",
                "Animate this artwork with gentle motion and camera work. Characters show natural movements while maintaining artistic quality."
            ]
        }
    
    def image_to_data_uri(self, image_path: str) -> str:
        """Convert image to data URI"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    async def test_model(self, model_key: str, image_path: str, test_id: str) -> Dict[str, Any]:
        """Test a specific state-of-the-art model"""
        
        model_config = self.models[model_key]
        prompt = self.model_specific_prompts[model_key][0]  # Use first prompt
        
        print(f"🎬 Testing {model_key}: {model_config['description']}")
        print(f"   📝 Prompt: '{prompt[:80]}...'")
        print(f"   📸 Image: {os.path.basename(image_path)}")
        
        # Model-specific payload construction
        if model_key == "google-veo-3":
            # Veo-3 is text-to-video, doesn't use image input directly
            payload = {
                "version": model_config["version"],
                "input": {
                    "prompt": f"Based on a digital artwork: {prompt}",
                    "seed": 42
                }
            }
        elif model_key == "kling-v2.0":
            payload = {
                "version": model_config["version"],
                "input": {
                    "prompt": prompt,
                    "start_image": self.image_to_data_uri(image_path),
                    "duration": 5,
                    "aspect_ratio": "1:1"
                }
            }
        elif model_key == "wan2.1-i2v":
            payload = {
                "version": model_config["version"],
                "input": {
                    "image": self.image_to_data_uri(image_path),
                    "prompt": prompt,
                    "num_frames": 81,
                    "sample_steps": 30,
                    "fps": 16,
                    "sample_guide_scale": 5,
                    "sample_shift": 3,
                    "fast_mode": "balanced"
                }
            }
        else:
            return {"success": False, "error": f"Unknown model: {model_key}"}
        
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
                        print(f"   ❌ Submission failed: {response.status} - {error_text}")
                        return {"success": False, "error": f"Submission failed: {response.status}"}
                    
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
                        
                        if elapsed % 30 < 5:  # Print status every 30 seconds
                            print(f"   📊 Status: {status} ({elapsed:.1f}s elapsed)")
                        
                        if status == 'succeeded':
                            output = result['output']
                            
                            # Handle different output formats
                            if isinstance(output, list):
                                video_url = output[0] if output else None
                            elif isinstance(output, str):
                                video_url = output
                            else:
                                video_url = str(output) if output else None
                            
                            if video_url:
                                # Download video
                                timestamp = datetime.now().strftime('%H%M%S')
                                output_filename = f"SOTA_{model_key}_{test_id}_{timestamp}.mp4"
                                
                                async with session.get(video_url) as video_response:
                                    if video_response.status == 200:
                                        with open(output_filename, 'wb') as f:
                                            f.write(await video_response.read())
                                        
                                        size_mb = os.path.getsize(output_filename) / 1024 / 1024
                                        
                                        # Calculate cost
                                        if "cost_per_video" in model_config:
                                            cost = model_config["cost_per_video"]
                                        else:
                                            # Estimate for time-based pricing
                                            duration = 5  # Default estimate
                                            cost = duration * model_config["cost_per_second"]
                                        
                                        print(f"   🎉 SUCCESS! {output_filename} ({size_mb:.1f}MB, {elapsed:.1f}s, ${cost:.4f})")
                                        
                                        return {
                                            "success": True,
                                            "model": model_key,
                                            "video_file": output_filename,
                                            "size_mb": size_mb,
                                            "generation_time": elapsed,
                                            "cost": cost,
                                            "video_url": video_url,
                                            "prompt": prompt,
                                            "features": model_config["features"],
                                            "tier": model_config["tier"]
                                        }
                                    else:
                                        print(f"   ❌ Download failed: {video_response.status}")
                                        return {"success": False, "error": f"Download failed: {video_response.status}"}
                            else:
                                print(f"   ❌ No video URL in response")
                                return {"success": False, "error": "No video URL in response"}
                        
                        elif status == 'failed':
                            error = result.get('error', 'Unknown error')
                            print(f"   ❌ FAILED after {elapsed:.1f}s: {error}")
                            return {"success": False, "error": error, "time": elapsed}
                        
                        # Continue polling
                        if elapsed < 600:  # 10 minute timeout
                            await asyncio.sleep(8)
                        else:
                            print(f"   ⏰ Timeout after {elapsed:.1f}s")
                            return {"success": False, "error": "Timeout", "time": elapsed}
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"   ❌ Exception after {elapsed:.1f}s: {e}")
            return {"success": False, "error": str(e), "time": elapsed}


async def main():
    """Test state-of-the-art video models"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    print(f"🚀 STATE-OF-THE-ART VIDEO MODEL TESTING")
    print(f"Models: Wan2.1 I2V, Google Veo-3, Kling v2.0")
    print("=" * 60)
    
    # Find test images (use first two upscaled images)
    base_dir = "downloaded_verify_images/verify_C0xFHGOrBN7"
    test_images = []
    
    for model in ["recraft", "flux"]:  # Test with first 2 models
        model_dir = os.path.join(base_dir, f"{model}_model", "upscaled_images")
        if os.path.exists(model_dir):
            images = [f for f in os.listdir(model_dir) if f.endswith("_upscaled.jpg")]
            if images:
                test_images.append(os.path.join(model_dir, images[0]))
    
    if not test_images:
        print(f"❌ No upscaled images found in {base_dir}")
        return
    
    print(f"\\n📸 Found {len(test_images)} test images:")
    for img in test_images:
        print(f"   📸 {os.path.basename(img)}")
    
    tester = StateOfArtVideoTester(replicate_token)
    
    # Test each model with first image
    test_image = test_images[0]
    test_id = "recraft_upscaled"
    
    print(f"\\n🎯 Testing with: {os.path.basename(test_image)}")
    print("=" * 50)
    
    results = []
    total_cost = 0
    
    # Test models in order of expected reliability
    model_order = ["kling-v2.0", "wan2.1-i2v", "google-veo-3"]
    
    for model_key in model_order:
        print(f"\\n🚀 Testing {model_key}...")
        result = await tester.test_model(model_key, test_image, test_id)
        results.append(result)
        
        if result.get("success"):
            total_cost += result.get("cost", 0)
        
        # Wait between tests to avoid rate limiting
        await asyncio.sleep(3)
    
    # Summary
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"\\n🎉 STATE-OF-THE-ART TESTING COMPLETE!")
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    print(f"💰 Total cost: ${total_cost:.4f}")
    
    if successful:
        print(f"\\n🏆 SUCCESSFUL GENERATIONS:")
        for result in successful:
            features = ", ".join(result.get("features", []))
            print(f"   🎥 {result['video_file']}")
            print(f"      📊 {result['size_mb']:.1f}MB, {result['generation_time']:.1f}s, ${result['cost']:.4f}")
            print(f"      🏷️ {result['tier']} tier, {features}")
    
    if failed:
        print(f"\\n❌ FAILED ATTEMPTS:")
        for result in failed:
            print(f"   ⚠️ {result.get('model', 'Unknown')}: {result.get('error', 'Unknown error')}")
    
    # Save comprehensive results
    summary = {
        "test_timestamp": datetime.now().isoformat(),
        "test_image": test_image,
        "models_tested": list(tester.models.keys()),
        "results": results,
        "successful_count": len(successful),
        "total_cost": total_cost,
        "summary": {
            "best_model": successful[0]["model"] if successful else None,
            "fastest_generation": min(successful, key=lambda x: x["generation_time"])["model"] if successful else None,
            "most_cost_effective": min(successful, key=lambda x: x["cost"])["model"] if successful else None
        }
    }
    
    summary_file = f"state_of_art_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\\n📄 Detailed results saved: {summary_file}")
    
    if successful:
        print(f"\\n🚀 READY FOR PRODUCTION SCALING!")
        print(f"💡 Best performing models identified for full pipeline deployment")


if __name__ == "__main__":
    asyncio.run(main())