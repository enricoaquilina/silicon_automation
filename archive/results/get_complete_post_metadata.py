#!/usr/bin/env python3
"""
Get complete MongoDB metadata for a post with downloaded images
Show full details from posts, post_images, and GridFS
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

    print(f'\n🔍 GETTING COMPLETE POST METADATA')
    print(f'=================================')

    # Find a post that has both extracted images and generations
    # Let's use C0wmEEKItfR since we know it has downloaded images
    shortcode = "C0wmEEKItfR"
    
    # Get the post document
    post = db.posts.find_one({"shortcode": shortcode})
    if not post:
        print(f'❌ Post {shortcode} not found')
        return
    
    print(f'📋 POST DOCUMENT ({shortcode})')
    print(f'=' * 50)
    
    # Clean the post document for display
    clean_post = dict(post)
    if "_id" in clean_post:
        clean_post["_id"] = str(clean_post["_id"])
    if "image_ref" in clean_post:
        clean_post["image_ref"] = str(clean_post["image_ref"])
    
    print(json.dumps(clean_post, indent=2, default=str))
    
    # Get the image document if it exists
    if post.get("image_ref"):
        print(f'\n🖼️  POST_IMAGES DOCUMENT')
        print(f'=' * 50)
        
        image_doc = db.post_images.find_one({"_id": post["image_ref"]})
        if image_doc:
            # Clean the image document
            clean_image_doc = dict(image_doc)
            if "_id" in clean_image_doc:
                clean_image_doc["_id"] = str(clean_image_doc["_id"])
            if "post_id" in clean_image_doc:
                clean_image_doc["post_id"] = str(clean_image_doc["post_id"])
            
            print(json.dumps(clean_image_doc, indent=2, default=str))
            
            # Check GridFS files referenced in the generations
            print(f'\n💾 GRIDFS FILES ANALYSIS')
            print(f'=' * 50)
            
            file_ids_found = set()
            
            # Look through all generations to find file_ids
            if "images" in image_doc:
                for img_idx, img in enumerate(image_doc["images"]):
                    if "midjourney_generations" in img:
                        for gen_idx, gen in enumerate(img["midjourney_generations"]):
                            if gen.get("file_id"):
                                file_ids_found.add(gen["file_id"])
            
            if "generations" in image_doc:
                for gen in image_doc["generations"]:
                    if gen.get("file_id"):
                        file_ids_found.add(gen["file_id"])
            
            print(f'Found {len(file_ids_found)} file IDs referenced in generations')
            
            for i, file_id in enumerate(file_ids_found, 1):
                print(f'\n📄 GRIDFS FILE {i}: {file_id}')
                print(f'-' * 30)
                
                try:
                    grid_file = fs.get(file_id)
                    print(f'Filename: {grid_file.filename}')
                    print(f'Size: {grid_file.length:,} bytes')
                    print(f'Upload Date: {grid_file.upload_date}')
                    print(f'Content Type: {getattr(grid_file, "content_type", "unknown")}')
                    
                    # Get metadata
                    metadata = getattr(grid_file, 'metadata', {}) or {}
                    if metadata:
                        print(f'Metadata:')
                        for key, value in metadata.items():
                            if isinstance(value, str) and len(value) > 150:
                                print(f'  {key}: {value[:150]}...')
                            else:
                                print(f'  {key}: {value}')
                    else:
                        print(f'No metadata')
                        
                except Exception as e:
                    print(f'❌ Error reading GridFS file {file_id}: {e}')
    
    # Look for any original extraction files for this shortcode
    print(f'\n📸 ORIGINAL EXTRACTION FILES')
    print(f'=' * 50)
    
    original_files = list(fs.find({"filename": {"$regex": f"instagram_production_{shortcode}_"}}))
    print(f'Found {len(original_files)} original extraction files for {shortcode}')
    
    for i, grid_file in enumerate(original_files, 1):
        print(f'\n📄 ORIGINAL FILE {i}:')
        print(f'   Filename: {grid_file.filename}')
        print(f'   Size: {grid_file.length:,} bytes')
        print(f'   Upload Date: {grid_file.upload_date}')
        
        # Get metadata
        metadata = getattr(grid_file, 'metadata', {}) or {}
        if metadata:
            print(f'   Original URL: {metadata.get("original_url", "N/A")[:100]}...')
            print(f'   Extraction Date: {metadata.get("extracted_at", "N/A")}')
            print(f'   Quality: {metadata.get("quality", "N/A")}')
            print(f'   Extractor Version: {metadata.get("extractor_version", "N/A")}')

    # Summary
    print(f'\n📊 METADATA SUMMARY FOR {shortcode}')
    print(f'=' * 50)
    print(f'Post collection fields: {len(clean_post)} fields')
    if post.get("image_ref"):
        print(f'Has image_ref: ✅ {post["image_ref"]}')
        if image_doc:
            total_generations = 0
            if "images" in image_doc:
                for img in image_doc["images"]:
                    if "midjourney_generations" in img:
                        total_generations += len(img["midjourney_generations"])
            if "generations" in image_doc:
                total_generations += len(image_doc["generations"])
            print(f'Total generations: {total_generations}')
        else:
            print(f'Image document: ❌ Not found')
    else:
        print(f'Has image_ref: ❌ No')
    
    print(f'GridFS files referenced: {len(file_ids_found)}')
    print(f'Original extraction files: {len(original_files)}')
    print(f'Instagram URL: https://instagram.com/p/{shortcode}/')

    client.close()

if __name__ == "__main__":
    get_complete_post_metadata()