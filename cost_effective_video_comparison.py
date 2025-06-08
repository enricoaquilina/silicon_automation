#!/usr/bin/env python3
"""
Cost-Effective Video Model Comparison
- Test only the most cost-effective models
- Kling v2.0 ($1.40) vs Hunyuan Video ($2.02)
- Generate side-by-side comparison with same input
- Calculate exact costs and quality differences
"""

import os
import asyncio
import aiohttp
import base64
import json
from datetime import datetime
from typing import Dict, List, Any


class CostEffectiveVideoComparison:
    """Compare only the most cost-effective video models"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
        self.api_url = "https://api.replicate.com/v1/predictions"
        
        # Only cost-effective models
        self.video_models = {
            "kling-v2.0": {
                "version": "03c47b845aed8a009e0f83a45be0a2100ca11a7077e667a33224a54e85b2965c",
                "cost_per_video": 1.40,
                "description": "Kling v2.0 - Most cost-effective ($1.40)",
                "duration": 5,
                "features": ["image-to-video", "720p", "reliable"]
            },
            "hunyuan-video": {
                "version": "6c9132aee14409cd6568d030453f1ba50f5f3412b844fe67f78a9eb62d55664f",
                "cost_per_video": 2.02,
                "description": "Hunyuan Video - State-of-the-art realistic motion ($2.02)",
                "duration": 5.4,
                "features": ["text-to-video", "realistic-motion", "state-of-the-art"]
            }
        }
        
        self.total_cost = 0
    
    def image_to_data_uri(self, image_path: str) -> str:
        """Convert image to data URI"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    async def test_kling_v2(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Test Kling v2.0 with image input"""
        print(f"🎬 Testing Kling v2.0 (image-to-video)")
        
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
        print(f"🎬 Testing Hunyuan Video (text-to-video)")
        
        try:
            payload = {
                "version": self.video_models["hunyuan-video"]["version"],
                "input": {
                    "prompt": prompt,
                    "width": 864,
                    "height": 480,
                    "video_length": 129,  # frames
                    "inference_steps": 50,
                    "fps": 24,
                    "embedded_guidance_scale": 6
                }
            }
            
            return await self._run_prediction("hunyuan-video", payload)
            
        except Exception as e:
            return {"success": False, "error": str(e), "model": "hunyuan-video"}
    
    async def _run_prediction(self, model_key: str, payload: dict) -> Dict[str, Any]:
        """Generic prediction runner"""
        
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
                        return {"success": False, "error": f"Submission failed: {response.status} - {error_text}"}
                    
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
                        
                        if elapsed % 30 < 3:  # Status every 30s
                            print(f"   📊 {model_key} status: {status} ({elapsed:.1f}s)")
                        
                        if status == 'succeeded':
                            video_url = result['output']
                            if isinstance(video_url, list):
                                video_url = video_url[0]
                            
                            # Download video
                            timestamp = datetime.now().strftime('%H%M%S')
                            output_filename = f"comparison_{model_key}_{timestamp}.mp4"
                            
                            async with session.get(video_url) as video_response:
                                if video_response.status == 200:
                                    with open(output_filename, 'wb') as f:
                                        f.write(await video_response.read())
                                    
                                    size_mb = os.path.getsize(output_filename) / 1024 / 1024
                                    cost = model_config["cost_per_video"]
                                    self.total_cost += cost
                                    
                                    print(f"   🎉 {model_key} SUCCESS: {output_filename}")
                                    print(f"   📊 {size_mb:.1f}MB, {elapsed:.1f}s generation, ${cost:.2f}")
                                    
                                    return {
                                        "success": True,
                                        "model": model_key,
                                        "file": output_filename,
                                        "size_mb": size_mb,
                                        "generation_time": elapsed,
                                        "cost": cost,
                                        "video_url": video_url,
                                        "features": model_config["features"]
                                    }
                            
                        elif status == 'failed':
                            error = result.get('error', 'Unknown error')
                            print(f"   ❌ {model_key} failed: {error}")
                            return {"success": False, "error": error, "model": model_key}
                        
                        # Continue polling
                        if elapsed > 600:  # 10 minute timeout
                            return {"success": False, "error": "Timeout", "model": model_key}
                        
                        await asyncio.sleep(8)
        
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            return {"success": False, "error": str(e), "model": model_key, "time": elapsed}
    
    async def run_cost_effective_comparison(self, test_image: str) -> Dict[str, Any]:
        """Run comparison between the most cost-effective models"""
        
        print(f"🚀 COST-EFFECTIVE VIDEO MODEL COMPARISON")
        print(f"Models: Kling v2.0 ($1.40) vs Hunyuan Video ($2.02)")
        print(f"Test image: {os.path.basename(test_image)}")
        print("=" * 70)
        
        start_time = datetime.now()
        
        # Enhanced prompt for both models
        prompt = "SiliconSentiments digital artwork with cinematic camera movement. Professional cinematography with smooth transitions, technological aesthetic, and high-quality visual effects. Gentle motion with artistic flair."
        
        print(f"\\n📝 Using prompt: '{prompt[:60]}...'")
        
        results = {}
        
        # Test both models
        print(f"\\n🎯 TESTING MODELS SEQUENTIALLY...")
        
        # Test Kling v2.0 (image-to-video)
        kling_result = await self.test_kling_v2(test_image, prompt)
        results["kling-v2.0"] = kling_result
        
        # Wait between tests
        await asyncio.sleep(3)
        
        # Test Hunyuan Video (text-to-video) 
        hunyuan_result = await self.test_hunyuan_video(prompt)
        results["hunyuan-video"] = hunyuan_result
        
        # Analysis
        duration = (datetime.now() - start_time).total_seconds()
        successful = [r for r in results.values() if r.get("success")]
        failed = [r for r in results.values() if not r.get("success")]
        
        comparison = {
            "test_timestamp": datetime.now().isoformat(),
            "test_image": test_image,
            "prompt": prompt,
            "results": results,
            "summary": {
                "successful_models": len(successful),
                "failed_models": len(failed),
                "total_cost": self.total_cost,
                "total_time_minutes": duration / 60
            }
        }
        
        print(f"\\n🎉 COMPARISON COMPLETE!")
        print(f"✅ Successful: {len(successful)}/2 models")
        print(f"💰 Total cost: ${self.total_cost:.2f}")
        print(f"⏱️ Total time: {duration/60:.1f} minutes")
        
        if successful:
            print(f"\\n🏆 RESULTS COMPARISON:")
            for result in successful:
                model = result['model']
                cost = result['cost']
                time = result['generation_time']
                size = result['size_mb']
                features = ', '.join(result['features'])
                
                print(f"   🎥 {model}:")
                print(f"      💰 Cost: ${cost:.2f}")
                print(f"      ⏱️ Time: {time:.1f}s")
                print(f"      📊 Size: {size:.1f}MB")
                print(f"      🏷️ Features: {features}")
                print(f"      📁 File: {result['file']}")
        
        if failed:
            print(f"\\n❌ FAILED MODELS:")
            for result in failed:
                print(f"   ⚠️ {result.get('model', 'Unknown')}: {result.get('error', 'Unknown error')}")
        
        # Cost efficiency analysis
        if len(successful) >= 2:
            kling_cost = results["kling-v2.0"].get("cost", 0)
            hunyuan_cost = results["hunyuan-video"].get("cost", 0)
            cost_difference = hunyuan_cost - kling_cost
            cost_increase = (cost_difference / kling_cost) * 100 if kling_cost > 0 else 0
            
            print(f"\\n💡 COST EFFICIENCY ANALYSIS:")
            print(f"   💸 Kling v2.0: ${kling_cost:.2f}")
            print(f"   💸 Hunyuan Video: ${hunyuan_cost:.2f}")
            print(f"   📈 Difference: +${cost_difference:.2f} ({cost_increase:.1f}% increase)")
            print(f"   🎯 Value question: Is the quality improvement worth {cost_increase:.1f}% more cost?")
        
        # Save detailed comparison
        comparison_file = f"cost_effective_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)
        
        print(f"\\n📄 Detailed comparison saved: {comparison_file}")
        
        return comparison


