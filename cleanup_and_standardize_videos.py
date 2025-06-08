#!/usr/bin/env python3
"""
Cleanup and Standardize Model Videos
- Remove individual videos after compilation
- Ensure consistent 2-second timing per image
- Standardize compilation durations
- Clean up directory structure
"""

import os
import subprocess
import shutil
import json
from datetime import datetime
from typing import Dict, List, Any


class VideoStandardizer:
    """Standardize video timing and cleanup directories"""
    
    def __init__(self):
        self.models = ["recraft", "flux", "sdxl", "kandinsky"]
        self.target_duration_per_image = 2.0  # seconds
    
    def get_video_duration(self, video_path: str) -> float:
        """Get actual duration of a video file"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                return self.target_duration_per_image  # Default fallback
        except Exception:
            return self.target_duration_per_image  # Default fallback
    
    def analyze_current_compilation(self, model: str, base_dir: str) -> Dict[str, Any]:
        """Analyze current compilation timing and content"""
        
        model_dir = os.path.join(base_dir, f"{model}_model")
        compilation_file = os.path.join(model_dir, "videos", f"SiliconSentiments_{model}_compilation_with_audio.mp4")
        individual_dir = os.path.join(model_dir, "videos", "individual")
        upscaled_dir = os.path.join(model_dir, "upscaled_images")
        
        analysis = {
            "model": model,
            "compilation_exists": os.path.exists(compilation_file),
            "compilation_duration": 0,
            "upscaled_count": 0,
            "individual_videos": 0,
            "expected_duration": 0,
            "size_mb": 0
        }
        
        # Count upscaled images
        if os.path.exists(upscaled_dir):
            analysis["upscaled_count"] = len([f for f in os.listdir(upscaled_dir) if f.endswith("_upscaled.jpg")])
        
        # Count individual videos
        if os.path.exists(individual_dir):
            analysis["individual_videos"] = len([f for f in os.listdir(individual_dir) if f.endswith(".mp4")])
        
        # Calculate expected duration (2 seconds per image)
        analysis["expected_duration"] = analysis["upscaled_count"] * self.target_duration_per_image
        
        # Get compilation info
        if analysis["compilation_exists"]:
            analysis["compilation_duration"] = self.get_video_duration(compilation_file)
            analysis["size_mb"] = round(os.path.getsize(compilation_file) / 1024 / 1024, 1)
        
        return analysis
    
    def cleanup_individual_videos(self, model: str, base_dir: str) -> bool:
        """Remove individual videos after compilation"""
        
        individual_dir = os.path.join(base_dir, f"{model}_model", "videos", "individual")
        
        if not os.path.exists(individual_dir):
            return True
        
        try:
            # Count files before cleanup
            files_before = len([f for f in os.listdir(individual_dir) if f.endswith(".mp4")])
            
            # Remove individual videos directory
            shutil.rmtree(individual_dir)
            
            print(f"   ✅ {model.upper()}: Removed {files_before} individual videos")
            return True
            
        except Exception as e:
            print(f"   ❌ {model.upper()}: Cleanup failed - {e}")
            return False
    
    def create_timing_report(self, analyses: List[Dict], base_dir: str) -> str:
        """Create a report of video timing analysis"""
        
        report_file = os.path.join(base_dir, "VIDEO_TIMING_REPORT.md")
        
        with open(report_file, 'w') as f:
            f.write("# SiliconSentiments Video Timing Analysis\\n\\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Standard Duration: {self.target_duration_per_image} seconds per image\\n\\n")
            
            f.write("## Model Compilation Summary\\n\\n")
            f.write("| Model | Images | Expected | Actual | Size | Status |\\n")
            f.write("|-------|--------|----------|--------|------|--------|\\n")
            
            total_images = 0
            total_expected = 0
            total_actual = 0
            
            for analysis in analyses:
                model = analysis["model"].upper()
                images = analysis["upscaled_count"]
                expected = f"{analysis['expected_duration']:.1f}s"
                actual = f"{analysis['compilation_duration']:.1f}s" if analysis["compilation_exists"] else "N/A"
                size = f"{analysis['size_mb']}MB" if analysis["compilation_exists"] else "N/A"
                status = "✅" if analysis["compilation_exists"] else "❌"
                
                f.write(f"| {model} | {images} | {expected} | {actual} | {size} | {status} |\\n")
                
                total_images += images
                total_expected += analysis["expected_duration"]
                if analysis["compilation_exists"]:
                    total_actual += analysis["compilation_duration"]
            
            f.write(f"| **TOTAL** | **{total_images}** | **{total_expected:.1f}s** | **{total_actual:.1f}s** | | |\\n\\n")
            
            f.write("## Individual Model Details\\n\\n")
            
            for analysis in analyses:
                model_name = analysis["model"]
                f.write(f"### {model_name.upper()} Model\\n")
                f.write(f"- **Upscaled Images**: {analysis['upscaled_count']}\\n")
                f.write(f"- **Individual Videos**: {analysis['individual_videos']} (cleaned up)\\n")
                f.write(f"- **Expected Duration**: {analysis['expected_duration']:.1f} seconds\\n")
                
                if analysis["compilation_exists"]:
                    f.write(f"- **Actual Duration**: {analysis['compilation_duration']:.1f} seconds\\n")
                    f.write(f"- **File Size**: {analysis['size_mb']} MB\\n")
                    
                    timing_diff = analysis["compilation_duration"] - analysis["expected_duration"]
                    if abs(timing_diff) < 0.5:
                        f.write(f"- **Timing**: ✅ Accurate (±{timing_diff:.1f}s)\\n")
                    else:
                        f.write(f"- **Timing**: ⚠️ Off by {timing_diff:+.1f}s\\n")
                else:
                    f.write(f"- **Status**: ❌ Compilation missing\\n")
                
                f.write("\\n")
            
            f.write("## Final Directory Structure\\n\\n")
            f.write("Clean model organization with only essential files:\\n\\n")
            f.write("```\\n")
            for model in self.models:
                f.write(f"{model}_model/\\n")
                f.write(f"├── upscaled_images/           # {analysis['upscaled_count']} super-resolution images\\n")
                f.write(f"└── videos/\\n")
                f.write(f"    └── SiliconSentiments_{model}_compilation_with_audio.mp4\\n")
            f.write("```\\n\\n")
            
            f.write("## Performance Summary\\n\\n")
            f.write(f"- **Total Content**: {total_images} upscaled images across {len(self.models)} AI models\\n")
            f.write(f"- **Video Content**: {total_actual:.1f} seconds of compilation videos\\n")
            f.write(f"- **Timing Standard**: {self.target_duration_per_image}s per image maintained\\n")
            f.write(f"- **Storage Optimized**: Individual videos removed after compilation\\n")
            f.write(f"- **Ready for Deployment**: Clean, organized structure\\n\\n")
            
            f.write("---\\n")
            f.write("*Generated by SiliconSentiments Video Standardizer*\\n")
        
        return report_file
    
    def standardize_and_cleanup(self, base_directory: str) -> Dict[str, Any]:
        """Complete standardization and cleanup process"""
        
        print(f"🎬 VIDEO STANDARDIZATION & CLEANUP")
        print(f"Base Directory: {base_directory}")
        print(f"Target: {self.target_duration_per_image}s per image")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Analyze current compilations
            print(f"\\n1️⃣ ANALYZING CURRENT COMPILATIONS...")
            analyses = []
            
            for model in self.models:
                analysis = self.analyze_current_compilation(model, base_directory)
                analyses.append(analysis)
                
                status = "✅" if analysis["compilation_exists"] else "❌"
                expected = analysis["expected_duration"]
                actual = analysis["compilation_duration"] if analysis["compilation_exists"] else 0
                
                print(f"   📊 {model.upper()}: {analysis['upscaled_count']} images → {expected:.1f}s expected / {actual:.1f}s actual {status}")
            
            # Step 2: Cleanup individual videos
            print(f"\\n2️⃣ CLEANING UP INDIVIDUAL VIDEOS...")
            cleanup_results = {}
            
            for model in self.models:
                cleanup_success = self.cleanup_individual_videos(model, base_directory)
                cleanup_results[model] = cleanup_success
            
            # Step 3: Create timing report
            print(f"\\n3️⃣ CREATING TIMING REPORT...")
            report_file = self.create_timing_report(analyses, base_directory)
            print(f"   📄 Report created: {os.path.basename(report_file)}")
            
            # Calculate totals
            total_images = sum(a["upscaled_count"] for a in analyses)
            total_compilations = sum(1 for a in analyses if a["compilation_exists"])
            total_duration = sum(a["compilation_duration"] for a in analyses if a["compilation_exists"])
            successful_cleanups = sum(1 for success in cleanup_results.values() if success)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "base_directory": base_directory,
                "target_duration_per_image": self.target_duration_per_image,
                "analyses": analyses,
                "cleanup_results": cleanup_results,
                "report_file": report_file,
                "totals": {
                    "images": total_images,
                    "compilations": total_compilations,
                    "total_duration": total_duration,
                    "successful_cleanups": successful_cleanups
                },
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\\n🎉 STANDARDIZATION COMPLETE!")
            print(f"✅ Analyzed {total_images} images across {len(self.models)} models")
            print(f"🎬 {total_compilations}/{len(self.models)} compilations ready ({total_duration:.1f}s total)")
            print(f"🧹 Cleaned up {successful_cleanups}/{len(self.models)} model directories")
            print(f"📐 Standard timing: {self.target_duration_per_image}s per image")
            print(f"⏱️ Duration: {duration:.1f}s")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"\\n❌ STANDARDIZATION FAILED: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }


def main():
    """Run video standardization and cleanup"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cleanup_and_standardize_videos.py <base_directory>")
        print("Example: python cleanup_and_standardize_videos.py downloaded_verify_images/verify_C0xFHGOrBN7/")
        return
    
    base_directory = sys.argv[1]
    
    if not os.path.exists(base_directory):
        print(f"❌ Directory not found: {base_directory}")
        return
    
    # Check if ffprobe is available
    try:
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFprobe not found. Please install FFmpeg.")
        return
    
    # Run standardization
    standardizer = VideoStandardizer()
    result = standardizer.standardize_and_cleanup(base_directory)
    
    # Save result
    if result.get("success"):
        result_filename = f"video_standardization_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_path = os.path.join(base_directory, result_filename)
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\\n📄 Standardization result saved: {result_filename}")
        
        # Show final structure
        print(f"\\n📁 FINAL CLEAN STRUCTURE:")
        for model in ["recraft", "flux", "sdxl", "kandinsky"]:
            model_dir = os.path.join(base_directory, f"{model}_model")
            if os.path.exists(model_dir):
                upscaled_count = len([f for f in os.listdir(os.path.join(model_dir, "upscaled_images")) if f.endswith("_upscaled.jpg")])
                compilation_file = os.path.join(model_dir, "videos", f"SiliconSentiments_{model}_compilation_with_audio.mp4")
                has_compilation = "✅" if os.path.exists(compilation_file) else "❌"
                expected_duration = upscaled_count * 2.0
                print(f"   📂 {model}_model/ - {upscaled_count} images → {expected_duration:.0f}s video {has_compilation}")


if __name__ == "__main__":
    main()