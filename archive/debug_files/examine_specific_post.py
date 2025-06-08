#!/usr/bin/env python3
"""
Examine a specific post in detail to understand the image data structure
"""

from pymongo import MongoClient
from gridfs import GridFS
import json
from bson import ObjectId

def examine_post_detail():
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

    # Get the first post with complete data
    post_id = "66b88bd6b2979f6117b347fc"  # C013goXoa0_
    
    print(f'\n🔍 DETAILED POST EXAMINATION')
    print(f'==========================')
    
    # Get the post
    post = db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        print(f'❌ Post not found')
        return
    
    print(f'📋 POST DETAILS:')
    print(f'   Shortcode: {post.get("shortcode")}')
    print(f'   Caption: {post.get("caption", "")[:100]}...')
    print(f'   Created At: {post.get("created_at")}')
    print(f'   Instagram Status: {post.get("instagram_status")}')
    print(f'   Image Ref: {post.get("image_ref")}')
    
    # Get the image document
    image_doc = db.post_images.find_one({"_id": post["image_ref"]})
    print(f'\n🖼️  IMAGE DOCUMENT:')
    print(f'   ID: {image_doc["_id"]}')
    print(f'   Status: {image_doc.get("status")}')
    print(f'   Created: {image_doc.get("created_at")}')
    
    # Show the complete structure
    print(f'\n📄 COMPLETE IMAGE DOCUMENT STRUCTURE:')
    
    # Remove binary data for readable output
    clean_doc = dict(image_doc)
    if "_id" in clean_doc:
        clean_doc["_id"] = str(clean_doc["_id"])
    
    print(json.dumps(clean_doc, indent=2, default=str))
    
    # Check if this post has any Instagram original images
    print(f'\n🔍 LOOKING FOR INSTAGRAM ORIGINALS:')
    
    # Check if the post has carousel URLs or original Instagram image URLs
    if "carousel_urls" in post:
        print(f'   📸 Carousel URLs found: {len(post["carousel_urls"])}')
        for i, url in enumerate(post["carousel_urls"][:3], 1):
            print(f'      {i}. {url}')
            if "instagram.com" in url or "cdninstagram.com" in url:
                print(f'         🟡 This is an Instagram original URL!')
    
    # Check for any extracted Instagram images
    if "extracted_images" in post:
        print(f'   📸 Extracted images found: {len(post["extracted_images"])}')
        for i, img in enumerate(post["extracted_images"][:3], 1):
            print(f'      {i}. {img}')
            if "instagram.com" in img or "cdninstagram.com" in img:
                print(f'         🟡 This is an Instagram original URL!')
    
    # Check if any URLs in generations point to Instagram
    if "images" in image_doc:
        for img in image_doc["images"]:
            if "midjourney_generations" in img:
                for gen in img["midjourney_generations"]:
                    if gen.get("image_url"):
                        url = gen["image_url"]
                        if "instagram.com" in url or "cdninstagram.com" in url:
                            print(f'   🟡 FOUND INSTAGRAM ORIGINAL: {url}')
                        elif "discord" in url or "midjourney" in url:
                            print(f'   🟣 FOUND MIDJOURNEY GENERATED: {url[:60]}...')
    
    # Check what other fields the post might have
    print(f'\n📊 POST FIELDS ANALYSIS:')
    all_fields = list(post.keys())
    print(f'   All fields: {all_fields}')
    
    # Look for any image-related fields
    image_fields = [field for field in all_fields if 'image' in field.lower() or 'url' in field.lower() or 'carousel' in field.lower()]
    print(f'   Image-related fields: {image_fields}')
    
    # Show any image-related data
    for field in image_fields:
        if field in post and post[field]:
            data = post[field]
            if isinstance(data, list):
                print(f'   {field}: [{len(data)} items] {data[:2] if len(data) > 0 else []}...')
            else:
                print(f'   {field}: {str(data)[:100]}...')

    client.close()

if __name__ == "__main__":
    examine_post_detail()