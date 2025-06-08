#!/usr/bin/env python3
"""
Organize Multimedia Directory
- Clean up and organize directory structure
- Separate generations, upscales, videos, and final compilation
- Keep only essential files for clear workflow visibility
"""

import os
import shutil
import json
from datetime import datetime
from typing import Dict, List, Any


class MultimediaDirectoryOrganizer:
    """Organize multimedia content into clean directory structure"""
    
    def __init__(self):
        self.structure = {
            "01_original": "Original Instagram images and metadata",
            "02_generations": "AI-generated variations from VLM analysis", 
            "03_upscaled": "Super-resolution upscaled images",
            "04_videos": "Individual HD videos with audio",
            "05_final": "Final compilation and deployment files",
            "archive": "Intermediate files and backups"
        }
    
    def create_organized_structure(self, base_dir: str) -> Dict[str, str]:
        """Create organized directory structure"""
        organized_dirs = {}
        
        print(f"📁 Creating organized directory structure...")
        for dir_name, description in self.structure.items():
            dir_path = os.path.join(base_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            organized_dirs[dir_name] = dir_path
            print(f"   📂 {dir_name}/ - {description}")
        
        return organized_dirs
    
    def categorize_files(self, directory: str) -> Dict[str, List[str]]:
        """Categorize files by type and importance"""
        files = {}
        all_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        
        # Original files
        files["original"] = [f for f in all_files if "_original." in f]
        
        # Generated variations (base AI generations)
        files["generations"] = [f for f in all_files if 
                              any(model in f for model in ["_recraft_v", "_flux", "_sdxl", "_kandinsky"]) and
                              "_upscaled" not in f and "_video" not in f and "_audio" not in f]
        
        # Upscaled images
        files["upscaled"] = [f for f in all_files if "_upscaled.jpg" in f]
        
        # Videos (individual and final)
        files["videos_individual"] = [f for f in all_files if 
                                    f.endswith("_hd_video.mp4") or f.endswith("_with_audio.mp4")]
        files["videos_final"] = [f for f in all_files if "compilation" in f and f.endswith(".mp4")]
        
        # Audio files
        files["audio"] = [f for f in all_files if f.endswith("_audio.mp3")]
        
        # Metadata and results
        files["metadata"] = [f for f in all_files if 
                           f.endswith(".json") and any(keyword in f for keyword in 
                           ["result", "info", "metadata", "enhanced"])]
        
        # Archive (everything else)
        files["archive"] = [f for f in all_files if f not in 
                          (files["original"] + files["generations"] + files["upscaled"] + 
                           files["videos_individual"] + files["videos_final"] + 
                           files["audio"] + files["metadata"])]
        
        return files
    
    def move_files_to_organized_structure(self, source_dir: str, organized_dirs: Dict[str, str], 
                                        categorized_files: Dict[str, List[str]]) -> Dict[str, Any]:
        """Move files to organized directory structure"""
        moved_files = {}
        
        print(f"\n📦 Organizing files...")
        
        # Move original files
        if categorized_files["original"]:
            print(f"   📸 Moving {len(categorized_files['original'])} original files...")
            moved_files["01_original"] = []
            for file in categorized_files["original"]:
                src = os.path.join(source_dir, file)
                dst = os.path.join(organized_dirs["01_original"], file)
                shutil.move(src, dst)
                moved_files["01_original"].append(file)
                print(f"      ✅ {file}")
        
        # Move generated variations
        if categorized_files["generations"]:
            print(f"   🎨 Moving {len(categorized_files['generations'])} generated variations...")
            moved_files["02_generations"] = []
            for file in categorized_files["generations"]:
                src = os.path.join(source_dir, file)
                dst = os.path.join(organized_dirs["02_generations"], file)
                shutil.move(src, dst)
                moved_files["02_generations"].append(file)
                print(f"      ✅ {file}")
        
        # Move upscaled images
        if categorized_files["upscaled"]:
            print(f"   📈 Moving {len(categorized_files['upscaled'])} upscaled images...")
            moved_files["03_upscaled"] = []
            for file in categorized_files["upscaled"]:
                src = os.path.join(source_dir, file)
                dst = os.path.join(organized_dirs["03_upscaled"], file)
                shutil.move(src, dst)
                moved_files["03_upscaled"].append(file)
                print(f"      ✅ {file}")
        
        # Move videos and audio
        video_files = categorized_files["videos_individual"] + categorized_files["audio"]
        if video_files:
            print(f"   🎬 Moving {len(video_files)} video and audio files...")
            moved_files["04_videos"] = []
            for file in video_files:
                src = os.path.join(source_dir, file)
                dst = os.path.join(organized_dirs["04_videos"], file)
                shutil.move(src, dst)
                moved_files["04_videos"].append(file)
                print(f"      ✅ {file}")
        
        # Move final compilation
        final_files = categorized_files["videos_final"] + categorized_files["metadata"]
        if final_files:
            print(f"   🚀 Moving {len(final_files)} final compilation files...")
            moved_files["05_final"] = []
            for file in final_files:
                src = os.path.join(source_dir, file)
                dst = os.path.join(organized_dirs["05_final"], file)
                shutil.move(src, dst)
                moved_files["05_final"].append(file)
                print(f"      ✅ {file}")
        
        # Move archive files
        if categorized_files["archive"]:
            print(f"   📦 Moving {len(categorized_files['archive'])} archive files...")
            moved_files["archive"] = []
            for file in categorized_files["archive"]:
                src = os.path.join(source_dir, file)
                dst = os.path.join(organized_dirs["archive"], file)
                shutil.move(src, dst)
                moved_files["archive"].append(file)
                print(f"      ✅ {file}")
        
        return moved_files
    
    def create_directory_summary(self, base_dir: str, organized_dirs: Dict[str, str], 
                               moved_files: Dict[str, Any]) -> str:
        """Create a summary of the organized directory structure"""
        summary_file = os.path.join(base_dir, "DIRECTORY_STRUCTURE.md")
        
        with open(summary_file, 'w') as f:
            f.write("# SiliconSentiments Multimedia Directory Structure\\n\\n")
            f.write(f"Organized on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            
            f.write("## Directory Overview\\n\\n")
            f.write("This directory contains the complete multimedia generation pipeline for SiliconSentiments:\\n")
            f.write("**Original Instagram Image → VLM Analysis → AI Generation → Upscaling → Video Creation → Audio Overlay → Final Compilation**\\n\\n")
            
            for dir_name, description in self.structure.items():
                dir_path = organized_dirs[dir_name]
                file_count = len(moved_files.get(dir_name, []))
                
                f.write(f"### 📂 `{dir_name}/`\\n")
                f.write(f"**Purpose**: {description}\\n")
                f.write(f"**Files**: {file_count} items\\n\\n")
                
                if dir_name in moved_files and moved_files[dir_name]:
                    f.write("**Contents**:\\n")
                    for file in sorted(moved_files[dir_name]):
                        file_path = os.path.join(dir_path, file)
                        if os.path.exists(file_path):
                            size = os.path.getsize(file_path)
                            size_mb = size / 1024 / 1024
                            if size_mb > 1:
                                f.write(f"- `{file}` ({size_mb:.1f} MB)\\n")
                            else:
                                f.write(f"- `{file}` ({size:,} bytes)\\n")
                    f.write("\\n")
            
            f.write("## Workflow Summary\\n\\n")
            f.write("1. **Original**: Source Instagram image analyzed with LLaVA-13B VLM\\n")
            f.write("2. **Generations**: 4 AI variations created with Recraft-v3\\n") 
            f.write("3. **Upscaled**: Super-resolution images (20-25MB each)\\n")
            f.write("4. **Videos**: Individual HD videos with audio overlay\\n")
            f.write("5. **Final**: Complete compilation ready for deployment\\n\\n")
            
            f.write("## Deployment Files\\n\\n")
            f.write("**Ready for @siliconsentiments_art**:\\n")
            final_files = moved_files.get("05_final", [])
            for file in final_files:
                if "compilation" in file and file.endswith(".mp4"):
                    f.write(f"- 🎬 **Main Video**: `05_final/{file}`\\n")
                elif "info.json" in file:
                    f.write(f"- 📄 **Metadata**: `05_final/{file}`\\n")
            
            f.write("\\n---\\n")
            f.write("*Generated by SiliconSentiments Multimedia Pipeline*\\n")
        
        print(f"   📄 Directory summary created: DIRECTORY_STRUCTURE.md")
        return summary_file
    
    def organize_multimedia_directory(self, directory: str) -> Dict[str, Any]:
        """Complete directory organization workflow"""
        
        print(f"🚀 MULTIMEDIA DIRECTORY ORGANIZATION")
        print(f"Directory: {directory}")
        print("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Create organized structure
            print(f"\\n1️⃣ CREATING ORGANIZED STRUCTURE...")
            organized_dirs = self.create_organized_structure(directory)
            
            # Step 2: Categorize existing files
            print(f"\\n2️⃣ CATEGORIZING FILES...")
            categorized_files = self.categorize_files(directory)
            
            total_files = sum(len(files) for files in categorized_files.values())
            print(f"   📊 Found {total_files} files to organize:")
            for category, files in categorized_files.items():
                if files:
                    print(f"      {category}: {len(files)} files")
            
            # Step 3: Move files to organized structure
            print(f"\\n3️⃣ MOVING FILES TO ORGANIZED STRUCTURE...")
            moved_files = self.move_files_to_organized_structure(
                directory, organized_dirs, categorized_files
            )
            
            # Step 4: Create directory summary
            print(f"\\n4️⃣ CREATING DIRECTORY SUMMARY...")
            summary_file = self.create_directory_summary(directory, organized_dirs, moved_files)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "directory": directory,
                "organized_structure": organized_dirs,
                "moved_files": moved_files,
                "summary_file": summary_file,
                "total_files_organized": total_files,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\\n🎉 DIRECTORY ORGANIZATION COMPLETE!")
            print(f"✅ Organized {total_files} files into structured directories")
            print(f"📂 Clean workflow structure created")
            print(f"📄 Summary: DIRECTORY_STRUCTURE.md")
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
    """Run the directory organization"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python organize_multimedia_directory.py <directory>")
        print("Example: python organize_multimedia_directory.py downloaded_verify_images/verify_C0xFHGOrBN7/")
        return
    
    directory = sys.argv[1]
    
    if not os.path.exists(directory):
        print(f"❌ Directory not found: {directory}")
        return
    
    # Run organization
    organizer = MultimediaDirectoryOrganizer()
    result = organizer.organize_multimedia_directory(directory)
    
    # Save result
    if result.get("success"):
        result_filename = f"organization_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_path = os.path.join(directory, result_filename)
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\\n📄 Organization result saved: {result_filename}")
        print(f"\\n📂 ORGANIZED DIRECTORY STRUCTURE:")
        print(f"📍 {directory}")
        print("   📂 01_original/ - Original Instagram images")
        print("   📂 02_generations/ - AI-generated variations")  
        print("   📂 03_upscaled/ - Super-resolution images")
        print("   📂 04_videos/ - Individual videos with audio")
        print("   📂 05_final/ - Final compilation for deployment")
        print("   📂 archive/ - Intermediate files")


if __name__ == "__main__":
    main()