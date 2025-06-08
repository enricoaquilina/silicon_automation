#!/usr/bin/env python3
"""
Complete Multi-Model Multimedia Pipeline
- Process ALL generated images from multiple AI models
- Upscale each image with Real-ESRGAN
- Generate videos from all upscaled images
- Create audio overlays for all videos
- Organize by model type and create model-specific compilations
- Generate final comprehensive compilation
"""

import os
import asyncio
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from multimedia_content_pipeline import MultimediaContentPipeline


class CompleteMultiModelMultimediaPipeline(MultimediaContentPipeline):
    """Complete pipeline for processing all AI model generations"""
    
    def __init__(self, replicate_token: str, mongodb_uri: str = "mongodb://192.168.0.22:27017/"):
        super().__init__(replicate_token, mongodb_uri)
        
        # Model categories for organization
        self.model_categories = {
            "recraft": ["recraft", "recraft_v3"],
            "flux": ["flux", "flux11pro", "flux-1.1-pro"],
            "sdxl": ["sdxl"],
            "kandinsky": ["kandinsky"]
        }
    
    def categorize_images_by_model(self, generations_dir: str) -> Dict[str, List[str]]:
        """Categorize generated images by AI model type"""
        categorized = {category: [] for category in self.model_categories.keys()}
        categorized["other"] = []
        
        if not os.path.exists(generations_dir):
            print(f"❌ Generations directory not found: {generations_dir}")
            return categorized
        
        print(f"🔍 Categorizing images by model type...")
        
        for file in os.listdir(generations_dir):
            if file.endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(generations_dir, file)
                categorized_flag = False
                
                # Check which model category this image belongs to
                for category, model_names in self.model_categories.items():
                    if any(model_name in file.lower() for model_name in model_names):
                        categorized[category].append(file_path)
                        categorized_flag = True
                        break
                
                if not categorized_flag:
                    categorized["other"].append(file_path)
        
        # Print categorization summary
        for category, files in categorized.items():
            if files:
                print(f"   📸 {category.upper()}: {len(files)} images")
        
        return categorized
    
    async def process_model_category(self, category: str, image_files: List[str], 
                                   output_base_dir: str, video_model: str = "animate-diff") -> Dict[str, Any]:
        """Process all images from a specific model category"""
        
        if not image_files:
            return {"success": False, "error": f"No images found for {category}"}
        
        print(f"\n🎨 PROCESSING {category.upper()} MODEL CATEGORY")
        print(f"Images: {len(image_files)}")
        print("=" * 60)
        
        # Create category-specific directories
        category_dir = os.path.join(output_base_dir, f"model_{category}")
        upscaled_dir = os.path.join(category_dir, "upscaled")
        videos_dir = os.path.join(category_dir, "videos")
        
        os.makedirs(upscaled_dir, exist_ok=True)
        os.makedirs(videos_dir, exist_ok=True)
        
        results = {
            "category": category,
            "total_images": len(image_files),
            "upscaled_results": [],
            "video_results": [],
            "total_cost": 0,
            "success": True
        }
        
        try:
            # Step 1: Upscale all images in this category
            print(f"\n1️⃣ UPSCALING {len(image_files)} {category.upper()} IMAGES...")
            for i, image_path in enumerate(image_files, 1):
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                
                print(f"\n{i}/{len(image_files)} 📈 Upscaling {os.path.basename(image_path)}...")
                
                upscale_result = await self.upscale_image(image_path, "real-esrgan", 4)
                
                if upscale_result.get("success"):
                    # Download upscaled image
                    upscaled_filename = f"{base_name}_upscaled.jpg"
                    upscaled_path = await self.download_multimedia_content(
                        upscale_result["upscaled_url"], upscaled_filename, upscaled_dir, "image"
                    )
                    
                    if upscaled_path:
                        upscale_result["local_path"] = upscaled_path
                        upscale_result["original_image"] = image_path
                        results["total_cost"] += upscale_result.get("cost_estimate", 0)
                        
                        # Save to GridFS
                        gridfs_id = await self.save_multimedia_to_gridfs(
                            upscaled_path,
                            {
                                "category": category,
                                "original_image": image_path,
                                "upscale_model": "real-esrgan",
                                "pipeline_stage": "multi_model_upscaling",
                                "brand": "SiliconSentiments"
                            },
                            "image/jpeg"
                        )
                        upscale_result["gridfs_id"] = gridfs_id
                
                results["upscaled_results"].append(upscale_result)
            
            # Step 2: Generate videos from upscaled images
            successful_upscales = [r for r in results["upscaled_results"] if r.get("success") and r.get("local_path")]
            
            if successful_upscales:
                print(f"\n2️⃣ GENERATING VIDEOS FROM {len(successful_upscales)} UPSCALED IMAGES...")
                
                for i, upscale_result in enumerate(successful_upscales, 1):
                    upscaled_path = upscale_result["local_path"]
                    base_name = os.path.splitext(os.path.basename(upscaled_path))[0].replace("_upscaled", "")
                    
                    print(f"\n{i}/{len(successful_upscales)} 🎬 Creating video from {os.path.basename(upscaled_path)}...")
                    
                    # Enhanced video prompt for each category
                    video_prompt = f"""SiliconSentiments {category} model digital art animation.
                    
CONTENT: High-resolution cybernetic portrait with advanced neural network visualization
MOVEMENT: Fluid geometric transformations, pulsing circuit elements, floating data particles
CAMERA: Cinematic slow zoom, gentle rotation, smooth depth transitions  
STYLE: Professional 4K {category} aesthetic, ethereal lighting, technological beauty
MOOD: Futuristic consciousness, digital transcendence, artistic innovation
EFFECTS: Dynamic circuit animation, particle systems, holographic overlays, depth of field
QUALITY: Ultra high definition, crisp details, smooth motion, broadcast quality"""
                    
                    video_result = await self.generate_video_from_image(
                        upscaled_path, video_prompt, 6, video_model
                    )
                    
                    if video_result.get("success"):
                        # Download video
                        video_filename = f"{base_name}_{category}_hd_video.mp4"
                        video_path = await self.download_multimedia_content(
                            video_result["video_url"], video_filename, videos_dir, "video"
                        )
                        
                        if video_path:
                            video_result["local_path"] = video_path
                            video_result["upscaled_source"] = upscaled_path
                            video_result["category"] = category
                            results["total_cost"] += video_result.get("cost_estimate", 0)
                            
                            # Save to GridFS
                            gridfs_id = await self.save_multimedia_to_gridfs(
                                video_path,
                                {
                                    "category": category,
                                    "upscaled_source": upscaled_path,
                                    "video_model": video_model,
                                    "pipeline_stage": "multi_model_video_generation",
                                    "brand": "SiliconSentiments"
                                },
                                "video/mp4"
                            )
                            video_result["gridfs_id"] = gridfs_id
                    
                    results["video_results"].append(video_result)
            
            # Calculate success metrics
            successful_videos = [r for r in results["video_results"] if r.get("success")]
            results["successful_upscales"] = len(successful_upscales)
            results["successful_videos"] = len(successful_videos)
            
            print(f"\n✅ {category.upper()} PROCESSING COMPLETE!")
            print(f"   📈 Upscaled: {len(successful_upscales)}/{len(image_files)} images")
            print(f"   🎬 Videos: {len(successful_videos)}/{len(successful_upscales)} generated")
            print(f"   💰 Cost: ${results['total_cost']:.3f}")
            
            return results
            
        except Exception as e:
            print(f"\n❌ {category.upper()} PROCESSING FAILED: {e}")
            results["success"] = False
            results["error"] = str(e)
            return results
    
    async def create_model_compilation(self, category: str, video_results: List[Dict], 
                                     category_dir: str, audio_file: str = None) -> Optional[str]:
        """Create a compilation video for a specific model category"""
        
        successful_videos = [r for r in video_results if r.get("success") and r.get("local_path")]
        
        if len(successful_videos) < 2:
            print(f"   ⚠️ {category.upper()}: Not enough videos for compilation ({len(successful_videos)} videos)")
            return None
        
        print(f"\n🎬 Creating {category.upper()} compilation from {len(successful_videos)} videos...")
        
        # Create concat file
        concat_file = os.path.join(category_dir, f"{category}_concat.txt")
        with open(concat_file, 'w') as f:
            for video_result in successful_videos:
                abs_path = os.path.abspath(video_result["local_path"])
                f.write(f"file '{abs_path}'\\n")
        
        # Output compilation file
        compilation_filename = f"SiliconSentiments_{category}_compilation.mp4"
        compilation_path = os.path.join(category_dir, compilation_filename)
        
        try:
            # FFmpeg concatenation
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                compilation_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(compilation_path):
                os.remove(concat_file)  # Clean up
                
                size = os.path.getsize(compilation_path)
                duration = len(successful_videos) * 2.1  # Approximate duration
                
                print(f"   ✅ {category.upper()} compilation created: {compilation_filename}")
                print(f"   📏 Duration: {duration:.1f}s | Size: {size/1024/1024:.1f}MB")
                
                return compilation_path
            else:
                print(f"   ❌ {category.upper()} compilation failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"   ❌ {category.upper()} compilation error: {e}")
            return None
    
    async def create_master_compilation(self, model_compilations: List[str], 
                                      output_dir: str, audio_file: str = None) -> Optional[str]:
        """Create master compilation from all model compilations"""
        
        valid_compilations = [c for c in model_compilations if c and os.path.exists(c)]
        
        if len(valid_compilations) < 2:
            print(f"⚠️ Not enough model compilations for master compilation ({len(valid_compilations)} available)")
            return None
        
        print(f"\n🎬 CREATING MASTER COMPILATION from {len(valid_compilations)} model compilations...")
        
        # Create master concat file
        concat_file = os.path.join(output_dir, "master_concat.txt")
        with open(concat_file, 'w') as f:
            for compilation_path in valid_compilations:
                abs_path = os.path.abspath(compilation_path)
                f.write(f"file '{abs_path}'\\n")
        
        # Output master compilation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        master_filename = f"SiliconSentiments_MASTER_compilation_{timestamp}.mp4"
        master_path = os.path.join(output_dir, master_filename)
        
        try:
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0', 
                '-i', concat_file,
                '-c', 'copy',
                master_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(master_path):
                os.remove(concat_file)  # Clean up
                
                size = os.path.getsize(master_path)
                
                print(f"   ✅ MASTER COMPILATION CREATED: {master_filename}")
                print(f"   💾 Size: {size/1024/1024:.1f}MB")
                
                return master_path
            else:
                print(f"   ❌ Master compilation failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"   ❌ Master compilation error: {e}")
            return None
    
    async def complete_multi_model_pipeline(self, base_directory: str, 
                                          video_model: str = "animate-diff") -> Dict[str, Any]:
        """Complete pipeline: All models → Upscale → Videos → Compilations"""
        
        print(f"🚀 COMPLETE MULTI-MODEL MULTIMEDIA PIPELINE")
        print(f"Base Directory: {base_directory}")
        print(f"Video Model: {video_model}")
        print("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Setup directories
            generations_dir = os.path.join(base_directory, "02_generations")
            output_dir = os.path.join(base_directory, "multi_model_multimedia")
            os.makedirs(output_dir, exist_ok=True)
            
            # Step 1: Categorize images by model
            print(f"\\n1️⃣ CATEGORIZING IMAGES BY MODEL...")
            categorized_images = self.categorize_images_by_model(generations_dir)
            
            total_images = sum(len(files) for files in categorized_images.values())
            if total_images == 0:
                return {"success": False, "error": "No images found to process"}
            
            # Step 2: Process each model category
            print(f"\\n2️⃣ PROCESSING {total_images} IMAGES ACROSS ALL MODELS...")
            model_results = {}
            total_cost = 0
            
            for category, image_files in categorized_images.items():
                if image_files:  # Only process categories with images
                    result = await self.process_model_category(
                        category, image_files, output_dir, video_model
                    )
                    model_results[category] = result
                    total_cost += result.get("total_cost", 0)
            
            # Step 3: Create model-specific compilations
            print(f"\\n3️⃣ CREATING MODEL-SPECIFIC COMPILATIONS...")
            model_compilations = []
            
            for category, result in model_results.items():
                if result.get("success") and result.get("video_results"):
                    category_dir = os.path.join(output_dir, f"model_{category}")
                    compilation_path = await self.create_model_compilation(
                        category, result["video_results"], category_dir
                    )
                    if compilation_path:
                        model_compilations.append(compilation_path)
            
            # Step 4: Create master compilation
            print(f"\\n4️⃣ CREATING MASTER COMPILATION...")
            master_compilation = await self.create_master_compilation(
                model_compilations, output_dir
            )
            
            # Calculate final metrics
            duration = (datetime.now() - start_time).total_seconds()
            total_upscaled = sum(r.get("successful_upscales", 0) for r in model_results.values())
            total_videos = sum(r.get("successful_videos", 0) for r in model_results.values())
            
            result = {
                "success": True,
                "base_directory": base_directory,
                "total_images_processed": total_images,
                "total_upscaled": total_upscaled,
                "total_videos_generated": total_videos,
                "model_results": model_results,
                "model_compilations": model_compilations,
                "master_compilation": master_compilation,
                "total_cost": total_cost,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\\n🎉 COMPLETE MULTI-MODEL PIPELINE SUCCESS!")
            print(f"✅ Processed {total_images} images across all models")
            print(f"📈 Generated {total_upscaled} upscaled images")
            print(f"🎬 Created {total_videos} HD videos")
            print(f"📁 Built {len(model_compilations)} model compilations")
            if master_compilation:
                print(f"🏆 Master compilation: {os.path.basename(master_compilation)}")
            print(f"⏱️ Duration: {duration/60:.1f} minutes")
            print(f"💰 Total cost: ${total_cost:.3f}")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"\\n❌ COMPLETE PIPELINE FAILED: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }


async def main():
    """Run the complete multi-model multimedia pipeline"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python complete_multi_model_multimedia_pipeline.py <base_directory> [video_model]")
        print("Example: python complete_multi_model_multimedia_pipeline.py downloaded_verify_images/verify_C0xFHGOrBN7/ animate-diff")
        return
    
    base_directory = sys.argv[1]
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
        print("❌ FFmpeg not found. Please install FFmpeg.")
        return
    
    # Run complete pipeline
    pipeline = CompleteMultiModelMultimediaPipeline(replicate_token)
    result = await pipeline.complete_multi_model_pipeline(base_directory, video_model)
    
    # Save result
    report_path = os.path.join(base_directory, f'complete_multi_model_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\\n📄 Complete result saved: {report_path}")
    
    if result.get('success'):
        print(f"\\n🚀 READY FOR DEPLOYMENT!")
        print(f"🎯 Multi-model multimedia content created for @siliconsentiments_art")


if __name__ == "__main__":
    asyncio.run(main())