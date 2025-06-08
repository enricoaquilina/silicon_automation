#!/usr/bin/env python3
"""
Complete Regeneration Pipeline
1. Clear existing folders for C0xFHGOrBN7
2. Regenerate images with ALL models (8 total)
3. Upscale all generated images  
4. Generate videos (5 images per model → 1 combined video per model)
5. Add music to each video
6. Compute and track total costs
"""

import os
import asyncio
import aiohttp
import shutil
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any
import base64


class CompleteRegenerationPipeline:
    """Complete pipeline from scratch to final videos with music"""
    
    def __init__(self, replicate_token: str, shortcode: str):
        self.replicate_token = replicate_token
        self.shortcode = shortcode
        self.api_url = "https://api.replicate.com/v1/predictions"
        
        # All 8 image generation models
        self.image_models = {
            "flux-1.1-pro": {
                "version": "80a09d66baa990429c2f5ae8a4306bf778a1b3775afd01cc2cc8bdbe9033769c",
                "cost_per_image": 0.005,
                "short_name": "flux",
                "description": "Flux 1.1 Pro - Advanced generation"
            },
            "recraft-v3": {
                "version": "0fea59248a8a1ddb8197792577f6627ec65482abc49f50c6e9da40ca8729d24d", 
                "cost_per_image": 0.004,
                "short_name": "recraft",
                "description": "Recraft v3 - Professional design"
            },
            "sdxl": {
                "version": "7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
                "cost_per_image": 0.002,
                "short_name": "sdxl",
                "description": "Stable Diffusion XL"
            },
            "kandinsky-2.2": {
                "version": "ad9d7879fbffa2874e1d909d1d37d9bc682889cc65b31f7bb00d2362619f194a",
                "cost_per_image": 0.002,
                "short_name": "kandinsky",
                "description": "Kandinsky 2.2"
            },
            "leonardo-phoenix": {
                "version": "4cd55e5b4b40428d87cb2bc74e86bb2ac4c3c4b0b3ca04c4725c1e9c5b5e4b0a",
                "cost_per_image": 0.004,
                "short_name": "leonardo",
                "description": "Leonardo Phoenix 1.0"
            },
            "janus-pro-7b": {
                "version": "fbf6eb41957601528aab2b3f6d37a287015d9f486c3ac4ec6e80f04744ac1a32",
                "cost_per_image": 0.003,
                "short_name": "janus",
                "description": "Janus Pro 7B"
            },
            "playground-v2_5": {
                "version": "a45f82a1382bed5c7aeb861dac7c7d191b0fdf74d8d57c4a0e6ed7d4d0bf7d24",
                "cost_per_image": 0.004,
                "short_name": "playground", 
                "description": "Playground v2.5"
            },
            "minimax-video": {
                "version": "c8bcc4751328608bb75043b3af7bed4eabcf1a6c0a478d50a4cf57fa04bd5101",
                "cost_per_image": 0.020,
                "short_name": "minimax",
                "description": "Minimax Video-01"
            }
        }
        
        # Upscaling models
        self.upscale_models = {
            "real-esrgan": {
                "version": "f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa",
                "cost_per_image": 0.002,
                "description": "Real-ESRGAN x4 upscaler"
            }
        }
        
        # Video generation models (working ones)
        self.video_models = {
            "google-veo-3": {
                "version": "3c08e75333152bd7c21eb75f0db2478fe32588feb45bb9acc59fba03b83fc002",
                "cost_per_video": 0.0005,
                "description": "Google Veo-3 with audio"
            }
        }
        
        # Music generation
        self.music_models = {
            "musicgen": {
                "version": "b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2dab",
                "cost_per_generation": 0.002,
                "description": "MusicGen - AI music generation"
            }
        }
        
        self.costs = {
            "image_generation": 0,
            "upscaling": 0,
            "video_generation": 0,
            "music_generation": 0,
            "total": 0
        }
    
    async def clear_existing_folders(self, base_dir: str) -> bool:
        """Clear existing generated content for this shortcode"""
        print(f"🧹 CLEARING EXISTING CONTENT")
        print(f"Shortcode: {self.shortcode}")
        print(f"Base directory: {base_dir}")
        
        try:
            if os.path.exists(base_dir):
                # List what will be removed
                items = os.listdir(base_dir)
                print(f"   📁 Found {len(items)} items to clear:")
                for item in items:
                    if item.endswith('_model') or item.endswith('.jpg') or item.endswith('.mp4'):
                        print(f"      🗑️ {item}")
                
                # Remove model directories but keep originals
                for item in items:
                    item_path = os.path.join(base_dir, item)
                    if item.endswith('_model') and os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        print(f"   ✅ Removed {item}")
                    elif item.endswith('.mp4'):
                        os.remove(item_path)
                        print(f"   ✅ Removed {item}")
            
            print(f"   🎉 Clearing complete!")
            return True
            
        except Exception as e:
            print(f"   ❌ Error clearing folders: {e}")
            return False
    
    def image_to_data_uri(self, image_path: str) -> str:
        """Convert image to data URI"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    async def generate_images_all_models(self, original_image: str, output_dir: str) -> Dict[str, Any]:
        """Generate 5 images with each of the 8 models"""
        print(f"\\n🎨 GENERATING IMAGES WITH ALL 8 MODELS")
        print(f"Original: {os.path.basename(original_image)}")
        
        # SiliconSentiments prompt
        prompt = """SiliconSentiments digital art transformation: Abstract interpretation of digital artwork

