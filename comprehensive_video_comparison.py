#!/usr/bin/env python3
"""
Comprehensive Video Model Comparison
- Test 4 cost-effective video models side-by-side
- Kling v2.0, Hunyuan Video, Minimax Video-01, and Wan2.1 I2V
- Generate quality vs cost analysis
- Make informed decision for production pipeline
"""

import os
import asyncio
import aiohttp
import base64
import json
from datetime import datetime
from typing import Dict, List, Any


class ComprehensiveVideoComparison:
    """Compare all available cost-effective video models"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
        self.api_url = "https://api.replicate.com/v1/predictions"
        
        # All cost-effective video models with accurate pricing
        self.video_models = {
            "kling-v2.0": {
                "version": "03c47b845aed8a009e0f83a45be0a2100ca11a7077e667a33224a54e85b2965c",
                "cost_per_video": 1.40,  # $0.28/second × 5 seconds
                "description": "Kling v2.0 - Most cost-effective",
                "duration": 5,
                "features": ["image-to-video", "720p", "reliable"],
                "input_type": "image"
            },
            "hunyuan-video": {
                "version": "6c9132aee14409cd6568d030453f1ba50f5f3412b844fe67f78a9eb62d55664f",
                "cost_per_video": 2.02,  # Fixed cost
                "description": "Hunyuan Video - State-of-the-art realistic motion",
                "duration": 5.4,
                "features": ["text-to-video", "realistic-motion", "state-of-the-art"],
                "input_type": "text"
            },
            "minimax-video-01": {
                "version": "c8bcc4751328608bb75043b3af7bed4eabcf1a6c0a478d50a4cf57fa04bd5101",
                "cost_per_video": 0.50,  # $0.500 per video billing unit (from docs)
                "description": "Minimax Video-01 - Hailuo, very cost-effective",
                "duration": 6,
                "features": ["text-to-video", "image-to-video", "6s"],
                "input_type": "both"
            },
            "wan2.1-i2v": {
                "version": "ae5bc519ee414f255f66c7ac22062e01bbbd6050c04f888d002d5ee0dc087a0c",
                "cost_per_video": 0.65,  # Estimated based on ~5.1s @ $0.0122/s
                "description": "Wan2.1 I2V - Image-to-video specialist 480p",
                "duration": 5.1,
                "features": ["image-to-video", "480p", "81-frames"],
                "input_type": "image"
            }
        }
        
        self.total_cost = 0
        self.results = {}
    
    def image_to_data_uri(self, image_path: str) -> str:
        """Convert image to data URI"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    def display_cost_preview(self):
        """Show cost preview before running tests"""
        print(f"💰 COST PREVIEW - 4 MODEL COMPARISON")
        print("=" * 60)
        
        total_estimated_cost = sum(model["cost_per_video"] for model in self.video_models.values())
        
        for model_key, config in self.video_models.items():
            cost = config["cost_per_video"]
            duration = config["duration"]
            features = ", ".join(config["features"])
            print(f"   🎬 {model_key}: ${cost:.2f} ({duration}s) - {features}")
        
        print(f"\\n   🏆 TOTAL ESTIMATED COST: ${total_estimated_cost:.2f}")
        print(f"   📊 Cost range: ${min(m['cost_per_video'] for m in self.video_models.values()):.2f} - ${max(m['cost_per_video'] for m in self.video_models.values()):.2f}")
        
        return total_estimated_cost
    
    async def test_kling_v2(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Test Kling v2.0 with image input"""
        print(f"\\n🎬 Testing Kling v2.0...")
        
        try:
            image_uri = self.image_to_data_uri(image_path)
            
            payload = {
                "version": self.video_models["kling-v2.0"]["version"],
                "input": {
                    "prompt": prompt,
                    "start_image": image_uri,
                    "duration": 5,
                    "aspect_ratio": "1:1"
                }
            }
            
            return await self._run_prediction("kling-v2.0", payload)
            
        except Exception as e:
            return {"success": False, "error": str(e), "model": "kling-v2.0"}
    
    async def test_hunyuan_video(self, prompt: str) -> Dict[str, Any]:
        """Test Hunyuan Video with text prompt"""
        print(f"\\n🎬 Testing Hunyuan Video...")
        
        try:
            payload = {
                "version": self.video_models["hunyuan-video"]["version"],
                "input": {
                    "prompt": prompt,
                    "width": 864,
                    "height": 480,
                    "video_length": 129,
                    "inference_steps": 50,
                    "fps": 24,
                    "embedded_guidance_scale": 6
                }
            }
            
            return await self._run_prediction("hunyuan-video", payload)
            
        except Exception as e:
            return {"success": False, "error": str(e), "model": "hunyuan-video"}
    
    async def test_minimax_video(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Test Minimax Video-01 with image input"""
        print(f"\\n🎬 Testing Minimax Video-01...")
        
        try:
            image_uri = self.image_to_data_uri(image_path)
            
            payload = {
                "version": self.video_models["minimax-video-01"]["version"],
                "input": {
                    "prompt": prompt,
                    "first_frame_image": image_uri
                }
            }
            
            return await self._run_prediction("minimax-video-01", payload)
            
        except Exception as e:
            return {"success": False, "error": str(e), "model": "minimax-video-01"}
    
    async def test_wan21_i2v(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Test Wan2.1 I2V with image input"""
        print(f"\\n🎬 Testing Wan2.1 I2V...")
        
        try:
            image_uri = self.image_to_data_uri(image_path)
            
            payload = {
                "version": self.video_models["wan2.1-i2v"]["version"],
                "input": {
                    "image": image_uri,
                    "prompt": prompt,
                    "num_frames": 81,
                    "sample_steps": 30,
                    "fps": 16,
                    "sample_guide_scale": 5,
                    "sample_shift": 3,
                    "fast_mode": "Balanced"  # Fixed the parameter issue
                }
            }
            
            return await self._run_prediction("wan2.1-i2v", payload)
            
        except Exception as e:
            return {"success": False, "error": str(e), "model": "wan2.1-i2v"}
    
    async def _run_prediction(self, model_key: str, payload: dict) -> Dict[str, Any]:
        """Generic prediction runner with detailed tracking"""
        
        model_config = self.video_models[model_key]
        
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
                        print(f"   ❌ {model_key} submission failed: {response.status}")
                        return {"success": False, "error": f"Submission failed: {response.status} - {error_text}"}
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   ✅ {model_key} prediction submitted: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.api_url}/{prediction_id}"
                
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        status = result['status']
                        elapsed = (datetime.now() - start_time).total_seconds()
                        
                        if elapsed % 30 < 3:  # Status every 30s
                            print(f"   📊 {model_key}: {status} ({elapsed:.1f}s)")
                        
                        if status == 'succeeded':
                            video_output = result['output']
                            
                            # Handle different output formats
                            if isinstance(video_output, list):
                                video_url = video_output[0] if video_output else None
                            elif isinstance(video_output, str):
                                video_url = video_output
                            else:
                                video_url = str(video_output) if video_output else None
                            
                            if video_url:
                                # Download video
                                timestamp = datetime.now().strftime('%H%M%S')
                                output_filename = f"compare_{model_key}_{timestamp}.mp4"
                                
                                async with session.get(video_url) as video_response:
                                    if video_response.status == 200:
                                        with open(output_filename, 'wb') as f:
                                            f.write(await video_response.read())
                                        
                                        size_mb = os.path.getsize(output_filename) / 1024 / 1024
                                        cost = model_config["cost_per_video"]
                                        self.total_cost += cost
                                        
                                        print(f"   🎉 {model_key} SUCCESS!")
                                        print(f"   📁 File: {output_filename}")
                                        print(f"   📊 {size_mb:.1f}MB, {elapsed:.1f}s, ${cost:.2f}")
                                        
                                        return {
                                            "success": True,
                                            "model": model_key,
                                            "file": output_filename,
                                            "size_mb": size_mb,
                                            "generation_time": elapsed,
                                            "cost": cost,
                                            "video_url": video_url,
                                            "features": model_config["features"],
                                            "description": model_config["description"]
                                        }
                                    else:
                                        print(f"   ❌ {model_key} download failed: {video_response.status}")
                                        return {"success": False, "error": f"Download failed: {video_response.status}"}
                            else:
                                print(f"   ❌ {model_key} no video URL in response")
                                return {"success": False, "error": "No video URL in response"}
                        
                        elif status == 'failed':
                            error = result.get('error', 'Unknown error')
                            print(f"   ❌ {model_key} generation failed: {error}")
                            return {"success": False, "error": error, "model": model_key}
                        
                        # Continue polling
                        if elapsed > 600:  # 10 minute timeout
                            print(f"   ⏰ {model_key} timeout after {elapsed:.1f}s")
                            return {"success": False, "error": "Timeout", "model": model_key}
                        
                        await asyncio.sleep(8)
        
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"   ❌ {model_key} exception: {e}")
            return {"success": False, "error": str(e), "model": model_key, "time": elapsed}
    
    async def run_comprehensive_comparison(self, test_image: str) -> Dict[str, Any]:
        """Run comprehensive comparison of all 4 models"""
        
        print(f"🚀 COMPREHENSIVE VIDEO MODEL COMPARISON")
        print(f"Testing 4 cost-effective models with same input")
        print(f"Test image: {os.path.basename(test_image)}")
        print("=" * 70)
        
        # Display cost preview
        estimated_cost = self.display_cost_preview()
        
        # Confirmation prompt (simulated)
        print(f"\\n⚠️ This will cost approximately ${estimated_cost:.2f}")
        print(f"🎯 Proceeding with comprehensive comparison...")
        
        start_time = datetime.now()
        
        # Enhanced prompt optimized for all models
        prompt = "SiliconSentiments digital artwork with cinematic camera movement. Professional cinematography with smooth panning motion, technological aesthetic with glowing elements, and high-quality visual effects. Gentle animation with artistic flair and futuristic ambiance."
        
        print(f"\\n📝 Using optimized prompt: '{prompt[:60]}...'")
        print(f"\\n🎬 TESTING ALL MODELS...")
        
        # Test all models
        test_functions = [
            ("kling-v2.0", self.test_kling_v2(test_image, prompt)),
            ("hunyuan-video", self.test_hunyuan_video(prompt)),
            ("minimax-video-01", self.test_minimax_video(test_image, prompt)),
            ("wan2.1-i2v", self.test_wan21_i2v(test_image, prompt))
        ]
        
        # Run tests sequentially to avoid API rate limiting
        for model_name, test_coro in test_functions:
            result = await test_coro
            self.results[model_name] = result
            
            # Wait between tests
            await asyncio.sleep(5)
        
        # Analysis
        duration = (datetime.now() - start_time).total_seconds()
        successful = [r for r in self.results.values() if r.get("success")]
        failed = [r for r in self.results.values() if not r.get("success")]
        
        # Comprehensive analysis
        analysis = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "test_image": test_image,
                "prompt": prompt,
                "total_duration_minutes": duration / 60
            },
            "results": self.results,
            "cost_analysis": {
                "estimated_cost": estimated_cost,
                "actual_cost": self.total_cost,
                "cost_by_model": {model: result.get("cost", 0) for model, result in self.results.items() if result.get("success")}
            },
            "performance_summary": {
                "successful_models": len(successful),
                "failed_models": len(failed),
                "success_rate": len(successful) / len(self.results) if self.results else 0
            }
        }
        
        print(f"\\n🎉 COMPREHENSIVE COMPARISON COMPLETE!")
        print(f"✅ Successful: {len(successful)}/4 models")
        print(f"💰 Actual cost: ${self.total_cost:.2f}")
        print(f"⏱️ Total time: {duration/60:.1f} minutes")
        
        if successful:
            print(f"\\n🏆 MODEL COMPARISON RESULTS:")
            
            # Sort by cost for easy comparison
            successful_sorted = sorted(successful, key=lambda x: x.get("cost", 0))
            
            for result in successful_sorted:
                model = result['model']
                cost = result['cost']
                time = result['generation_time']
                size = result['size_mb']
                features = ', '.join(result['features'])
                
                print(f"\\n   🎥 {model.upper()}:")
                print(f"      💰 Cost: ${cost:.2f}")
                print(f"      ⏱️ Generation: {time:.1f}s")
                print(f"      📊 Size: {size:.1f}MB")
                print(f"      🏷️ Features: {features}")
                print(f"      📁 File: {result['file']}")
            
            # Value analysis
            print(f"\\n💡 VALUE ANALYSIS:")
            cheapest = min(successful_sorted, key=lambda x: x["cost"])
            most_expensive = max(successful_sorted, key=lambda x: x["cost"])
            cost_range = most_expensive["cost"] - cheapest["cost"]
            
            print(f"   💸 Cheapest: {cheapest['model']} (${cheapest['cost']:.2f})")
            print(f"   💎 Most expensive: {most_expensive['model']} (${most_expensive['cost']:.2f})")
            print(f"   📈 Cost range: ${cost_range:.2f} ({(cost_range/cheapest['cost']*100):.1f}% difference)")
            
            print(f"\\n🎯 RECOMMENDATION:")
            print(f"   📊 Review all 4 generated videos for quality comparison")
            print(f"   💰 Consider cost vs quality trade-offs")
            print(f"   🚀 Choose optimal model for production pipeline")
        
        if failed:
            print(f"\\n❌ FAILED MODELS:")
            for result in failed:
                model = result.get('model', 'Unknown')
                error = result.get('error', 'Unknown error')
                print(f"   ⚠️ {model}: {error}")
        
        # Save comprehensive analysis
        analysis_file = f"comprehensive_video_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"\\n📄 Comprehensive analysis saved: {analysis_file}")
        
        return analysis


async def main():
    """Run comprehensive video model comparison"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Find test image
    test_image = "downloaded_verify_images/verify_C0xFHGOrBN7/multi_model_multimedia/model_recraft/upscaled/C0xFHGOrBN7_recraft_fixed_recraft_v1_upscaled.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        print("Available images:")
        import glob
        images = glob.glob("downloaded_verify_images/**/*upscaled.jpg", recursive=True)
        for img in images[:5]:
            print(f"   📸 {img}")
        if images:
            test_image = images[0]
            print(f"\\n✅ Using: {test_image}")
        else:
            return
    
    # Run comprehensive comparison
    comparator = ComprehensiveVideoComparison(replicate_token)
    analysis = await comparator.run_comprehensive_comparison(test_image)
    
    if analysis["performance_summary"]["successful_models"] > 0:
        print(f"\\n🚀 READY FOR PRODUCTION DECISION!")
        print(f"✅ Compare generated videos to choose optimal model")
        print(f"💡 Use results to configure production pipeline")


if __name__ == "__main__":
    asyncio.run(main())