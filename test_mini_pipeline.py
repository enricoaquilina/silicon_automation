#!/usr/bin/env python3
"""
Mini Test Pipeline - Validate Complete Workflow
Test with 2 image models, upscale, generate video, add music
Estimate costs before running full pipeline
"""

import os
import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Any
import base64


class MiniTestPipeline:
    """Test the complete workflow on a smaller scale"""
    
    def __init__(self, replicate_token: str):
        self.replicate_token = replicate_token
        self.api_url = "https://api.replicate.com/v1/predictions"
        
        # Test with 2 fast/cheap models
        self.test_models = {
            "sdxl": {
                "version": "7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
                "cost_per_image": 0.002,
                "short_name": "sdxl"
            },
            "kandinsky-2.2": {
                "version": "ad9d7879fbffa2874e1d909d1d37d9bc682889cc65b31f7bb00d2362619f194a",
                "cost_per_image": 0.002, 
                "short_name": "kandinsky"
            }
        }
        
        self.costs = {"images": 0, "upscale": 0, "video": 0, "music": 0, "total": 0}
    
    def image_to_data_uri(self, image_path: str) -> str:
        """Convert image to data URI"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    async def test_image_generation(self) -> Dict[str, Any]:
        """Test generating 2 images with SDXL (fastest)"""
        print(f"🎨 TESTING IMAGE GENERATION")
        
        prompt = "SiliconSentiments digital art: futuristic geometric design with technological elements"
        
        payload = {
            "version": self.test_models["sdxl"]["version"],
            "input": {
                "prompt": prompt,
                "num_outputs": 2,
                "width": 1024,
                "height": 1024
            }
        }
        
        headers = {
            "Authorization": f"Token {self.replicate_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 201:
                        return {"success": False, "error": f"Status {response.status}"}
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   ✅ Prediction submitted: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.api_url}/{prediction_id}"
                start_time = datetime.now()
                
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        status = result['status']
                        
                        if status == 'succeeded':
                            image_urls = result['output']
                            
                            # Download images
                            downloaded_files = []
                            for i, url in enumerate(image_urls[:2], 1):
                                filename = f"test_sdxl_v{i}.jpg"
                                
                                async with session.get(url) as img_response:
                                    if img_response.status == 200:
                                        with open(filename, 'wb') as f:
                                            f.write(await img_response.read())
                                        downloaded_files.append(filename)
                            
                            cost = len(downloaded_files) * self.test_models["sdxl"]["cost_per_image"]
                            self.costs["images"] += cost
                            elapsed = (datetime.now() - start_time).total_seconds()
                            
                            print(f"   ✅ Generated {len(downloaded_files)} images in {elapsed:.1f}s (${cost:.3f})")
                            
                            return {
                                "success": True,
                                "files": downloaded_files,
                                "cost": cost,
                                "time": elapsed
                            }
                            
                        elif status == 'failed':
                            return {"success": False, "error": result.get('error')}
                        
                        await asyncio.sleep(3)
                        elapsed = (datetime.now() - start_time).total_seconds()
                        if elapsed > 180:  # 3 minute timeout
                            return {"success": False, "error": "Timeout"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_upscaling(self, image_file: str) -> Dict[str, Any]:
        """Test upscaling one image"""
        print(f"🔍 TESTING UPSCALING")
        
        try:
            image_uri = self.image_to_data_uri(image_file)
            
            payload = {
                "version": "f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa",
                "input": {
                    "image": image_uri,
                    "scale": 4
                }
            }
            
            headers = {
                "Authorization": f"Token {self.replicate_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 201:
                        return {"success": False, "error": f"Status {response.status}"}
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   ✅ Upscale prediction submitted: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.api_url}/{prediction_id}"
                start_time = datetime.now()
                
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        status = result['status']
                        
                        if status == 'succeeded':
                            upscaled_url = result['output']
                            
                            # Download upscaled image
                            upscaled_filename = f"test_upscaled_{datetime.now().strftime('%H%M%S')}.jpg"
                            
                            async with session.get(upscaled_url) as img_response:
                                if img_response.status == 200:
                                    with open(upscaled_filename, 'wb') as f:
                                        f.write(await img_response.read())
                                    
                                    cost = 0.002  # Real-ESRGAN cost
                                    self.costs["upscale"] += cost
                                    elapsed = (datetime.now() - start_time).total_seconds()
                                    
                                    print(f"   ✅ Upscaled in {elapsed:.1f}s (${cost:.3f})")
                                    
                                    return {
                                        "success": True,
                                        "file": upscaled_filename,
                                        "cost": cost,
                                        "time": elapsed
                                    }
                            
                        elif status == 'failed':
                            return {"success": False, "error": result.get('error')}
                        
                        await asyncio.sleep(3)
                        elapsed = (datetime.now() - start_time).total_seconds()
                        if elapsed > 120:  # 2 minute timeout
                            return {"success": False, "error": "Timeout"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_video_generation(self) -> Dict[str, Any]:
        """Test video generation with Google Veo-3"""
        print(f"🎬 TESTING VIDEO GENERATION")
        
        prompt = "SiliconSentiments digital artwork with cinematic camera movement and professional lighting"
        
        payload = {
            "version": "3c08e75333152bd7c21eb75f0db2478fe32588feb45bb9acc59fba03b83fc002",
            "input": {
                "prompt": prompt,
                "seed": 42
            }
        }
        
        headers = {
            "Authorization": f"Token {self.replicate_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 201:
                        return {"success": False, "error": f"Status {response.status}"}
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   ✅ Video prediction submitted: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.api_url}/{prediction_id}"
                start_time = datetime.now()
                
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        status = result['status']
                        elapsed = (datetime.now() - start_time).total_seconds()
                        
                        if elapsed % 30 < 3:  # Print status every 30 seconds
                            print(f"   📊 Video status: {status} ({elapsed:.1f}s)")
                        
                        if status == 'succeeded':
                            video_url = result['output']
                            
                            # Download video
                            video_filename = f"test_video_{datetime.now().strftime('%H%M%S')}.mp4"
                            
                            async with session.get(video_url) as video_response:
                                if video_response.status == 200:
                                    with open(video_filename, 'wb') as f:
                                        f.write(await video_response.read())
                                    
                                    size_mb = os.path.getsize(video_filename) / 1024 / 1024
                                    cost = 0.0005  # Veo-3 estimated cost
                                    self.costs["video"] += cost
                                    
                                    print(f"   ✅ Video generated in {elapsed:.1f}s ({size_mb:.1f}MB, ${cost:.4f})")
                                    
                                    return {
                                        "success": True,
                                        "file": video_filename,
                                        "size_mb": size_mb,
                                        "cost": cost,
                                        "time": elapsed
                                    }
                            
                        elif status == 'failed':
                            return {"success": False, "error": result.get('error')}
                        
                        await asyncio.sleep(5)
                        if elapsed > 300:  # 5 minute timeout
                            return {"success": False, "error": "Timeout"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_music_generation(self) -> Dict[str, Any]:
        """Test music generation"""
        print(f"🎵 TESTING MUSIC GENERATION")
        
        prompt = "Ambient electronic music with technological vibes, 10 seconds"
        
        payload = {
            "version": "b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2dab",
            "input": {
                "prompt": prompt,
                "model_version": "stereo-large",
                "output_format": "mp3",
                "duration": 10
            }
        }
        
        headers = {
            "Authorization": f"Token {self.replicate_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 201:
                        return {"success": False, "error": f"Status {response.status}"}
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   ✅ Music prediction submitted: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.api_url}/{prediction_id}"
                start_time = datetime.now()
                
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        status = result['status']
                        
                        if status == 'succeeded':
                            music_url = result['output']
                            
                            # Download music
                            music_filename = f"test_music_{datetime.now().strftime('%H%M%S')}.mp3"
                            
                            async with session.get(music_url) as music_response:
                                if music_response.status == 200:
                                    with open(music_filename, 'wb') as f:
                                        f.write(await music_response.read())
                                    
                                    cost = 0.002  # MusicGen cost
                                    self.costs["music"] += cost
                                    elapsed = (datetime.now() - start_time).total_seconds()
                                    
                                    print(f"   ✅ Music generated in {elapsed:.1f}s (${cost:.3f})")
                                    
                                    return {
                                        "success": True,
                                        "file": music_filename,
                                        "cost": cost,
                                        "time": elapsed
                                    }
                            
                        elif status == 'failed':
                            return {"success": False, "error": result.get('error')}
                        
                        await asyncio.sleep(3)
                        elapsed = (datetime.now() - start_time).total_seconds()
                        if elapsed > 120:  # 2 minute timeout
                            return {"success": False, "error": "Timeout"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_mini_test(self) -> Dict[str, Any]:
        """Run complete mini test pipeline"""
        print(f"🚀 MINI TEST PIPELINE - VALIDATING COMPLETE WORKFLOW")
        print("=" * 60)
        
        start_time = datetime.now()
        results = {}
        
        # Step 1: Generate images
        image_result = await self.test_image_generation()
        results["images"] = image_result
        
        if not image_result.get("success"):
            print(f"❌ Image generation failed, stopping pipeline")
            return results
        
        # Step 2: Upscale first image
        upscale_result = await self.test_upscaling(image_result["files"][0])
        results["upscale"] = upscale_result
        
        # Step 3: Generate video
        video_result = await self.test_video_generation()
        results["video"] = video_result
        
        # Step 4: Generate music
        music_result = await self.test_music_generation()
        results["music"] = music_result
        
        # Calculate totals
        self.costs["total"] = sum([self.costs["images"], self.costs["upscale"], 
                                  self.costs["video"], self.costs["music"]])
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Final summary
        successful_steps = len([r for r in results.values() if r.get("success")])
        
        print(f"\\n🎉 MINI TEST COMPLETE!")
        print(f"✅ Successful steps: {successful_steps}/4")
        print(f"⏱️ Total time: {duration/60:.1f} minutes")
        print(f"💰 COST BREAKDOWN:")
        print(f"   📸 Images: ${self.costs['images']:.3f}")
        print(f"   🔍 Upscale: ${self.costs['upscale']:.3f}")
        print(f"   🎬 Video: ${self.costs['video']:.3f}")
        print(f"   🎵 Music: ${self.costs['music']:.3f}")
        print(f"   🏆 TOTAL: ${self.costs['total']:.3f}")
        
        # Estimate full pipeline cost
        if successful_steps == 4:
            # 8 models × 5 images each = 40 images
            # Each image: generation + upscale = $0.002 + $0.002 = $0.004
            # Each model: 1 video + 1 music = $0.0005 + $0.002 = $0.0025
            estimated_full_cost = (40 * 0.004) + (8 * 0.0025)
            
            print(f"\\n📊 FULL PIPELINE COST ESTIMATE:")
            print(f"   📸 40 images (8 models × 5 each): ${40 * 0.004:.3f}")
            print(f"   🔍 40 upscales: ${40 * 0.002:.3f}")
            print(f"   🎬 8 videos (1 per model): ${8 * 0.0005:.3f}")
            print(f"   🎵 8 music tracks: ${8 * 0.002:.3f}")
            print(f"   🎯 ESTIMATED TOTAL: ${estimated_full_cost:.3f}")
            
            print(f"\\n🚀 MINI TEST SUCCESSFUL - READY FOR FULL PIPELINE!")
        else:
            print(f"\\n⚠️ Some steps failed - review before full pipeline")
        
        return results


async def main():
    """Run mini test pipeline"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Run mini test
    tester = MiniTestPipeline(replicate_token)
    results = await tester.run_mini_test()
    
    # Save results
    test_file = f"mini_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(test_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\\n📄 Test results saved: {test_file}")


if __name__ == "__main__":
    asyncio.run(main())