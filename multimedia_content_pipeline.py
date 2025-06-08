#!/usr/bin/env python3
"""
Enhanced Multimedia Content Pipeline
- Image Generation (existing models)
- Image Upscaling (Real-ESRGAN, Clarity)
- Video Generation (LTX-Video) 
- Audio Synthesis (MusicGen)
- Complete multimedia content creation for SiliconSentiments
"""

import os
import asyncio
import aiohttp
import json
import base64
import sys
from datetime import datetime
from PIL import Image
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from gridfs import GridFS

# Import our existing pipeline
from enhanced_multi_model_pipeline import EnhancedMultiModelPipeline


class MultimediaContentPipeline(EnhancedMultiModelPipeline):
    """Enhanced pipeline with upscaling, video generation, and audio synthesis"""
    
    # Multimedia models configuration
    MULTIMEDIA_MODELS = {
        "real-esrgan": {
            "version": "f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa",
            "cost_per_second": 0.000225,
            "type": "upscaler",
            "description": "Real-ESRGAN super-resolution upscaler"
        },
        "clarity-upscaler": {
            "version": "dfad41707589d68ecdccd1dfa600d55a208f9310748e44bfe35b4a6291453d5e", 
            "cost_per_second": 0.00115,
            "type": "upscaler",
            "description": "Clarity AI high-resolution upscaler"
        },
        "ltx-video": {
            "version": "8c47da666861d081eeb4d1261853087de23923a268a69b63febdf5dc1dee08e4",
            "cost_per_second": 0.000975,
            "type": "video_generator",
            "description": "LTX-Video generation model"
        },
        "minimax-video-01": {
            "version": "c8bcc4751328608bb75043b3af7bed4eabcf1a6c0a478d50a4cf57fa04bd5101",
            "cost_per_second": 0.020,
            "type": "video_generator", 
            "description": "Minimax Video-01 6s video generation"
        },
        "animate-diff": {
            "version": "1531004ee4c98894ab11f8a4ce6206099e732c1da15121987a8eef54828f0663",
            "cost_per_second": 0.0023,
            "type": "video_generator",
            "description": "AnimateDiff text-to-video animation"
        },
        "musicgen": {
            "version": "671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
            "cost_per_second": 0.000725,
            "type": "audio_generator", 
            "description": "MusicGen audio synthesis"
        }
    }
    
    def __init__(self, replicate_token: str, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        super().__init__(replicate_token, mongodb_uri)
        
    async def upscale_image(self, image_path: str, upscaler_model: str = "real-esrgan", 
                           scale_factor: int = 4) -> Dict[str, Any]:
        """Upscale an image using specified upscaler model"""
        
        if upscaler_model not in self.MULTIMEDIA_MODELS:
            raise Exception(f"Upscaler '{upscaler_model}' not available")
        
        model_config = self.MULTIMEDIA_MODELS[upscaler_model]
        print(f"⬆️  Upscaling with {model_config['description']} ({scale_factor}x)...")
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{image_b64}"
            
            # Configure payload based on upscaler
            if upscaler_model == "real-esrgan":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "image": data_uri,
                        "scale": scale_factor,
                        "face_enhance": False
                    }
                }
            elif upscaler_model == "clarity-upscaler":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "image": data_uri,
                        "scale_factor": scale_factor,
                        "prompt": "high resolution digital art, sharp details, professional quality",
                        "negative_prompt": "blurry, low quality, pixelated",
                        "creativity": 0.3,
                        "resemblance": 0.8
                    }
                }
            
            headers = {
                "Authorization": f"Token {self.replicate_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.replicate_api_url, 
                                      json=payload, headers=headers) as response:
                    if response.status != 201:
                        error_text = await response.text()
                        raise Exception(f"Upscaler submission failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   📝 Upscaling prediction: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.replicate_api_url}/{prediction_id}"
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            upscaled_url = result['output']
                            if isinstance(upscaled_url, list):
                                upscaled_url = upscaled_url[0]
                            
                            print(f"   ✅ Upscaling complete!")
                            return {
                                "success": True,
                                "upscaled_url": upscaled_url,
                                "model": upscaler_model,
                                "scale_factor": scale_factor,
                                "cost_estimate": model_config["cost_per_second"] * 10  # Estimate
                            }
                        elif result['status'] == 'failed':
                            raise Exception(f"Upscaling failed: {result.get('error')}")
                        
                        await asyncio.sleep(3)
                        
        except Exception as e:
            print(f"   ❌ Upscaling error: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_video_from_image(self, image_path: str, prompt: str, 
                                      duration: int = 5, video_model: str = "minimax-video-01") -> Dict[str, Any]:
        """Generate video from image using specified video model"""
        
        if video_model not in self.MULTIMEDIA_MODELS:
            video_model = "minimax-video-01"  # Fallback to reliable model
            
        model_config = self.MULTIMEDIA_MODELS[video_model]
        print(f"🎬 Generating video with {model_config['description']} ({duration}s)...")
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{image_b64}"
            
            # Enhanced video prompt for SiliconSentiments
            video_prompt = f"""SiliconSentiments digital art animation: {prompt}
            
MOVEMENT: Gentle floating particles, subtle geometric transformations, flowing energy streams, pulsing light effects
CAMERA: Slow zoom, gentle rotation, smooth parallax movement
STYLE: Cinematic, ethereal, technological, professional quality
MOOD: Futuristic, contemplative, artistic, brand-consistent
EFFECTS: Glowing accents, particle systems, smooth transitions"""

            # Configure payload based on video model
            if video_model == "ltx-video":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "image": data_uri,
                        "prompt": video_prompt,
                        "aspect_ratio": "1:1",
                        "duration": duration,
                        "guidance_scale": 3.0,
                        "num_inference_steps": 30
                    }
                }
            elif video_model == "minimax-video-01":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "first_frame_image": data_uri,
                        "prompt": video_prompt,
                        "prompt_optimizer": True
                    }
                }
                duration = 6  # Minimax fixed duration
            elif video_model == "animate-diff":
                payload = {
                    "version": model_config["version"],
                    "input": {
                        "prompt": video_prompt,
                        "seed": 42,
                        "steps": 25,
                        "guidance_scale": 7.5,
                        "motion_module": "mm_sd_v14"
                    }
                }
            
            headers = {
                "Authorization": f"Token {self.replicate_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.replicate_api_url, 
                                      json=payload, headers=headers) as response:
                    if response.status != 201:
                        error_text = await response.text()
                        raise Exception(f"Video generation failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   📝 Video generation prediction: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.replicate_api_url}/{prediction_id}"
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            video_url = result['output']
                            if isinstance(video_url, list):
                                video_url = video_url[0]
                            
                            print(f"   ✅ Video generation complete!")
                            return {
                                "success": True,
                                "video_url": video_url,
                                "duration": duration,
                                "prompt": video_prompt,
                                "model": video_model,
                                "cost_estimate": model_config["cost_per_second"] * duration
                            }
                        elif result['status'] == 'failed':
                            raise Exception(f"Video generation failed: {result.get('error')}")
                        
                        await asyncio.sleep(5)
                        
        except Exception as e:
            print(f"   ❌ Video generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_audio(self, description: str, duration: int = 30) -> Dict[str, Any]:
        """Generate audio using MusicGen"""
        
        model_config = self.MULTIMEDIA_MODELS["musicgen"]
        print(f"🎵 Generating audio with {model_config['description']} ({duration}s)...")
        
        try:
            # Create SiliconSentiments audio prompt
            audio_prompt = f"""Futuristic ambient electronic music inspired by {description}. 
            
STYLE: Ambient electronic, cyberpunk, technological soundscape
ELEMENTS: Synthesized textures, digital atmospheres, gentle rhythms, ethereal tones
MOOD: Contemplative, innovative, futuristic, artistic
INSTRUMENTS: Synthesizers, digital effects, ambient pads, subtle percussion
QUALITY: High-fidelity, professional, cinematic"""

            payload = {
                "version": model_config["version"],
                "input": {
                    "prompt": audio_prompt,
                    "model_version": "stereo-melody-large",
                    "output_format": "mp3",
                    "normalization_strategy": "loudness",
                    "duration": duration
                }
            }
            
            headers = {
                "Authorization": f"Token {self.replicate_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.replicate_api_url, 
                                      json=payload, headers=headers) as response:
                    if response.status != 201:
                        error_text = await response.text()
                        raise Exception(f"Audio generation failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    prediction_id = result['id']
                    print(f"   📝 Audio generation prediction: {prediction_id}")
                
                # Poll for completion
                get_url = f"{self.replicate_api_url}/{prediction_id}"
                while True:
                    async with session.get(get_url, headers=headers) as response:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            audio_url = result['output']
                            if isinstance(audio_url, list):
                                audio_url = audio_url[0]
                            
                            print(f"   ✅ Audio generation complete!")
                            return {
                                "success": True,
                                "audio_url": audio_url,
                                "duration": duration,
                                "prompt": audio_prompt,
                                "cost_estimate": model_config["cost_per_second"] * duration
                            }
                        elif result['status'] == 'failed':
                            raise Exception(f"Audio generation failed: {result.get('error')}")
                        
                        await asyncio.sleep(5)
                        
        except Exception as e:
            print(f"   ❌ Audio generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def download_multimedia_content(self, url: str, filename: str, output_dir: str, 
                                        content_type: str = "image") -> Optional[str]:
        """Download multimedia content (image/video/audio)"""
        try:
            filepath = os.path.join(output_dir, filename)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(filepath, 'wb') as f:
                            f.write(await response.read())
                        
                        size = os.path.getsize(filepath)
                        print(f"   ✅ Downloaded {content_type}: {filename} ({size:,} bytes)")
                        return filepath
                    else:
                        print(f"   ❌ Download failed: {response.status}")
                        return None
            
        except Exception as e:
            print(f"   ❌ Download error: {e}")
            return None
    
    async def save_multimedia_to_gridfs(self, file_path: str, metadata: Dict[str, Any], 
                                      content_type: str) -> Optional[str]:
        """Save multimedia content to GridFS"""
        if not self.fs:
            return None
        
        try:
            with open(file_path, 'rb') as f:
                file_id = self.fs.put(
                    f,
                    filename=os.path.basename(file_path),
                    metadata={
                        **metadata,
                        "content_type": content_type,
                        "multimedia_pipeline": "v1.0",
                        "created_at": datetime.now().isoformat()
                    },
                    contentType=content_type
                )
            
            print(f"   💾 Saved to GridFS: {file_id}")
            return str(file_id)
            
        except Exception as e:
            print(f"   ❌ GridFS save error: {e}")
            return None
    
    async def create_complete_multimedia_content(self, image_path: str, shortcode: str, 
                                               output_dir: str, vlm_model: str = "llava-13b",
                                               generation_models: List[str] = None) -> Dict[str, Any]:
        """Create complete multimedia content: Image → Upscale → Video → Audio"""
        
        if generation_models is None:
            generation_models = ["flux-1.1-pro", "recraft-v3"]
        
        print(f"🚀 COMPLETE MULTIMEDIA CONTENT PIPELINE")
        print(f"Input: {image_path}")
        print(f"Shortcode: {shortcode}")
        print(f"Models: {', '.join(generation_models)}")
        print("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Generate base images with existing pipeline
            print(f"\n1️⃣ GENERATING BASE IMAGES...")
            base_result = await self.process_image_with_models(
                image_path, shortcode, output_dir, generation_models, vlm_model
            )
            
            if not base_result.get("success"):
                return {"success": False, "error": "Base image generation failed"}
            
            # Step 2: Process each generated image with multimedia pipeline
            multimedia_results = []
            total_cost = base_result.get("total_cost", 0)
            
            for model_name, model_result in base_result.get("model_results", {}).items():
                if not model_result.get("success"):
                    continue
                
                for file_info in model_result.get("generated_files", []):
                    image_file = file_info["filepath"]
                    base_filename = os.path.splitext(file_info["filename"])[0]
                    
                    print(f"\n2️⃣ PROCESSING {file_info['filename']}...")
                    
                    # Step 2a: Upscale image
                    print(f"  📈 Upscaling...")
                    upscale_result = await self.upscale_image(image_file, "real-esrgan", 4)
                    
                    upscaled_path = None
                    if upscale_result.get("success"):
                        upscaled_filename = f"{base_filename}_upscaled.jpg"
                        upscaled_path = await self.download_multimedia_content(
                            upscale_result["upscaled_url"], upscaled_filename, output_dir, "image"
                        )
                        total_cost += upscale_result.get("cost_estimate", 0)
                    
                    # Step 2b: Generate video
                    print(f"  🎬 Generating video...")
                    video_description = base_result.get("vlm_description", "digital artwork")
                    video_result = await self.generate_video_from_image(
                        upscaled_path or image_file, video_description, 5
                    )
                    
                    video_path = None
                    if video_result.get("success"):
                        video_filename = f"{base_filename}_video.mp4"
                        video_path = await self.download_multimedia_content(
                            video_result["video_url"], video_filename, output_dir, "video"
                        )
                        total_cost += video_result.get("cost_estimate", 0)
                    
                    # Step 2c: Generate audio
                    print(f"  🎵 Generating audio...")
                    audio_result = await self.generate_audio(video_description, 30)
                    
                    audio_path = None
                    if audio_result.get("success"):
                        audio_filename = f"{base_filename}_audio.mp3"
                        audio_path = await self.download_multimedia_content(
                            audio_result["audio_url"], audio_filename, output_dir, "audio"
                        )
                        total_cost += audio_result.get("cost_estimate", 0)
                    
                    # Step 2d: Save all to GridFS
                    multimedia_metadata = {
                        "shortcode": shortcode,
                        "base_model": model_name,
                        "variation": file_info["variation"],
                        "pipeline_stage": "multimedia_enhanced",
                        "brand": "SiliconSentiments"
                    }
                    
                    gridfs_ids = {}
                    if upscaled_path:
                        gridfs_ids["upscaled"] = await self.save_multimedia_to_gridfs(
                            upscaled_path, multimedia_metadata, "image/jpeg"
                        )
                    if video_path:
                        gridfs_ids["video"] = await self.save_multimedia_to_gridfs(
                            video_path, multimedia_metadata, "video/mp4"
                        )
                    if audio_path:
                        gridfs_ids["audio"] = await self.save_multimedia_to_gridfs(
                            audio_path, multimedia_metadata, "audio/mpeg"
                        )
                    
                    multimedia_results.append({
                        "base_image": file_info,
                        "upscaled_image": upscaled_path,
                        "video": video_path,
                        "audio": audio_path,
                        "gridfs_ids": gridfs_ids,
                        "upscale_result": upscale_result,
                        "video_result": video_result,
                        "audio_result": audio_result
                    })
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "shortcode": shortcode,
                "base_generation": base_result,
                "multimedia_content": multimedia_results,
                "total_content_pieces": len(multimedia_results),
                "total_cost": total_cost,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\n🎉 MULTIMEDIA PIPELINE COMPLETE!")
            print(f"✅ Generated {len(multimedia_results)} complete multimedia sets")
            print(f"⏱️ Duration: {duration:.1f}s")
            print(f"💰 Total cost: ${total_cost:.3f}")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"\n❌ MULTIMEDIA PIPELINE FAILED: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }


async def main():
    """Run the complete multimedia content pipeline"""
    if len(sys.argv) < 3:
        print("Usage: python multimedia_content_pipeline.py <image_path> <shortcode> [models] [vlm]")
        print("Example: python multimedia_content_pipeline.py image.jpg C0xFHGOrBN7 flux-1.1-pro,recraft-v3 llava-13b")
        return
    
    image_path = sys.argv[1]
    shortcode = sys.argv[2]
    
    # Parse models
    if len(sys.argv) > 3:
        models = [m.strip() for m in sys.argv[3].split(',')]
    else:
        models = ["flux-1.1-pro", "recraft-v3"]
    
    # Parse VLM
    vlm_model = "llava-13b"
    if len(sys.argv) > 4:
        vlm_model = sys.argv[4].strip()
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Setup output directory
    output_dir = os.path.dirname(image_path)
    
    # Run multimedia pipeline
    pipeline = MultimediaContentPipeline(replicate_token)
    result = await pipeline.create_complete_multimedia_content(
        image_path, shortcode, output_dir, vlm_model, models
    )
    
    # Save result
    report_path = os.path.join(output_dir, f'multimedia_content_result_{shortcode}.json')
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n📄 Result saved: {report_path}")
    
    if result.get('success'):
        print(f"\n🎉 SUCCESS! Complete multimedia content pipeline!")
        print(f"🚀 Ready for @siliconsentiments_art deployment!")


if __name__ == "__main__":
    asyncio.run(main())