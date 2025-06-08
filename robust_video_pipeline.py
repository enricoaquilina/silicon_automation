#!/usr/bin/env python3
"""
Robust Video Generation Pipeline
- Multiple state-of-the-art models with fallbacks
- Retry logic for "Prediction interrupted" errors
- Simple prompts that work
- Music generation for later integration
"""

import os
import asyncio
import base64
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class RobustVideoGenerator:
    """Robust video generation with multiple models and retry logic"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
        self.api_url = "https://api.replicate.com/v1/predictions"
        
        # State-of-the-art video models (priority order)
        self.models = {
            "kling-v2.0": {
                "version": "03c47b845aed8a009e0f83a45be0a2100ca11a7077e667a33224a54e85b2965c",
                "description": "Kling v2.0 - 5s videos in 720p",
                "cost_per_video": 0.0005,
                "reliability": "medium",  # Works but can get interrupted
                "quality": "high"
            },
            "leonardo-motion-2.0": {
                "version": "3a2633c4fc40d3b76c0cf31c9b859ff3f6a9f524972365c3c868f99ba90ee70d",
                "description": "Leonardo Motion 2.0 - 5s 480p videos",
                "cost_per_video": 0.01,
                "reliability": "high",  # New addition, might be more stable
                "quality": "medium"
            },
            "minimax-video-01": {
                "version": "c8bcc4751328608bb75043b3af7bed4eabcf1a6c0a478d50a4cf57fa04bd5101",
                "description": "Minimax Video-01 (Hailuo) - 6s videos",
                "cost_per_video": 0.006,
                "reliability": "low",  # Getting interrupted frequently
                "quality": "high"
            }
        }
        
        # Enhanced cinematic prompts with character movement and camera work
        self.enhanced_prompts = [
            "Digital artwork with gentle geometric transformations and subtle character movements. The camera slowly pans across the surface with a cinematic dolly shot, revealing intricate details. Characters breathe softly and eyes blink naturally. Smooth cinematic movement with soft lighting and high picture quality.",
            "Futuristic digital illustration with flowing data particles. Characters move with graceful gestures while the camera performs a cinematic tracking shot following subtle movements. Technological aesthetic with gentle character animation and high-definition clarity.",
            "Abstract geometric design with pulsing light elements. Any characters display subtle head tilts and gentle swaying while the camera moves smoothly around the subject with cinematic crane shots. Professional cinematography with warm glow effects and natural character motion.",
            "SiliconSentiments branded artwork with neural network patterns. Characters exhibit delicate facial expressions and hand movements while the camera performs a slow cinematic orbital movement with depth of field. Cybernetic style with gentle transitions and crisp quality.",
            "Digital art composition with holographic overlays. Characters show subtle breathing and eye movements while the camera glides through the scene with fluid cinematic motion and rack focus. Contemporary style with subtle effects and premium visual quality."
        ]
    
    def image_to_data_uri(self, image_path: str) -> str:
        """Convert image to data URI"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    async def generate_video_with_retry(self, model_key: str, image_path: str, 
                                      enhanced_prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """Generate video with retry logic for interrupted predictions"""
        
        model_config = self.models[model_key]
        
        for attempt in range(max_retries):
            print(f"🎬 {model_key} - Attempt {attempt + 1}/{max_retries}")
            print(f"   📝 Prompt: '{enhanced_prompt[:80]}...'")
            
            result = await self._single_generation_attempt(model_key, image_path, enhanced_prompt)
            
            if result.get("success"):
                print(f"   ✅ Success on attempt {attempt + 1}")
                return result
            elif "interrupted" in result.get("error", "").lower():
                print(f"   ⚠️ Interrupted - Retrying in 10 seconds...")
                await asyncio.sleep(10)  # Wait before retry
            else:
                print(f"   ❌ Non-retriable error: {result.get('error')}")
                break
        
        return {"success": False, "error": f"Failed after {max_retries} attempts", "model": model_key}
    
    async def _single_generation_attempt(self, model_key: str, image_path: str, 
                                       enhanced_prompt: str) -> Dict[str, Any]:
        """Single video generation attempt"""
        
        model_config = self.models[model_key]
        image_uri = self.image_to_data_uri(image_path)
        
        # Model-specific payloads
        if model_key == "kling-v2.0":
            payload = {
                "version": model_config["version"],
                "input": {
                    "prompt": enhanced_prompt,
                    "start_image": image_uri,
                    "duration": 5,
                    "aspect_ratio": "1:1"
                }
            }
        elif model_key == "leonardo-motion-2.0":
            payload = {
                "version": model_config["version"],
                "input": {
                    "prompt": enhanced_prompt,
                    "aspect_ratio": "16:9",  # Leonardo only supports 16:9, 9:16, 2:3, 4:5
                    "prompt_enhancement": True,
                    "frame_interpolation": True
                }
            }
        elif model_key == "minimax-video-01":
            payload = {
                "version": model_config["version"],
                "input": {
                    "prompt": enhanced_prompt,
                    "first_frame_image": image_uri
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
                        return {"success": False, "error": f"Submission failed: {response.status} - {error_text}"}
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   🎯 Prediction submitted: {prediction_id}")
                
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
                            
                            if video_url:
                                # Download video
                                timestamp = datetime.now().strftime('%H%M%S')
                                output_filename = f"{model_key}_enhanced_prompt_{timestamp}.mp4"
                                
                                async with session.get(video_url) as video_response:
                                    if video_response.status == 200:
                                        with open(output_filename, 'wb') as f:
                                            f.write(await video_response.read())
                                        
                                        size_mb = os.path.getsize(output_filename) / 1024 / 1024
                                        
                                        return {
                                            "success": True,
                                            "model": model_key,
                                            "prompt": enhanced_prompt,
                                            "video_file": output_filename,
                                            "size_mb": size_mb,
                                            "generation_time": elapsed,
                                            "video_url": video_url,
                                            "cost": model_config["cost_per_video"]
                                        }
                            
                            return {"success": False, "error": "No video URL in response"}
                        
                        elif status == 'failed':
                            error = result.get('error', 'Unknown error')
                            return {"success": False, "error": error, "time": elapsed}
                        
                        # Continue polling
                        if elapsed < 400:  # 6.5 minute timeout (longer for Kling)
                            await asyncio.sleep(8)  # Check every 8 seconds
                        else:
                            return {"success": False, "error": "Timeout", "time": elapsed}
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            return {"success": False, "error": str(e), "time": elapsed}
    
    async def generate_videos_for_images(self, image_paths: List[str], 
                                       output_dir: str = ".") -> Dict[str, Any]:
        """Generate videos for multiple images with fallback models"""
        
        print(f"🚀 ROBUST VIDEO GENERATION PIPELINE")
        print(f"Images to process: {len(image_paths)}")
        print(f"Models available: {len(self.models)}")
        print("=" * 60)
        
        start_time = datetime.now()
        results = []
        total_cost = 0
        
        for i, image_path in enumerate(image_paths, 1):
            image_name = os.path.splitext(os.path.basename(image_path))[0]
            print(f"\\n📸 Processing Image {i}/{len(image_paths)}: {image_name}")
            
            # Use first enhanced prompt with camera movement
            prompt = self.enhanced_prompts[0]
            
            # Try models in priority order (most reliable first)
            success = False
            
            for model_key in ["leonardo-motion-2.0", "kling-v2.0", "minimax-video-01"]:
                if success:
                    break
                
                print(f"\\n   🎬 Trying {model_key}...")
                result = await self.generate_video_with_retry(model_key, image_path, prompt)
                
                if result.get("success"):
                    success = True
                    results.append(result)
                    total_cost += result.get("cost", 0)
                    
                    print(f"   🎉 SUCCESS: {result['video_file']}")
                    print(f"   📊 {result['size_mb']:.1f}MB, {result['generation_time']:.1f}s, ${result['cost']:.4f}")
                    break
                else:
                    print(f"   ❌ {model_key} failed: {result.get('error')}")
                    # Try next model
            
            if not success:
                print(f"   ⚠️ All models failed for {image_name}")
                results.append({
                    "success": False,
                    "image": image_name,
                    "error": "All models failed"
                })
        
        duration = (datetime.now() - start_time).total_seconds()
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        summary = {
            "total_images": len(image_paths),
            "successful_videos": len(successful),
            "failed_videos": len(failed),
            "success_rate": len(successful) / len(image_paths),
            "total_cost": total_cost,
            "total_time_minutes": duration / 60,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\\n🎉 PIPELINE COMPLETE!")
        print(f"✅ Success: {len(successful)}/{len(image_paths)} ({summary['success_rate']:.1%})")
        print(f"💰 Total cost: ${total_cost:.4f}")
        print(f"⏱️ Total time: {duration/60:.1f} minutes")
        
        if successful:
            print(f"\\n📁 Generated videos:")
            for result in successful:
                print(f"   🎥 {result['video_file']} ({result['model']})")
        
        # Save summary
        summary_file = os.path.join(output_dir, f"video_generation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\\n📄 Summary saved: {summary_file}")
        
        return summary


async def main():
    """Test robust video generation pipeline"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Find upscaled images
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
    
    # Create robust generator
    generator = RobustVideoGenerator(replicate_token)
    
    # Generate videos for all upscaled images
    summary = await generator.generate_videos_for_images(test_images[:2])  # Test with first 2 images
    
    if summary["successful_videos"] > 0:
        print(f"\\n🚀 READY FOR FULL SCALE DEPLOYMENT!")
        print(f"✅ Pipeline validated with {summary['success_rate']:.1%} success rate")
        print(f"💡 Next: Process all {len(test_images)} upscaled images")


if __name__ == "__main__":
    asyncio.run(main())