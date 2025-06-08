#!/usr/bin/env python3
"""
Get complete MongoDB metadata for a post with downloaded images - Fixed version
"""

from pymongo import MongoClient
from gridfs import GridFS
import json
from bson import ObjectId

def get_complete_post_metadata():
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

    # Find a post that has image_ref
    post_with_image = db.posts.find_one({"image_ref": {"$exists": True}})
    if not post_with_image:
        print(f'❌ No posts with image_ref found')
        return
    
    shortcode = post_with_image.get("shortcode", "unknown")
    print(f'\n🔍 COMPLETE METADATA FOR POST: {shortcode}')
    print(f'=' * 60)

    # POST DOCUMENT
    print(f'\n📋 1. POST DOCUMENT')
    print(f'-' * 30)
    clean_post = dict(post_with_image)
    if "_id" in clean_post:
        clean_post["_id"] = str(clean_post["_id"])
    if "image_ref" in clean_post:
        clean_post["image_ref"] = str(clean_post["image_ref"])
    
    print(json.dumps(clean_post, indent=2, default=str))
    
    # POST_IMAGES DOCUMENT
    print(f'\n🖼️  2. POST_IMAGES DOCUMENT')
    print(f'-' * 30)
    
    image_doc = db.post_images.find_one({"_id": post_with_image["image_ref"]})
    if image_doc:
        clean_image_doc = dict(image_doc)
        if "_id" in clean_image_doc:
            clean_image_doc["_id"] = str(clean_image_doc["_id"])
        if "post_id" in clean_image_doc:
            clean_image_doc["post_id"] = str(clean_image_doc["post_id"])
        
        print(json.dumps(clean_image_doc, indent=2, default=str))
        
        # GRIDFS FILES
        print(f'\n💾 3. GRIDFS FILES REFERENCED')
        print(f'-' * 30)
        
        file_ids_found = set()
        
        # Extract file_ids from generations
        if "images" in image_doc:
            for img in image_doc["images"]:
                if "midjourney_generations" in img:
                    for gen in img["midjourney_generations"]:
                        if gen.get("file_id"):
                            file_ids_found.add(gen["file_id"])
        
        if "generations" in image_doc:
            for gen in image_doc["generations"]:
                if gen.get("file_id"):
                    file_ids_found.add(gen["file_id"])
        
        print(f'Found {len(file_ids_found)} file IDs in generations')
        
        for i, file_id in enumerate(file_ids_found, 1):
            print(f'\n📄 GridFS File {i}: {file_id}')
            try:
                grid_file = fs.get(file_id)
                print(f'   Filename: {grid_file.filename}')
                print(f'   Size: {grid_file.length:,} bytes')
                print(f'   Upload Date: {grid_file.upload_date}')
                
                metadata = getattr(grid_file, 'metadata', {}) or {}
                if metadata:
                    print(f'   Metadata keys: {list(metadata.keys())}')
                    # Show key metadata fields
                    key_fields = ['brand', 'automated', 'provider', 'model', 'prompt', 'cost']
                    for field in key_fields:
                        if field in metadata:
                            value = metadata[field]
                            if isinstance(value, str) and len(value) > 80:
                                print(f'   {field}: {value[:80]}...')
                            else:
                                print(f'   {field}: {value}')
                        
            except Exception as e:
                print(f'   ❌ Error: {e}')
    
    # ORIGINAL EXTRACTION FILES
    print(f'\n📸 4. ORIGINAL EXTRACTION FILES')
    print(f'-' * 30)
    
    original_files = list(fs.find({"filename": {"$regex": f"instagram_production_{shortcode}_"}}))
    print(f'Found {len(original_files)} original files for {shortcode}')
    
    for i, grid_file in enumerate(original_files, 1):
        print(f'\n📄 Original File {i}:')
        print(f'   Filename: {grid_file.filename}')
        print(f'   Size: {grid_file.length:,} bytes')
        print(f'   Upload Date: {grid_file.upload_date}')
        
        metadata = getattr(grid_file, 'metadata', {}) or {}
        if metadata:
            key_fields = ['shortcode', 'img_index', 'original_url', 'extracted_at', 'quality', 'extractor_version']
            for field in key_fields:
                if field in metadata:
                    value = metadata[field]
                    if field == 'original_url' and len(str(value)) > 100:
                        print(f'   {field}: {str(value)[:100]}...')
                    else:
                        print(f'   {field}: {value}')

    # SUMMARY ANALYSIS
    print(f'\n📊 5. METADATA ANALYSIS SUMMARY')
    print(f'-' * 30)
    print(f'Post shortcode: {shortcode}')
    print(f'Instagram URL: https://instagram.com/p/{shortcode}/')
    print(f'Post fields: {len(clean_post)}')
    
    if image_doc:
        generation_count = 0
        if "images" in image_doc:
            for img in image_doc["images"]:
                if "midjourney_generations" in img:
                    generation_count += len(img["midjourney_generations"])
        if "generations" in image_doc:
            generation_count += len(image_doc["generations"])
        
        print(f'Total generations: {generation_count}')
        print(f'GridFS files referenced: {len(file_ids_found)}')
    
    print(f'Original extraction files: {len(original_files)}')
    
    # Check if we have the complete pipeline
    has_originals = len(original_files) > 0
    has_generations = image_doc and (
        ("images" in image_doc and any("midjourney_generations" in img for img in image_doc["images"])) or
        ("generations" in image_doc and len(image_doc["generations"]) > 0)
    )
    
    print(f'\n🎯 PIPELINE STATUS:')
    print(f'   Has original Instagram images: {"✅ Yes" if has_originals else "❌ No"}')
    print(f'   Has AI generations: {"✅ Yes" if has_generations else "❌ No"}')
    
    if has_originals and not has_generations:
        print(f'   Status: 🔄 Ready for VLM-to-Flux processing')
    elif has_originals and has_generations:
        print(f'   Status: ✅ Complete pipeline (Original → Generation)')
    elif not has_originals and has_generations:
        print(f'   Status: ⚠️  AI-only (no original source)')
    else:
        print(f'   Status: ❌ No content')

    client.close()

if __name__ == "__main__":
    get_complete_post_metadata()