#!/usr/bin/env python3
"""
Analyze Extraction Pattern
Debug what images we're extracting and why we get duplicates
"""

from pymongo import MongoClient
from gridfs import GridFS

def analyze_shortcode_extraction(shortcode: str):
    """Analyze what was extracted for a specific shortcode"""
    
    client = MongoClient('mongodb://192.168.0.22:27017/')
    db = client['instagram_db']
    fs = GridFS(db)
    
    print(f"🔍 ANALYZING EXTRACTION FOR: {shortcode}")
    print("=" * 60)
    
    # Find all files for this shortcode
    files = list(fs.find({"filename": {"$regex": f".*{shortcode}.*"}}))
    
    print(f"📊 Total files found: {len(files)}")
    print("\n📋 Detailed file analysis:")
    
    for i, file_obj in enumerate(files, 1):
        print(f"\n{i}. {file_obj.filename}")
        print(f"   Size: {file_obj.length/1024:.1f} KB")
        print(f"   Upload: {file_obj.uploadDate}")
        
        # Try to get metadata if available
        metadata = getattr(file_obj, 'metadata', {})
        if metadata:
            print(f"   Metadata: {metadata}")
        
        # Try to analyze filename for patterns
        filename = file_obj.filename
        if "fbcdn.net" in filename:
            # Extract resolution info from Instagram URL
            if "/s150x150/" in filename:
                print(f"   Type: Thumbnail (150x150)")
            elif "/s320x320/" in filename:
                print(f"   Type: Small (320x320)")
            elif "/s640x640/" in filename:
                print(f"   Type: Medium (640x640)")
            elif "/s1080x1080/" in filename:
                print(f"   Type: High-res (1080x1080)")
            else:
                print(f"   Type: Unknown resolution")
    
    # Check original Instagram post for comparison
    print(f"\n🌐 Original post: https://www.instagram.com/p/{shortcode}/")
    print("\n💡 RECOMMENDATIONS:")
    print("1. Filter to only save the highest resolution version of each unique image")
    print("2. Detect carousel vs single post to know expected image count")
    print("3. Use image similarity to deduplicate different sizes of same image")

if __name__ == "__main__":
    analyze_shortcode_extraction("C0xFHGOrBN7")