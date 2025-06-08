#!/usr/bin/env python3
"""
View Extracted Images
Download images from GridFS for a specific shortcode to view locally
"""

import os
from pymongo import MongoClient
from gridfs import GridFS

def download_images_for_shortcode(shortcode: str):
    """Download all images for a specific shortcode from GridFS"""
    
    # Connect to MongoDB
    client = MongoClient('mongodb://192.168.0.22:27017/')
    db = client['instagram_db']
    fs = GridFS(db)
    
    # Create folder for images
    folder_name = f"extracted_images_{shortcode}"
    os.makedirs(folder_name, exist_ok=True)
    
    print(f"📥 Downloading images for shortcode: {shortcode}")
    print(f"📁 Saving to folder: {folder_name}/")
    print("=" * 50)
    
    # Find all files for this shortcode
    files = fs.find({"filename": {"$regex": f".*{shortcode}.*"}})
    
    downloaded_count = 0
    total_size = 0
    
    for file_obj in files:
        try:
            # Extract file extension from filename
            filename = file_obj.filename
            if "." in filename:
                ext = filename.split(".")[-1]
            else:
                ext = "jpg"  # Default extension
            
            # Create local filename
            local_filename = f"{shortcode}_{downloaded_count + 1:02d}.{ext}"
            local_path = os.path.join(folder_name, local_filename)
            
            # Download file data
            file_data = file_obj.read()
            
            # Save to local file
            with open(local_path, 'wb') as f:
                f.write(file_data)
            
            file_size = len(file_data)
            total_size += file_size
            downloaded_count += 1
            
            print(f"✅ {local_filename} ({file_size/1024:.1f} KB)")
            
        except Exception as e:
            print(f"❌ Failed to download {file_obj.filename}: {e}")
    
    print("=" * 50)
    print(f"🎊 Download complete!")
    print(f"   📸 Downloaded: {downloaded_count} images")
    print(f"   💾 Total size: {total_size/1024:.1f} KB")
    print(f"   📁 Location: {os.path.abspath(folder_name)}/")
    
    # Show file listing
    if downloaded_count > 0:
        print(f"\n📋 Files in {folder_name}/:")
        for file in sorted(os.listdir(folder_name)):
            file_path = os.path.join(folder_name, file)
            size = os.path.getsize(file_path)
            print(f"   {file} ({size/1024:.1f} KB)")

if __name__ == "__main__":
    download_images_for_shortcode("C0xLaimIm1B")