async def main():
    """Run cost-effective video model comparison"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Find test image
    test_image = "downloaded_verify_images/verify_C0xFHGOrBN7/recraft_model/upscaled_images/C0xFHGOrBN7_recraft_fixed_recraft_v1_upscaled.jpg"
    
    if not os.path.exists(test_image):
        # Find any upscaled image
        base_dir = "downloaded_verify_images/verify_C0xFHGOrBN7"
        for model in ["recraft", "flux", "sdxl", "kandinsky"]:
            model_dir = os.path.join(base_dir, f"{model}_model", "upscaled_images")
            if os.path.exists(model_dir):
                images = [f for f in os.listdir(model_dir) if f.endswith("_upscaled.jpg")]
                if images:
                    test_image = os.path.join(model_dir, images[0])
                    break
    
    if not os.path.exists(test_image):
        print(f"❌ No test image found")
        return
    
    # Run comparison
    comparator = CostEffectiveVideoComparison(replicate_token)
    comparison = await comparator.run_cost_effective_comparison(test_image)
    
    if comparison["summary"]["successful_models"] > 0:
        print(f"\\n🚀 READY FOR DECISION!")
        print(f"✅ Review generated videos to compare quality")
        print(f"💡 Choose the model that offers best value for your needs")


if __name__ == "__main__":
    asyncio.run(main())