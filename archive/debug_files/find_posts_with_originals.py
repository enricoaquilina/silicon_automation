#!/usr/bin/env python3
"""
Find posts that have original Instagram images properly linked in the database
Look for posts with both original extractions and proper database references
"""

from pymongo import MongoClient
from gridfs import GridFS
import json
from bson import ObjectId

def find_posts_with_originals():
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

    print(f'\n🔍 FINDING POSTS WITH ORIGINAL INSTAGRAM IMAGES')
    print(f'===============================================')

    # Get all original extraction files from GridFS
    original_files = list(fs.find({"filename": {"$regex": "instagram_production_"}}))
    print(f'Found {len(original_files)} original extraction files in GridFS')

    # Group by shortcode
    shortcodes_with_originals = {}
    for grid_file in original_files:
        filename = grid_file.filename
        # Extract shortcode from filename: instagram_production_C0wmEEKItfR_1.jpg
        parts = filename.split('_')
        if len(parts) >= 3:
            shortcode = parts[2]
            if shortcode not in shortcodes_with_originals:
                shortcodes_with_originals[shortcode] = []
            
            shortcodes_with_originals[shortcode].append({
                'file_id': str(grid_file._id),
                'filename': filename,
                'size': grid_file.length,
                'upload_date': grid_file.upload_date
            })

    print(f'Original images found for {len(shortcodes_with_originals)} shortcodes:')
    for shortcode, files in shortcodes_with_originals.items():
        print(f'  {shortcode}: {len(files)} images')

    # Now check which of these shortcodes have posts in the database
    print(f'\n📋 CHECKING POSTS COLLECTION FOR THESE SHORTCODES')
    print(f'===============================================')

    posts_with_originals = []
    posts_with_linked_originals = []

    for shortcode in shortcodes_with_originals.keys():
        post = db.posts.find_one({"shortcode": shortcode})
        if post:
            post_info = {
                'shortcode': shortcode,
                'post_id': str(post['_id']),
                'image_ref': post.get('image_ref'),
                'instagram_status': post.get('instagram_status', 'unknown'),
                'caption': post.get('caption', '')[:100] + '...',
                'original_files': shortcodes_with_originals[shortcode]
            }
            posts_with_originals.append(post_info)
            
            # Check if the post has an image_ref that might contain the originals
            if post.get('image_ref'):
                image_doc = db.post_images.find_one({"_id": post["image_ref"]})
                if image_doc:
                    # Check if any generation references the original files
                    file_ids_in_generations = set()
                    
                    if "images" in image_doc:
                        for img in image_doc["images"]:
                            if "midjourney_generations" in img:
                                for gen in img["midjourney_generations"]:
                                    if gen.get("file_id"):
                                        file_ids_in_generations.add(gen["file_id"])
                    
                    if "generations" in image_doc:
                        for gen in image_doc["generations"]:
                            if gen.get("file_id"):
                                file_ids_in_generations.add(gen["file_id"])
                    
                    # Check if any original file_ids are linked
                    original_file_ids = {f['file_id'] for f in shortcodes_with_originals[shortcode]}
                    linked_originals = original_file_ids.intersection(file_ids_in_generations)
                    
                    if linked_originals:
                        post_info['linked_original_files'] = list(linked_originals)
                        posts_with_linked_originals.append(post_info)
            
            print(f'\n📄 POST: {shortcode}')
            print(f'   Post ID: {post_info["post_id"]}')
            print(f'   Image Ref: {post_info["image_ref"] or "None"}')
            print(f'   Status: {post_info["instagram_status"]}')
            print(f'   Original files: {len(post_info["original_files"])}')
            print(f'   Caption: {post_info["caption"]}')
            
            if 'linked_original_files' in post_info:
                print(f'   ✅ LINKED ORIGINALS: {len(post_info["linked_original_files"])} files')
            else:
                print(f'   ⚠️  Original files not linked in image_ref')
        else:
            print(f'\n❌ No post found for shortcode: {shortcode}')

    # Show posts that have originals but aren't properly linked
    print(f'\n📊 SUMMARY')
    print(f'==========')
    print(f'Posts with original Instagram images: {len(posts_with_originals)}')
    print(f'Posts with properly linked originals: {len(posts_with_linked_originals)}')
    
    unlinked_posts = len(posts_with_originals) - len(posts_with_linked_originals)
    print(f'Posts with unlinked originals: {unlinked_posts}')

    if posts_with_linked_originals:
        print(f'\n✅ POSTS READY FOR VLM PIPELINE:')
        for post in posts_with_linked_originals:
            print(f'   {post["shortcode"]} - {len(post["linked_original_files"])} linked originals')
            print(f'      Image ref: {post["image_ref"]}')
            print(f'      Instagram URL: https://instagram.com/p/{post["shortcode"]}/')

    if unlinked_posts > 0:
        print(f'\n🔧 POSTS NEEDING LINKING:')
        unlinked = [p for p in posts_with_originals if 'linked_original_files' not in p]
        for post in unlinked[:5]:  # Show first 5
            print(f'   {post["shortcode"]} - {len(post["original_files"])} original files available')
            print(f'      Need to link to image_ref: {post["image_ref"] or "Create new image_ref"}')

    # Show a specific example if we have one
    if posts_with_originals:
        example_post = posts_with_originals[0]
        shortcode = example_post['shortcode']
        
        print(f'\n🔍 EXAMPLE: VIEWING ORIGINAL FROM {shortcode}')
        print(f'=' * 50)
        
        # Download one original for viewing
        first_original = example_post['original_files'][0]
        
        try:
            grid_file = fs.get(ObjectId(first_original['file_id']))
            
            # Save to local file for viewing
            import os
            output_dir = 'original_instagram_examples'
            os.makedirs(output_dir, exist_ok=True)
            
            filename = first_original['filename']
            local_path = os.path.join(output_dir, filename)
            
            file_data = grid_file.read()
            with open(local_path, 'wb') as f:
                f.write(file_data)
            
            print(f'📸 Downloaded example original: {filename}')
            print(f'   Local path: {os.path.abspath(local_path)}')
            print(f'   Size: {len(file_data):,} bytes')
            
            # Get metadata
            metadata = getattr(grid_file, 'metadata', {}) or {}
            if metadata:
                print(f'   Original URL: {metadata.get("original_url", "N/A")[:100]}...')
                print(f'   Extracted at: {metadata.get("extracted_at", "N/A")}')
                print(f'   Quality: {metadata.get("quality", "N/A")}')
            
            print(f'\n👀 VIEW THIS ORIGINAL INSTAGRAM IMAGE:')
            print(f'   open "{os.path.abspath(local_path)}"')
            
        except Exception as e:
            print(f'❌ Error downloading example: {e}')

    client.close()

if __name__ == "__main__":
    find_posts_with_originals()