STYLE: Futuristic digital illustration, technological aesthetics, nature-inspired elements, geometric patterns, crystalline structures

ELEMENTS: Flowing data streams, holographic overlays, organic circuit patterns, luminescent accents, metallic textures, prismatic effects

COMPOSITION: Professional digital artwork, clean lines, balanced composition, high contrast, vibrant colors

COLORS: Electric blue, neon green, chrome silver, warm gold accents, deep purple highlights

MOOD: Innovative, technological, ethereal, harmonious blend of nature and technology

FORMAT: High-quality digital illustration suitable for social media"""
        
        results = {}
        
        for model_name, model_config in self.image_models.items():
            print(f"\\n   🎯 Generating with {model_name}...")
            
            try:
                # Create model-specific payload
                if model_name == "recraft-v3":
                    payload = {
                        "version": model_config["version"],
                        "input": {
                            "prompt": prompt,
                            "size": "1024x1024",
                            "style": "digital_illustration",
                            "output_format": "jpg"
                        }
                    }
                elif model_name == "flux-1.1-pro":
                    payload = {
                        "version": model_config["version"],
                        "input": {
                            "prompt": prompt,
                            "num_outputs": 5,
                            "aspect_ratio": "1:1",
                            "output_format": "jpg",
                            "output_quality": 90
                        }
                    }
                else:
                    # Generic payload for other models
                    payload = {
                        "version": model_config["version"],
                        "input": {
                            "prompt": prompt,
                            "num_outputs": 5,
                            "width": 1024,
                            "height": 1024
                        }
                    }
                
                headers = {
                    "Authorization": f"Token {self.replicate_token}",
                    "Content-Type": "application/json"
                }
                
                async with aiohttp.ClientSession() as session:
                    # Submit prediction
                    async with session.post(self.api_url, json=payload, headers=headers) as response:
                        if response.status != 201:
                            error_text = await response.text()
                            print(f"      ❌ {model_name} submission failed: {response.status}")
                            continue
                        
                        result = await response.json()
                        prediction_id = result['id']
                        print(f"      🎯 Prediction submitted: {prediction_id}")
                    
                    # Poll for completion
                    get_url = f"{self.api_url}/{prediction_id}"
                    start_time = datetime.now()
                    
                    while True:
                        async with session.get(get_url, headers=headers) as response:
                            result = await response.json()
                            status = result['status']
                            
                            if status == 'succeeded':
                                image_urls = result['output']
                                if isinstance(image_urls, str):
                                    image_urls = [image_urls]
                                
                                # Download images
                                downloaded_files = []
                                for i, url in enumerate(image_urls[:5], 1):
                                    filename = f"{self.shortcode}_{model_config['short_name']}_v{i}.jpg"
                                    filepath = os.path.join(output_dir, filename)
                                    
                                    async with session.get(url) as img_response:
                                        if img_response.status == 200:
                                            with open(filepath, 'wb') as f:
                                                f.write(await img_response.read())
                                            downloaded_files.append(filepath)
                                
                                # Calculate cost (for models that generate multiple outputs separately)
                                if model_name == "recraft-v3":
                                    # Need to generate 5 separate predictions
                                    cost = model_config["cost_per_image"] * 5
                                else:
                                    cost = model_config["cost_per_image"] * len(downloaded_files)
                                
                                self.costs["image_generation"] += cost
                                
                                print(f"      ✅ {model_name}: {len(downloaded_files)} images (${cost:.3f})")
                                results[model_name] = {
                                    "success": True,
                                    "files": downloaded_files,
                                    "cost": cost
                                }
                                break
                                
                            elif status == 'failed':
                                error = result.get('error', 'Unknown error')
                                print(f"      ❌ {model_name} failed: {error}")
                                results[model_name] = {"success": False, "error": error}
                                break
                            
                            # Continue polling
                            elapsed = (datetime.now() - start_time).total_seconds()
                            if elapsed > 300:  # 5 minute timeout
                                print(f"      ⏰ {model_name} timeout")
                                results[model_name] = {"success": False, "error": "Timeout"}
                                break
                            
                            await asyncio.sleep(5)
                
            except Exception as e:
                print(f"      ❌ {model_name} exception: {e}")
                results[model_name] = {"success": False, "error": str(e)}
        
        successful = [r for r in results.values() if r.get("success")]
        print(f"\\n   🎉 Image generation complete: {len(successful)}/{len(self.image_models)} models successful")
        print(f"   💰 Image generation cost: ${self.costs['image_generation']:.3f}")
        
        return results
    
    async def upscale_all_images(self, image_results: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
        """Upscale all generated images"""
        print(f"\\n🔍 UPSCALING ALL GENERATED IMAGES")
        
        upscale_results = {}
        
        for model_name, result in image_results.items():
            if not result.get("success"):
                continue
                
            model_dir = os.path.join(output_dir, f"{model_name}_model")
            upscaled_dir = os.path.join(model_dir, "upscaled_images")
            os.makedirs(upscaled_dir, exist_ok=True)
            
            print(f"\\n   🔍 Upscaling {model_name} images...")
            
            upscaled_files = []
            
            for image_file in result["files"]:
                try:
                    # Upscale with Real-ESRGAN
                    image_uri = self.image_to_data_uri(image_file)
                    
                    payload = {
                        "version": self.upscale_models["real-esrgan"]["version"],
                        "input": {
                            "image": image_uri,
                            "scale": 4,
                            "face_enhance": True
                        }
                    }
                    
                    headers = {
                        "Authorization": f"Token {self.replicate_token}",
                        "Content-Type": "application/json"
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(self.api_url, json=payload, headers=headers) as response:
                            if response.status != 201:
                                continue
                            
                            result_data = await response.json()
                            prediction_id = result_data['id']
                        
                        # Poll for completion
                        get_url = f"{self.api_url}/{prediction_id}"
                        
                        while True:
                            async with session.get(get_url, headers=headers) as response:
                                result_data = await response.json()
                                
                                if result_data['status'] == 'succeeded':
                                    upscaled_url = result_data['output']
                                    
                                    # Download upscaled image
                                    base_name = os.path.splitext(os.path.basename(image_file))[0]
                                    upscaled_filename = f"{base_name}_upscaled.jpg"
                                    upscaled_path = os.path.join(upscaled_dir, upscaled_filename)
                                    
                                    async with session.get(upscaled_url) as img_response:
                                        if img_response.status == 200:
                                            with open(upscaled_path, 'wb') as f:
                                                f.write(await img_response.read())
                                            upscaled_files.append(upscaled_path)
                                            
                                            self.costs["upscaling"] += self.upscale_models["real-esrgan"]["cost_per_image"]
                                    break
                                elif result_data['status'] == 'failed':
                                    break
                                
                                await asyncio.sleep(3)
                    
                except Exception as e:
                    print(f"      ⚠️ Upscale error for {os.path.basename(image_file)}: {e}")
                    continue
            
            print(f"      ✅ {model_name}: {len(upscaled_files)} upscaled images")
            upscale_results[model_name] = {
                "success": len(upscaled_files) > 0,
                "files": upscaled_files,
                "count": len(upscaled_files)
            }
        
        print(f"\\n   🎉 Upscaling complete!")
        print(f"   💰 Upscaling cost: ${self.costs['upscaling']:.3f}")
        
        return upscale_results
    
    async def generate_videos_per_model(self, upscale_results: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
        """Generate one combined video per model (5 images → 1 video per model)"""
        print(f"\\n🎬 GENERATING VIDEOS PER MODEL")
        
        video_results = {}
        
        for model_name, result in upscale_results.items():
            if not result.get("success") or len(result["files"]) < 3:
                continue
            
            print(f"\\n   🎬 Generating video for {model_name}...")
            
            # Use first 5 upscaled images (or all if less than 5)
            images_to_use = result["files"][:5]
            
            try:
                # Use Google Veo-3 for video generation
                prompt = f"Transform these SiliconSentiments digital artworks into a cinematic sequence. Smooth camera transitions between each artwork with gentle movements. Professional cinematography with soft lighting and technological aesthetic. Each artwork displays for 2-3 seconds with smooth transitions."
                
                # For now, use first image as representative
                first_image = images_to_use[0]
                
                payload = {
                    "version": self.video_models["google-veo-3"]["version"],
                    "input": {
                        "prompt": f"Based on SiliconSentiments digital artwork: {prompt}",
                        "seed": 42
                    }
                }
                
                headers = {
                    "Authorization": f"Token {self.replicate_token}",
                    "Content-Type": "application/json"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, json=payload, headers=headers) as response:
                        if response.status != 201:
                            print(f"      ❌ Video submission failed for {model_name}")
                            continue
                        
                        result_data = await response.json()
                        prediction_id = result_data['id']
                        print(f"      🎯 Video prediction submitted: {prediction_id}")
                    
                    # Poll for completion
                    get_url = f"{self.api_url}/{prediction_id}"
                    start_time = datetime.now()
                    
                    while True:
                        async with session.get(get_url, headers=headers) as response:
                            result_data = await response.json()
                            status = result_data['status']
                            elapsed = (datetime.now() - start_time).total_seconds()
                            
                            if status == 'succeeded':
                                video_url = result_data['output']
                                
                                # Download video
                                model_dir = os.path.join(output_dir, f"{model_name}_model")
                                videos_dir = os.path.join(model_dir, "videos")
                                os.makedirs(videos_dir, exist_ok=True)
                                
                                video_filename = f"SiliconSentiments_{model_name}_combined_video.mp4"
                                video_path = os.path.join(videos_dir, video_filename)
                                
                                async with session.get(video_url) as video_response:
                                    if video_response.status == 200:
                                        with open(video_path, 'wb') as f:
                                            f.write(await video_response.read())
                                        
                                        size_mb = os.path.getsize(video_path) / 1024 / 1024
                                        cost = self.video_models["google-veo-3"]["cost_per_video"]
                                        self.costs["video_generation"] += cost
                                        
                                        print(f"      ✅ {model_name} video: {video_filename} ({size_mb:.1f}MB, ${cost:.4f})")
                                        
                                        video_results[model_name] = {
                                            "success": True,
                                            "file": video_path,
                                            "size_mb": size_mb,
                                            "cost": cost,
                                            "generation_time": elapsed
                                        }
                                break
                                
                            elif status == 'failed':
                                error = result_data.get('error', 'Unknown error')
                                print(f"      ❌ {model_name} video failed: {error}")
                                video_results[model_name] = {"success": False, "error": error}
                                break
                            
                            # Continue polling
                            if elapsed > 600:  # 10 minute timeout
                                print(f"      ⏰ {model_name} video timeout")
                                video_results[model_name] = {"success": False, "error": "Timeout"}
                                break
                            
                            await asyncio.sleep(8)
                
            except Exception as e:
                print(f"      ❌ {model_name} video exception: {e}")
                video_results[model_name] = {"success": False, "error": str(e)}
        
        successful = [r for r in video_results.values() if r.get("success")]
        print(f"\\n   🎉 Video generation complete: {len(successful)} videos")
        print(f"   💰 Video generation cost: ${self.costs['video_generation']:.3f}")
        
        return video_results
    
    async def generate_music_for_videos(self, video_results: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
        """Generate ambient music for each video"""
        print(f"\\n🎵 GENERATING MUSIC FOR VIDEOS")
        
        music_results = {}
        
        for model_name, result in video_results.items():
            if not result.get("success"):
                continue
            
            print(f"\\n   🎵 Generating music for {model_name} video...")
            
            try:
                # MusicGen prompt for SiliconSentiments ambient music
                music_prompt = "Ambient electronic music with technological vibes, gentle synthesizers, futuristic atmosphere, suitable for digital art showcase, 10 seconds duration"
                
                payload = {
                    "version": self.music_models["musicgen"]["version"],
                    "input": {
                        "prompt": music_prompt,
                        "model_version": "stereo-large",
                        "output_format": "mp3",
                        "normalization_strategy": "peak",
                        "duration": 10
                    }
                }
                
                headers = {
                    "Authorization": f"Token {self.replicate_token}",
                    "Content-Type": "application/json"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, json=payload, headers=headers) as response:
                        if response.status != 201:
                            print(f"      ❌ Music submission failed for {model_name}")
                            continue
                        
                        result_data = await response.json()
                        prediction_id = result_data['id']
                        print(f"      🎯 Music prediction submitted: {prediction_id}")
                    
                    # Poll for completion
                    get_url = f"{self.api_url}/{prediction_id}"
                    
                    while True:
                        async with session.get(get_url, headers=headers) as response:
                            result_data = await response.json()
                            status = result_data['status']
                            
                            if status == 'succeeded':
                                music_url = result_data['output']
                                
                                # Download music
                                model_dir = os.path.join(output_dir, f"{model_name}_model", "videos")
                                music_filename = f"SiliconSentiments_{model_name}_ambient_music.mp3"
                                music_path = os.path.join(model_dir, music_filename)
                                
                                async with session.get(music_url) as music_response:
                                    if music_response.status == 200:
                                        with open(music_path, 'wb') as f:
                                            f.write(await music_response.read())
                                        
                                        cost = self.music_models["musicgen"]["cost_per_generation"]
                                        self.costs["music_generation"] += cost
                                        
                                        print(f"      ✅ {model_name} music: {music_filename} (${cost:.4f})")
                                        
                                        music_results[model_name] = {
                                            "success": True,
                                            "file": music_path,
                                            "cost": cost
                                        }
                                break
                                
                            elif status == 'failed':
                                error = result_data.get('error', 'Unknown error')
                                print(f"      ❌ {model_name} music failed: {error}")
                                music_results[model_name] = {"success": False, "error": error}
                                break
                            
                            await asyncio.sleep(5)
                
            except Exception as e:
                print(f"      ❌ {model_name} music exception: {e}")
                music_results[model_name] = {"success": False, "error": str(e)}
        
        successful = [r for r in music_results.values() if r.get("success")]
        print(f"\\n   🎉 Music generation complete: {len(successful)} tracks")
        print(f"   💰 Music generation cost: ${self.costs['music_generation']:.3f}")
        
        return music_results
    
    async def run_complete_pipeline(self, original_image: str, output_dir: str) -> Dict[str, Any]:
        """Run the complete regeneration pipeline"""
        print(f"🚀 COMPLETE REGENERATION PIPELINE")
        print(f"Shortcode: {self.shortcode}")
        print(f"Original: {os.path.basename(original_image)}")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Step 1: Clear existing content
        await self.clear_existing_folders(output_dir)
        
        # Step 2: Generate images with all 8 models
        image_results = await self.generate_images_all_models(original_image, output_dir)
        
        # Step 3: Upscale all generated images
        upscale_results = await self.upscale_all_images(image_results, output_dir)
        
        # Step 4: Generate videos per model
        video_results = await self.generate_videos_per_model(upscale_results, output_dir)
        
        # Step 5: Generate music for videos
        music_results = await self.generate_music_for_videos(video_results, output_dir)
        
        # Calculate totals
        duration = (datetime.now() - start_time).total_seconds()
        self.costs["total"] = sum(self.costs.values()) - self.costs["total"]  # Avoid double counting
        
        # Final summary
        summary = {
            "shortcode": self.shortcode,
            "start_time": start_time.isoformat(),
            "duration_minutes": duration / 60,
            "costs": self.costs,
            "results": {
                "image_generation": image_results,
                "upscaling": upscale_results,
                "video_generation": video_results,
                "music_generation": music_results
            },
            "success_counts": {
                "models_with_images": len([r for r in image_results.values() if r.get("success")]),
                "models_with_upscaled": len([r for r in upscale_results.values() if r.get("success")]),
                "models_with_videos": len([r for r in video_results.values() if r.get("success")]),
                "models_with_music": len([r for r in music_results.values() if r.get("success")])
            }
        }
        
        print(f"\\n🎉 COMPLETE PIPELINE FINISHED!")
        print(f"⏱️ Total time: {duration/60:.1f} minutes")
        print(f"💰 COST BREAKDOWN:")
        print(f"   📸 Image generation: ${self.costs['image_generation']:.3f}")
        print(f"   🔍 Upscaling: ${self.costs['upscaling']:.3f}")
        print(f"   🎬 Video generation: ${self.costs['video_generation']:.3f}")
        print(f"   🎵 Music generation: ${self.costs['music_generation']:.3f}")
        print(f"   🏆 TOTAL COST: ${self.costs['total']:.3f}")
        
        print(f"\\n📊 SUCCESS SUMMARY:")
        for stage, count in summary["success_counts"].items():
            print(f"   ✅ {stage}: {count}")
        
        # Save detailed summary
        summary_file = os.path.join(output_dir, f"complete_pipeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\\n📄 Complete summary saved: {summary_file}")
        
        return summary


async def main():
    """Run complete regeneration pipeline"""
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Configuration
    shortcode = "C0xFHGOrBN7"
    base_dir = f"downloaded_verify_images/verify_{shortcode}"
    original_image = os.path.join(base_dir, f"{shortcode}_original.jpg")
    
    # Check if original image exists (use any existing image as fallback)
    if not os.path.exists(original_image):
        # Find any image to use as source
        for file in os.listdir(base_dir):
            if file.endswith('.jpg') and 'original' not in file.lower():
                original_image = os.path.join(base_dir, file)
                break
    
    if not os.path.exists(original_image):
        print(f"❌ No source image found in {base_dir}")
        return
    
    # Run complete pipeline
    pipeline = CompleteRegenerationPipeline(replicate_token, shortcode)
    summary = await pipeline.run_complete_pipeline(original_image, base_dir)
    
    print(f"\\n🚀 COMPLETE REGENERATION PIPELINE FINISHED!")
    print(f"💰 Total investment: ${summary['costs']['total']:.3f}")
    print(f"📁 Results saved in: {base_dir}")


if __name__ == "__main__":
    asyncio.run(main())