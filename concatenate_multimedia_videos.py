#!/usr/bin/env python3
"""
Concatenate Multimedia Videos
- Combine all individual videos with audio into one compilation
- Create final single video for deployment
- Complete the multimedia workflow
"""

import os
import subprocess
import json
from datetime import datetime
from typing import List, Dict, Any


class MultimediaVideoConcatenator:
    """Concatenate multiple videos with audio into final compilation"""
    
    def __init__(self):
        pass
    
    def find_videos_with_audio(self, directory: str) -> List[str]:
        """Find all videos with audio in directory"""
        video_files = []
        for file in os.listdir(directory):
            if file.endswith("_with_audio.mp4"):
                video_files.append(os.path.join(directory, file))
        
        # Sort to ensure consistent order
        video_files.sort()
        
        print(f"🎬 Found {len(video_files)} videos with audio:")
        for video in video_files:
            size = os.path.getsize(video)
            print(f"   📹 {os.path.basename(video)} ({size:,} bytes)")
        
        return video_files
    
    def get_video_duration(self, video_path: str) -> float:
        """Get duration of video using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                print(f"   ⚠️ Could not get duration for {os.path.basename(video_path)}, assuming 6 seconds")
                return 6.0
        except Exception as e:
            print(f"   ⚠️ Error getting duration: {e}, assuming 6 seconds")
            return 6.0
    
    def create_concat_file(self, video_files: List[str], output_dir: str) -> str:
        """Create FFmpeg concat file listing all videos"""
        concat_file = os.path.join(output_dir, "concat_list.txt")
        
        print(f"\n📝 Creating concatenation file...")
        with open(concat_file, 'w') as f:
            for video_file in video_files:
                # Use absolute paths to ensure ffmpeg can find files
                abs_path = os.path.abspath(video_file)
                f.write(f"file '{abs_path}'\n")
                
                duration = self.get_video_duration(video_file)
                print(f"   📹 {os.path.basename(video_file)} ({duration:.1f}s)")
        
        print(f"   ✅ Concat file created: {concat_file}")
        return concat_file
    
    def concatenate_videos(self, video_files: List[str], output_dir: str, 
                          output_filename: str = None) -> Dict[str, Any]:
        """Concatenate all videos into one final compilation"""
        
        if not video_files:
            return {"success": False, "error": "No videos to concatenate"}
        
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"SiliconSentiments_multimedia_compilation_{timestamp}.mp4"
        
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"\\n🎬 CONCATENATING VIDEOS")
        print(f"Input: {len(video_files)} videos")
        print(f"Output: {output_filename}")
        print("=" * 60)
        
        try:
            # Step 1: Create concat file
            concat_file = self.create_concat_file(video_files, output_dir)
            
            # Step 2: Use FFmpeg to concatenate
            print(f"\\n🔗 Concatenating videos...")
            cmd = [
                'ffmpeg', '-y',  # -y to overwrite existing files
                '-f', 'concat',  # Use concat demuxer
                '-safe', '0',    # Allow unsafe file names
                '-i', concat_file,  # Input concat file
                '-c', 'copy',    # Copy streams without re-encoding
                output_path
            ]
            
            # Run ffmpeg with absolute paths
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                # Clean up concat file
                os.remove(concat_file)
                
                size = os.path.getsize(output_path)
                total_duration = sum(self.get_video_duration(v) for v in video_files)
                
                print(f"   ✅ Concatenation complete!")
                print(f"   📹 Final video: {output_filename}")
                print(f"   📏 Duration: {total_duration:.1f} seconds")
                print(f"   💾 Size: {size:,} bytes ({size/1024/1024:.1f} MB)")
                
                return {
                    "success": True,
                    "output_path": output_path,
                    "output_filename": output_filename,
                    "total_duration": total_duration,
                    "file_size_bytes": size,
                    "input_videos": len(video_files),
                    "individual_videos": [os.path.basename(v) for v in video_files]
                }
            else:
                print(f"   ❌ FFmpeg concatenation failed:")
                print(f"   Error: {result.stderr}")
                return {
                    "success": False,
                    "error": f"FFmpeg failed: {result.stderr}",
                    "ffmpeg_returncode": result.returncode
                }
                
        except Exception as e:
            print(f"   ❌ Concatenation error: {e}")
            return {"success": False, "error": str(e)}
    
    def create_video_preview_info(self, result: Dict[str, Any], output_dir: str) -> str:
        """Create a summary file with video information"""
        if not result.get("success"):
            return None
        
        info_filename = result["output_filename"].replace(".mp4", "_info.json")
        info_path = os.path.join(output_dir, info_filename)
        
        video_info = {
            "final_compilation": {
                "filename": result["output_filename"],
                "duration_seconds": result["total_duration"],
                "file_size_bytes": result["file_size_bytes"],
                "file_size_mb": round(result["file_size_bytes"] / 1024 / 1024, 2),
                "input_videos_count": result["input_videos"],
                "creation_timestamp": datetime.now().isoformat()
            },
            "source_videos": result["individual_videos"],
            "workflow_summary": {
                "pipeline": "Upscaled Images → HD Videos → Audio Overlay → Final Compilation",
                "brand": "SiliconSentiments",
                "ready_for_deployment": True,
                "instagram_compatible": True,
                "quality": "Professional HD with ambient audio"
            }
        }
        
        with open(info_path, 'w') as f:
            json.dump(video_info, f, indent=2)
        
        print(f"   📄 Video info saved: {info_filename}")
        return info_path
    
    def complete_concatenation_workflow(self, directory: str, 
                                      output_filename: str = None) -> Dict[str, Any]:
        """Complete workflow: find videos → concatenate → create summary"""
        
        print(f"🚀 COMPLETE VIDEO CONCATENATION WORKFLOW")
        print(f"Directory: {directory}")
        print("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Find all videos with audio
            print(f"\\n1️⃣ SCANNING FOR VIDEOS WITH AUDIO...")
            video_files = self.find_videos_with_audio(directory)
            
            if not video_files:
                return {"success": False, "error": "No videos with audio found"}
            
            # Step 2: Concatenate videos
            print(f"\\n2️⃣ CONCATENATING {len(video_files)} VIDEOS...")
            concat_result = self.concatenate_videos(video_files, directory, output_filename)
            
            if not concat_result.get("success"):
                return concat_result
            
            # Step 3: Create summary info
            print(f"\\n3️⃣ CREATING VIDEO SUMMARY...")
            info_path = self.create_video_preview_info(concat_result, directory)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            final_result = {
                **concat_result,
                "info_file": info_path,
                "workflow_duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\\n🎉 VIDEO CONCATENATION COMPLETE!")
            print(f"✅ Final compilation: {concat_result['output_filename']}")
            print(f"⏱️ Total duration: {concat_result['total_duration']:.1f} seconds")
            print(f"💾 File size: {concat_result['file_size_bytes']/1024/1024:.1f} MB")
            print(f"🚀 Ready for @siliconsentiments_art deployment!")
            
            return final_result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"\\n❌ CONCATENATION WORKFLOW FAILED: {e}")
            return {
                "success": False,
                "error": str(e),
                "workflow_duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }


def main():
    """Run the video concatenation workflow"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python concatenate_multimedia_videos.py <directory> [output_filename]")
        print("Example: python concatenate_multimedia_videos.py downloaded_verify_images/verify_C0xFHGOrBN7/")
        print("Example: python concatenate_multimedia_videos.py downloaded_verify_images/verify_C0xFHGOrBN7/ SiliconSentiments_C0xFHGOrBN7_compilation.mp4")
        return
    
    directory = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found. Please install FFmpeg.")
        return
    
    # Run concatenation workflow
    concatenator = MultimediaVideoConcatenator()
    result = concatenator.complete_concatenation_workflow(directory, output_filename)
    
    # Save result
    if result.get("success"):
        result_filename = f"concatenation_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_path = os.path.join(directory, result_filename)
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\\n📄 Result saved: {result_filename}")
        print(f"\\n🎬 FINAL VIDEO LOCATION:")
        print(f"📍 {result['output_path']}")


if __name__ == "__main__":
    main()