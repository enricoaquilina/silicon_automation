#!/usr/bin/env python3
"""
View an original Instagram image from GridFS
Download and display one of the production extracted images
"""

from pymongo import MongoClient
from gridfs import GridFS
import os
from PIL import Image
import io

def view_gridfs_original():
    # Connect to MongoDB
    try:
        client = MongoClient('mongodb://192.168.0.22:27017/')
        client.admin.command('ping')
        db = client['instagram_db']
        fs = GridFS(db)
        print('✅ Connected to Pi MongoDB (instagram_db)')
    except Exception as e:
        print(f'❌ MongoDB connection failed: {e}')
        return

    print(f'\n🔍 FINDING ORIGINAL INSTAGRAM IMAGES IN GRIDFS')
    print(f'==============================================')

    # Find original Instagram images
    original_files = list(fs.find({"filename": {"$regex": "instagram_production_"}}).limit(5))
    
    if not original_files:
        print(f'❌ No original Instagram images found')
        return
    
    print(f'Found {len(original_files)} original images. Showing first 5:')
    
    for i, grid_file in enumerate(original_files, 1):
        filename = grid_file.filename
        file_id = grid_file._id
        size = grid_file.length
        upload_date = grid_file.upload_date
        
        # Extract shortcode from filename
        # Format: instagram_production_C0xFHGOrBN7_3.jpg
        parts = filename.split('_')
        if len(parts) >= 3:
            shortcode = parts[2]
            img_index = parts[3].split('.')[0] if len(parts) > 3 else '?'
        else:
            shortcode = 'unknown'
            img_index = '?'
        
        print(f'\n{i}. 📸 {filename}')
        print(f'   Shortcode: {shortcode}')
        print(f'   Image index: {img_index}')
        print(f'   File ID: {file_id}')
        print(f'   Size: {size:,} bytes')
        print(f'   Uploaded: {upload_date}')
        print(f'   Instagram URL: https://instagram.com/p/{shortcode}/')
    
    # Ask user which one to download and view
    print(f'\n📥 DOWNLOADING SAMPLE IMAGE FOR VIEWING')
    print(f'=====================================')
    
    # Download the first one as an example
    sample_file = original_files[0]
    filename = sample_file.filename
    
    print(f'Downloading: {filename}')
    
    try:
        # Create output directory
        output_dir = 'sample_gridfs_originals'
        os.makedirs(output_dir, exist_ok=True)
        
        # Download file data
        file_data = sample_file.read()
        
        # Save to local file
        local_path = os.path.join(output_dir, filename)
        with open(local_path, 'wb') as f:
            f.write(file_data)
        
        print(f'✅ Downloaded to: {local_path}')
        print(f'📏 File size: {len(file_data):,} bytes')
        
        # Try to open and get image info
        try:
            with Image.open(io.BytesIO(file_data)) as img:
                width, height = img.size
                format_type = img.format
                mode = img.mode
                
                print(f'🖼️  Image details:')
                print(f'   Dimensions: {width}x{height}')
                print(f'   Format: {format_type}')
                print(f'   Mode: {mode}')
                
                # Show file location for viewing
                abs_path = os.path.abspath(local_path)
                print(f'\n👀 VIEW THE IMAGE:')
                print(f'   File path: {abs_path}')
                print(f'   Command: open "{abs_path}"  # On macOS')
                print(f'   Or use any image viewer to open: {local_path}')
                
        except Exception as e:
            print(f'⚠️  Could not read image details: {e}')
        
        # Get metadata if available
        metadata = getattr(sample_file, 'metadata', {}) or {}
        if metadata:
            print(f'\n📋 METADATA:')
            for key, value in metadata.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f'   {key}: {value[:100]}...')
                else:
                    print(f'   {key}: {value}')
        
        # Extract shortcode for Instagram comparison
        parts = filename.split('_')
        if len(parts) >= 3:
            shortcode = parts[2]
            print(f'\n🔗 COMPARE WITH ORIGINAL:')
            print(f'   Instagram post: https://instagram.com/p/{shortcode}/')
            print(f'   This extracted image should match one of the carousel images')
        
    except Exception as e:
        print(f'❌ Download failed: {e}')

    client.close()

if __name__ == "__main__":
    view_gridfs_original()