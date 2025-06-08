#!/usr/bin/env python3
"""
Reorganize Multi-Model Content by Model Type
- Group upscaled images by model in separate folders
- Create single combined video for each model with audio
- Clean structure: each model gets its own directory with upscaled images and final video
"""

import os
import shutil
import subprocess
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional


class ModelGroupingOrganizer:
    """Reorganize content by AI model with combined videos and audio"""
    
    def __init__(self):
        self.model_categories = {
            "recraft": "Recraft v3 - Professional design model",
            "flux": "Flux 1.1 Pro - Advanced AI generation", 
            "sdxl": "Stable Diffusion XL - High-resolution generation",
            "kandinsky": "Kandinsky - Artistic AI model"
        }
    
    def create_model_directories(self, base_dir: str) -> Dict[str, str]:
        """Create clean model-specific directories"""
        model_dirs = {}
        
        print(f"📁 Creating model-specific directories...")
        for model, description in self.model_categories.items():
            model_dir = os.path.join(base_dir, f"{model}_model")
            upscaled_dir = os.path.join(model_dir, "upscaled_images")
            videos_dir = os.path.join(model_dir, "videos")
            
            os.makedirs(upscaled_dir, exist_ok=True)
            os.makedirs(videos_dir, exist_ok=True)
            
            model_dirs[model] = {
                "base": model_dir,
                "upscaled": upscaled_dir,
                "videos": videos_dir,
                "description": description
            }
            
            print(f"   📂 {model}_model/ - {description}")
        
        return model_dirs
    
    def move_upscaled_images_by_model(self, source_dir: str, model_dirs: Dict[str, Dict]) -> Dict[str, List[str]]:
        """Move upscaled images to model-specific directories"""
        moved_files = {model: [] for model in self.model_categories.keys()}
        
        print(f"\n📦 Moving upscaled images by model...")
        
        for model in self.model_categories.keys():
            source_upscaled_dir = os.path.join(source_dir, f"model_{model}", "upscaled")
            
            if os.path.exists(source_upscaled_dir):
                target_upscaled_dir = model_dirs[model]["upscaled"]
                
                for file in os.listdir(source_upscaled_dir):
                    if file.endswith("_upscaled.jpg"):
                        src_path = os.path.join(source_upscaled_dir, file)
                        dst_path = os.path.join(target_upscaled_dir, file)
                        
                        shutil.copy2(src_path, dst_path)  # Copy instead of move to preserve original
                        moved_files[model].append(file)
                        
                        size = os.path.getsize(dst_path)
                        print(f"   ✅ {model.upper()}: {file} ({size/1024/1024:.1f}MB)")
        
        return moved_files
    
    def find_best_audio_file(self, base_dir: str) -> Optional[str]:
        """Find the best audio file from previous generations"""
        audio_candidates = []
        
        # Check multiple possible locations
        audio_dirs = [
            os.path.join(base_dir, "04_videos"),
            os.path.join(base_dir, "multi_model_multimedia"),
            base_dir
        ]
        
        for audio_dir in audio_dirs:
            if os.path.exists(audio_dir):
                for root, dirs, files in os.walk(audio_dir):
                    for file in files:
                        if file.endswith("_audio.mp3"):
                            audio_path = os.path.join(root, file)
                            size = os.path.getsize(audio_path)
                            audio_candidates.append((audio_path, size))
        
        if audio_candidates:
            # Select the largest (best quality) audio file
            best_audio = max(audio_candidates, key=lambda x: x[1])
            print(f"🎵 Selected audio: {os.path.basename(best_audio[0])} ({best_audio[1]:,} bytes)")
            return best_audio[0]
        
        print(f"⚠️ No audio file found")
        return None
    
    def create_model_compilation_with_audio(self, model: str, model_dirs: Dict, 
                                          audio_file: Optional[str]) -> Optional[str]:
        """Create a single compilation video for a model with audio overlay"""
        
        videos_source_dir = os.path.join("multi_model_multimedia", f"model_{model}", "videos")
        
        if not os.path.exists(videos_source_dir):
            print(f"   ⚠️ {model.upper()}: No videos directory found")
            return None
        
        # Find all videos for this model
        video_files = []
        for file in os.listdir(videos_source_dir):
            if file.endswith("_hd_video.mp4"):
                video_files.append(os.path.join(videos_source_dir, file))
        
        if len(video_files) < 2:
            print(f"   ⚠️ {model.upper()}: Not enough videos for compilation ({len(video_files)} found)")
            return None
        
        video_files.sort()  # Ensure consistent order
        
        print(f"\n🎬 Creating {model.upper()} compilation from {len(video_files)} videos...")
        
        # Create concat file with proper format
        concat_file = os.path.join(model_dirs[model]["videos"], f"{model}_concat.txt")
        with open(concat_file, 'w') as f:
            for video_file in video_files:
                abs_path = os.path.abspath(video_file)
                f.write(f"file '{abs_path}'\\n")
        
        # Create compilation video (no audio first)
        temp_compilation = os.path.join(model_dirs[model]["videos"], f"{model}_temp_compilation.mp4")
        
        try:
            # Step 1: Concatenate videos
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                temp_compilation
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"   ❌ {model.upper()}: Video concatenation failed: {result.stderr}")
                return None
            
            # Step 2: Add audio if available
            final_filename = f"SiliconSentiments_{model}_compilation_with_audio.mp4"
            final_path = os.path.join(model_dirs[model]["videos"], final_filename)
            
            if audio_file and os.path.exists(audio_file):
                print(f"   🎵 Adding audio to {model.upper()} compilation...")
                
                cmd = [
                    'ffmpeg', '-y',
                    '-i', temp_compilation,  # Video input
                    '-i', audio_file,        # Audio input
                    '-c:v', 'copy',          # Copy video codec
                    '-c:a', 'aac',           # Audio codec
                    '-shortest',             # End when shortest stream ends
                    '-map', '0:v:0',         # Map video from first input
                    '-map', '1:a:0',         # Map audio from second input
                    final_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    os.remove(temp_compilation)  # Clean up temp file
                    os.remove(concat_file)       # Clean up concat file
                else:
                    print(f"   ⚠️ {model.upper()}: Audio overlay failed, using video-only compilation")
                    shutil.move(temp_compilation, final_path)
                    os.remove(concat_file)
            else:
                print(f"   📹 {model.upper()}: No audio available, creating video-only compilation")
                shutil.move(temp_compilation, final_path)
                os.remove(concat_file)
            
            if os.path.exists(final_path):
                size = os.path.getsize(final_path)
                duration = len(video_files) * 2.1  # Approximate duration
                
                print(f"   ✅ {model.upper()}: Compilation created!")
                print(f"      📹 {final_filename}")
                print(f"      📏 Duration: {duration:.1f}s | Size: {size/1024/1024:.1f}MB")
                print(f"      🎬 Videos: {len(video_files)} combined")
                
                return final_path
            
        except Exception as e:
            print(f"   ❌ {model.upper()}: Compilation error: {e}")
            
        return None
    
    def create_model_summary(self, model_dirs: Dict, moved_files: Dict, 
                           compilations: Dict, base_dir: str) -> str:
        """Create a summary of the model organization"""
        
        summary_file = os.path.join(base_dir, "MODEL_ORGANIZATION_SUMMARY.md")
        
        with open(summary_file, 'w') as f:
            f.write("# SiliconSentiments Multi-Model Organization\\n\\n")
            f.write(f"Organized on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            
            f.write("## Model-Specific Content Structure\\n\\n")
            f.write("Complete multimedia content organized by AI generation model:\\n\\n")
            
            for model, description in self.model_categories.items():
                upscaled_count = len(moved_files.get(model, []))
                compilation_file = compilations.get(model)
                
                f.write(f"### 📂 `{model}_model/`\\n")
                f.write(f"**Model**: {description}\\n")
                f.write(f"**Upscaled Images**: {upscaled_count} high-resolution files\\n")
                
                if compilation_file:
                    filename = os.path.basename(compilation_file)
                    size = os.path.getsize(compilation_file) / 1024 / 1024
                    f.write(f"**Final Video**: `{filename}` ({size:.1f}MB)\\n")
                else:
                    f.write(f"**Final Video**: Not created\\n")
                
                f.write("\\n**Directory Structure**:\\n")
                f.write(f"```\\n")
                f.write(f"{model}_model/\\n")
                f.write(f"├── upscaled_images/     # Super-resolution images (20-27MB each)\\n")
                f.write(f"└── videos/              # Final compilation with audio\\n")
                f.write(f"```\\n\\n")
                
                if moved_files.get(model):
                    f.write("**Upscaled Images**:\\n")
                    for file in sorted(moved_files[model]):
                        f.write(f"- `{file}`\\n")
                    f.write("\\n")
            
            f.write("## Deployment-Ready Content\\n\\n")
            f.write("Each model directory contains:\\n")
            f.write("1. **High-resolution upscaled images** - Perfect for print/display\\n")
            f.write("2. **Complete video compilation** - Ready for social media\\n")
            f.write("3. **Professional audio overlay** - Ambient SiliconSentiments soundtrack\\n\\n")
            
            f.write("## Model Comparison\\n\\n")
            f.write("| Model | Images | Video | Description |\\n")
            f.write("|-------|--------|-------|-------------|\\n")
            
            for model, description in self.model_categories.items():
                upscaled_count = len(moved_files.get(model, []))
                has_video = "✅" if compilations.get(model) else "❌"
                f.write(f"| {model.upper()} | {upscaled_count} | {has_video} | {description} |\\n")
            
            f.write("\\n---\\n")
            f.write("*Generated by SiliconSentiments Multi-Model Pipeline*\\n")
        
        print(f"\\n📄 Model summary created: MODEL_ORGANIZATION_SUMMARY.md")
        return summary_file
    
    def organize_by_model_with_audio(self, base_directory: str) -> Dict[str, Any]:
        """Complete reorganization by model with audio compilations"""
        
        print(f"🚀 MODEL-BASED ORGANIZATION WITH AUDIO")
        print(f"Base Directory: {base_directory}")
        print("=" * 80)
        
        start_time = datetime.now()
        
        try:
            source_multimedia_dir = os.path.join(base_directory, "multi_model_multimedia")
            
            if not os.path.exists(source_multimedia_dir):
                return {"success": False, "error": "Multi-model multimedia directory not found"}
            
            # Step 1: Create model directories
            print(f"\\n1️⃣ CREATING MODEL DIRECTORIES...")
            model_dirs = self.create_model_directories(base_directory)
            
            # Step 2: Move upscaled images by model
            print(f"\\n2️⃣ ORGANIZING UPSCALED IMAGES BY MODEL...")
            moved_files = self.move_upscaled_images_by_model(source_multimedia_dir, model_dirs)
            
            total_moved = sum(len(files) for files in moved_files.values())
            print(f"\\n   📊 Moved {total_moved} upscaled images across {len(model_dirs)} models")
            
            # Step 3: Find best audio file
            print(f"\\n3️⃣ FINDING AUDIO FILE...")
            audio_file = self.find_best_audio_file(base_directory)
            
            # Step 4: Create model compilations with audio
            print(f"\\n4️⃣ CREATING MODEL COMPILATIONS WITH AUDIO...")
            compilations = {}
            
            for model in self.model_categories.keys():
                if moved_files[model]:  # Only process models with images
                    compilation_path = self.create_model_compilation_with_audio(
                        model, model_dirs, audio_file
                    )
                    if compilation_path:
                        compilations[model] = compilation_path
            
            # Step 5: Create summary
            print(f"\\n5️⃣ CREATING ORGANIZATION SUMMARY...")
            summary_file = self.create_model_summary(model_dirs, moved_files, compilations, base_directory)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "base_directory": base_directory,
                "model_directories": model_dirs,
                "moved_files": moved_files,
                "compilations": compilations,
                "audio_file": audio_file,
                "summary_file": summary_file,
                "total_images_organized": total_moved,
                "total_compilations_created": len(compilations),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\\n🎉 MODEL ORGANIZATION COMPLETE!")
            print(f"✅ Organized {total_moved} upscaled images by model")
            print(f"🎬 Created {len(compilations)} video compilations with audio")
            print(f"📂 Model directories: {', '.join([f'{m}_model' for m in self.model_categories.keys()])}")
            print(f"⏱️ Duration: {duration:.1f}s")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"\\n❌ ORGANIZATION FAILED: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }


def main():
    """Run the model-based organization with audio"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python reorganize_by_model_with_audio.py <base_directory>")
        print("Example: python reorganize_by_model_with_audio.py downloaded_verify_images/verify_C0xFHGOrBN7/")
        return
    
    base_directory = sys.argv[1]
    
    if not os.path.exists(base_directory):
        print(f"❌ Directory not found: {base_directory}")
        return
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found. Please install FFmpeg.")
        return
    
    # Run organization
    organizer = ModelGroupingOrganizer()
    result = organizer.organize_by_model_with_audio(base_directory)
    
    # Save result
    if result.get("success"):
        result_filename = f"model_organization_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_path = os.path.join(base_directory, result_filename)
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\\n📄 Organization result saved: {result_filename}")
        print(f"\\n🏆 FINAL MODEL ORGANIZATION:")
        print(f"📍 {base_directory}")
        for model in ["recraft", "flux", "sdxl", "kandinsky"]:
            model_dir = f"{model}_model"
            if os.path.exists(os.path.join(base_directory, model_dir)):
                print(f"   📂 {model_dir}/ - Upscaled images + final compilation video")


if __name__ == "__main__":
    main()