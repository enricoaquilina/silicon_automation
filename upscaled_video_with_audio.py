#!/usr/bin/env python3
"""
Upscaled Video with Audio Pipeline
- Use upscaled images as video inputs
- Generate videos from high-resolution images
- Select best audio file and overlay on video
- Create final multimedia content
"""

import os
import asyncio
import aiohttp
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from multimedia_content_pipeline import MultimediaContentPipeline


class UpscaledVideoAudioPipeline(MultimediaContentPipeline):
    """Pipeline for creating videos from upscaled images with audio overlay"""
    
    def __init__(self, replicate_token: str, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        super().__init__(replicate_token, mongodb_uri)
    
    async def find_upscaled_images(self, directory: str) -> List[str]:
        """Find all upscaled images in directory"""
        upscaled_images = []
        for file in os.listdir(directory):
            if "_upscaled.jpg" in file:
                upscaled_images.append(os.path.join(directory, file))
        
        print(f"🔍 Found {len(upscaled_images)} upscaled images:")
        for img in upscaled_images:
            size = os.path.getsize(img)
            print(f"   📸 {os.path.basename(img)} ({size:,} bytes)")
        
        return upscaled_images
    
    async def find_audio_files(self, directory: str) -> List[str]:
        """Find all audio files in directory"""
        audio_files = []
        for file in os.listdir(directory):
            if file.endswith("_audio.mp3"):
                audio_files.append(os.path.join(directory, file))
        
        print(f"🎵 Found {len(audio_files)} audio files:")
        for audio in audio_files:
            size = os.path.getsize(audio)
            print(f"   🎶 {os.path.basename(audio)} ({size:,} bytes)")
        
        return audio_files
    
    async def generate_videos_from_upscaled_images(self, upscaled_images: List[str], 
                                                 output_dir: str, video_model: str = "animate-diff") -> List[Dict[str, Any]]:
        """Generate videos from all upscaled images"""
        video_results = []
        
        print(f"\n🎬 GENERATING VIDEOS FROM UPSCALED IMAGES")
        print(f"Model: {video_model}")
        print("=" * 60)
        
        for i, image_path in enumerate(upscaled_images, 1):
            base_name = os.path.splitext(os.path.basename(image_path))[0].replace("_upscaled", "")
            
            print(f"\n{i}/{len(upscaled_images)} 🎬 Processing {os.path.basename(image_path)}...")
            
            # Enhanced video prompt for upscaled content
            video_prompt = f"""High-resolution SiliconSentiments digital art animation based on upscaled artwork.
            
CONTENT: Futuristic cybernetic portrait with golden circuit patterns and neural networks
MOVEMENT: Subtle breathing motion, gentle particle flow, pulsing circuit elements, floating geometric shapes
CAMERA: Slow zoom in/out, gentle rotation around subject, smooth parallax depth
STYLE: Cinematic 4K quality, ethereal lighting, technological aesthetic, professional grade
MOOD: Contemplative, futuristic, artistic, brand-consistent SiliconSentiments theme
EFFECTS: Glowing circuit animation, particle systems, smooth light transitions, depth of field
QUALITY: Ultra high definition, crisp details, smooth motion, professional video production"""
            
            try:
                video_result = await self.generate_video_from_image(
                    image_path, video_prompt, 6, video_model
                )
                
                if video_result.get("success"):
                    # Download video
                    video_filename = f"{base_name}_hd_video.mp4"
                    video_path = await self.download_multimedia_content(
                        video_result["video_url"], video_filename, output_dir, "video"
                    )
                    
                    if video_path:
                        video_result["local_path"] = video_path
                        video_result["base_image"] = image_path
                        video_result["filename"] = video_filename
                        
                        # Save to GridFS
                        gridfs_id = await self.save_multimedia_to_gridfs(
                            video_path, 
                            {
                                "shortcode": base_name,
                                "content_type": "hd_video",
                                "source_image": image_path,
                                "video_model": video_model,
                                "pipeline_stage": "upscaled_video_generation",
                                "brand": "SiliconSentiments"
                            },
                            "video/mp4"
                        )
                        video_result["gridfs_id"] = gridfs_id
                        
                        print(f"   ✅ Video generated: {video_filename}")
                    else:
                        print(f"   ❌ Video download failed")
                        video_result["success"] = False
                else:
                    print(f"   ❌ Video generation failed: {video_result.get('error')}")
                
                video_results.append(video_result)
                
            except Exception as e:
                print(f"   ❌ Error processing {image_path}: {e}")
                video_results.append({
                    "success": False,
                    "error": str(e),
                    "base_image": image_path
                })
        
        return video_results
    
    def select_best_audio(self, audio_files: List[str]) -> str:
        """Select the best audio file (largest/highest quality)"""
        if not audio_files:
            return None
        
        best_audio = max(audio_files, key=lambda x: os.path.getsize(x))
        size = os.path.getsize(best_audio)
        
        print(f"🎯 Selected best audio: {os.path.basename(best_audio)} ({size:,} bytes)")
        return best_audio
    
    async def overlay_audio_on_videos(self, video_results: List[Dict[str, Any]], 
                                    audio_file: str, output_dir: str) -> List[Dict[str, Any]]:
        """Overlay audio on all generated videos using ffmpeg"""
        final_results = []
        
        if not audio_file:
            print("⚠️ No audio file available for overlay")
            return video_results
        
        print(f"\n🎵 OVERLAYING AUDIO ON VIDEOS")
        print(f"Audio: {os.path.basename(audio_file)}")
        print("=" * 60)
        
        for i, video_result in enumerate(video_results, 1):
            if not video_result.get("success") or not video_result.get("local_path"):
                final_results.append(video_result)
                continue
            
            video_path = video_result["local_path"]
            base_name = os.path.splitext(video_result["filename"])[0]
            final_filename = f"{base_name}_with_audio.mp4"
            final_path = os.path.join(output_dir, final_filename)
            
            print(f"\n{i}/{len(video_results)} 🎵 Adding audio to {video_result['filename']}...")
            
            try:
                # Use ffmpeg to overlay audio on video
                cmd = [
                    'ffmpeg', '-y',  # -y to overwrite existing files
                    '-i', video_path,  # Input video
                    '-i', audio_file,  # Input audio
                    '-c:v', 'copy',  # Copy video codec (no re-encoding)
                    '-c:a', 'aac',  # Audio codec
                    '-shortest',  # End when shortest stream ends
                    '-map', '0:v:0',  # Map video from first input
                    '-map', '1:a:0',  # Map audio from second input
                    final_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(final_path):
                    size = os.path.getsize(final_path)
                    print(f"   ✅ Audio overlay complete: {final_filename} ({size:,} bytes)")
                    
                    # Save to GridFS
                    gridfs_id = await self.save_multimedia_to_gridfs(
                        final_path,
                        {
                            **video_result.get("metadata", {}),
                            "has_audio": True,
                            "audio_file": os.path.basename(audio_file),
                            "pipeline_stage": "final_multimedia_content"
                        },
                        "video/mp4"
                    )
                    
                    final_result = {
                        **video_result,
                        "final_video_path": final_path,
                        "final_filename": final_filename,
                        "has_audio": True,
                        "audio_source": audio_file,
                        "final_gridfs_id": gridfs_id,
                        "final_size_bytes": size
                    }
                    
                else:
                    print(f"   ❌ FFmpeg failed: {result.stderr}")
                    final_result = {
                        **video_result,
                        "audio_overlay_failed": True,
                        "ffmpeg_error": result.stderr
                    }
                
                final_results.append(final_result)
                
            except Exception as e:
                print(f"   ❌ Audio overlay error: {e}")
                final_results.append({
                    **video_result,
                    "audio_overlay_failed": True,
                    "error": str(e)
                })
        
        return final_results
    
    async def create_complete_multimedia_from_upscaled(self, directory: str, 
                                                     video_model: str = "animate-diff") -> Dict[str, Any]:
        """Complete pipeline: upscaled images → videos → audio overlay"""
        
        print(f"🚀 COMPLETE UPSCALED MULTIMEDIA PIPELINE")
        print(f"Directory: {directory}")
        print(f"Video Model: {video_model}")
        print("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Find upscaled images and audio files
            print(f"\n1️⃣ SCANNING DIRECTORY...")
            upscaled_images = await self.find_upscaled_images(directory)
            audio_files = await self.find_audio_files(directory)
            
            if not upscaled_images:
                return {"success": False, "error": "No upscaled images found"}
            
            # Step 2: Generate videos from upscaled images
            print(f"\n2️⃣ GENERATING HIGH-QUALITY VIDEOS...")
            video_results = await self.generate_videos_from_upscaled_images(
                upscaled_images, directory, video_model
            )
            
            successful_videos = [v for v in video_results if v.get("success")]
            
            # Step 3: Select best audio and overlay
            print(f"\n3️⃣ AUDIO OVERLAY...")
            best_audio = self.select_best_audio(audio_files)
            final_results = await self.overlay_audio_on_videos(
                video_results, best_audio, directory
            )
            
            # Calculate stats
            duration = (datetime.now() - start_time).total_seconds()
            total_cost = sum(v.get("cost_estimate", 0) for v in video_results)
            final_videos = [v for v in final_results if v.get("final_video_path")]
            
            result = {
                "success": True,
                "directory": directory,
                "upscaled_images_processed": len(upscaled_images),
                "videos_generated": len(successful_videos),
                "final_videos_with_audio": len(final_videos),
                "best_audio_file": best_audio,
                "video_model": video_model,
                "video_results": video_results,
                "final_results": final_results,
                "total_cost": total_cost,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\n🎉 UPSCALED MULTIMEDIA PIPELINE COMPLETE!")
            print(f"✅ Generated {len(final_videos)} final videos with audio")
            print(f"⏱️ Duration: {duration:.1f}s")
            print(f"💰 Total cost: ${total_cost:.3f}")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"\n❌ PIPELINE FAILED: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }


async def main():
    """Run the upscaled video with audio pipeline"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python upscaled_video_with_audio.py <directory> [video_model]")
        print("Example: python upscaled_video_with_audio.py downloaded_verify_images/verify_C0xFHGOrBN7/ animate-diff")
        return
    
    directory = sys.argv[1]
    video_model = sys.argv[2] if len(sys.argv) > 2 else "animate-diff"
    
    # Check for Replicate token
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found. Please install FFmpeg for audio overlay functionality.")
        print("   macOS: brew install ffmpeg")
        print("   Ubuntu: sudo apt install ffmpeg")
        return
    
    # Run pipeline
    pipeline = UpscaledVideoAudioPipeline(replicate_token)
    result = await pipeline.create_complete_multimedia_from_upscaled(directory, video_model)
    
    # Save result
    report_path = os.path.join(directory, f'upscaled_multimedia_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n📄 Result saved: {report_path}")
    
    if result.get('success'):
        print(f"\n🎉 SUCCESS! Complete upscaled multimedia content created!")
        print(f"🚀 Ready for @siliconsentiments_art deployment!")


if __name__ == "__main__":
    asyncio.run(main())