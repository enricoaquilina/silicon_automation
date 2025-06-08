#!/usr/bin/env python3
"""
Show the image from a specific image_ref ID
Extract and display the GridFS file
"""

from pymongo import MongoClient
from gridfs import GridFS
import os
from PIL import Image
import io

def show_image_ref():
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

    # The specific image_ref we want to see
    image_ref_id = "6745b87236fb419468b649bc"
    
    print(f'\n🔍 EXAMINING IMAGE_REF: {image_ref_id}')
    print(f'=' * 50)

    # Get the post_images document
    try:
        from bson import ObjectId
        image_doc = db.post_images.find_one({"_id": ObjectId(image_ref_id)})
        
        if not image_doc:
            print(f'❌ Image document not found')
            return
        
        print(f'📋 Image document found for post: {image_doc.get("post_id", "unknown")}')
        
        # Find the main/best image file_id to download
        main_file_id = None
        file_options = []
        
        # Look for file_ids in generations
        if "images" in image_doc:
            for img in image_doc["images"]:
                if "midjourney_generations" in img:
                    for gen in img["midjourney_generations"]:
                        if gen.get("file_id"):
                            file_options.append({
                                "file_id": gen["file_id"],
                                "variation": gen.get("variation", "unknown"),
                                "type": "midjourney_generation"
                            })
        
        if "generations" in image_doc:
            for gen in image_doc["generations"]:
                if gen.get("file_id"):
                    file_options.append({
                        "file_id": gen["file_id"],
                        "variation": gen.get("variation", "unknown"),
                        "is_grid": gen.get("is_grid", False),
                        "type": "generation"
                    })
        
        print(f'\n📁 Found {len(file_options)} file options:')
        
        # Show all options and pick the best one
        best_file = None
        for i, option in enumerate(file_options, 1):
            try:
                grid_file = fs.get(option["file_id"])
                filename = grid_file.filename
                size = grid_file.length
                
                print(f'{i}. {filename} ({size:,} bytes) - {option["variation"]}')
                
                # Pick the largest non-grid file as the best option
                if not option.get("is_grid", False) and (not best_file or size > best_file["size"]):
                    best_file = {
                        "file_id": option["file_id"],
                        "filename": filename,
                        "size": size,
                        "grid_file": grid_file
                    }
                    
            except Exception as e:
                print(f'{i}. {option["file_id"]} - Error: {e}')
        
        # If no non-grid file, pick the largest grid file
        if not best_file and file_options:
            for option in file_options:
                try:
                    grid_file = fs.get(option["file_id"])
                    size = grid_file.length
                    if not best_file or size > best_file["size"]:
                        best_file = {
                            "file_id": option["file_id"],
                            "filename": grid_file.filename,
                            "size": size,
                            "grid_file": grid_file
                        }
                except:
                    continue
        
        if not best_file:
            print(f'❌ No valid files found')
            return
        
        print(f'\n📸 Downloading best image: {best_file["filename"]}')
        print(f'   File ID: {best_file["file_id"]}')
        print(f'   Size: {best_file["size"]:,} bytes')
        
        # Download the file
        output_dir = 'image_ref_downloads'
        os.makedirs(output_dir, exist_ok=True)
        
        grid_file = best_file["grid_file"]
        file_data = grid_file.read()
        
        # Save to local file
        safe_filename = best_file["filename"].replace("/", "_").replace("\\", "_")
        local_path = os.path.join(output_dir, f"image_ref_{image_ref_id}_{safe_filename}")
        
        with open(local_path, 'wb') as f:
            f.write(file_data)
        
        print(f'✅ Downloaded to: {local_path}')
        
        # Try to get image details
        try:
            with Image.open(io.BytesIO(file_data)) as img:
                width, height = img.size
                format_type = img.format
                mode = img.mode
                
                print(f'🖼️  Image details:')
                print(f'   Dimensions: {width}x{height}')
                print(f'   Format: {format_type}')
                print(f'   Mode: {mode}')
                
        except Exception as e:
            print(f'⚠️  Could not read image details: {e}')
        
        # Show metadata
        metadata = getattr(grid_file, 'metadata', {}) or {}
        if metadata:
            print(f'\n📋 File metadata:')
            for key, value in metadata.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f'   {key}: {value[:100]}...')
                else:
                    print(f'   {key}: {value}')
        
        # Show absolute path for viewing
        abs_path = os.path.abspath(local_path)
        print(f'\n👀 VIEW THE IMAGE:')
        print(f'   File path: {abs_path}')
        print(f'   Command: open "{abs_path}"  # On macOS')
        
        # Get the original post details
        post = db.posts.find_one({"image_ref": ObjectId(image_ref_id)})
        if post:
            shortcode = post.get("shortcode", "unknown")
            caption = post.get("caption", "")
            print(f'\n🔗 ORIGINAL POST:')
            print(f'   Shortcode: {shortcode}')
            print(f'   Instagram URL: https://instagram.com/p/{shortcode}/')
            print(f'   Caption: {caption[:200]}...')
        
    except Exception as e:
        print(f'❌ Error: {e}')

    client.close()

if __name__ == "__main__":
    show_image_ref()