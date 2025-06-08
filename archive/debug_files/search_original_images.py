#!/usr/bin/env python3
"""
Search MongoDB for any posts that have original Instagram images
Look for Instagram URLs vs generated content
"""

from pymongo import MongoClient
from gridfs import GridFS
import json
import re

def search_original_images():
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

    print(f'\n🔍 SEARCHING FOR ORIGINAL INSTAGRAM IMAGES')
    print(f'=========================================')

    # Search patterns for Instagram URLs
    instagram_patterns = [
        r'instagram\.com',
        r'cdninstagram\.com', 
        r'scontent.*\.fbcdn\.net',
        r'ig\.fbcdn\.net'
    ]

    # Check all posts for any Instagram-related image fields
    print(f'\n1️⃣ CHECKING POSTS FOR INSTAGRAM IMAGE FIELDS')
    print(f'============================================')
    
    # Look for posts with any image-related fields that might contain Instagram URLs
    potential_fields = [
        'carousel_urls', 'extracted_images', 'image_urls', 'media_urls',
        'original_images', 'instagram_images', 'source_images'
    ]
    
    posts_with_originals = []
    total_posts = db.posts.count_documents({})
    print(f'Total posts in database: {total_posts}')
    
    for field in potential_fields:
        posts_with_field = list(db.posts.find({field: {"$exists": True, "$ne": []}}).limit(10))
        if posts_with_field:
            print(f'\n📸 Found {len(posts_with_field)} posts with "{field}" field:')
            for post in posts_with_field:
                shortcode = post.get('shortcode', 'unknown')
                field_data = post.get(field, [])
                print(f'   {shortcode}: {field_data[:2] if isinstance(field_data, list) else str(field_data)[:100]}...')
                
                # Check if any URLs are Instagram originals
                if isinstance(field_data, list):
                    for url in field_data:
                        if any(re.search(pattern, str(url)) for pattern in instagram_patterns):
                            print(f'      🟡 INSTAGRAM ORIGINAL FOUND: {url}')
                            posts_with_originals.append({
                                'shortcode': shortcode,
                                'field': field,
                                'url': url,
                                'post_id': str(post['_id'])
                            })
                elif isinstance(field_data, str):
                    if any(re.search(pattern, field_data) for pattern in instagram_patterns):
                        print(f'      🟡 INSTAGRAM ORIGINAL FOUND: {field_data}')
                        posts_with_originals.append({
                            'shortcode': shortcode,
                            'field': field,
                            'url': field_data,
                            'post_id': str(post['_id'])
                        })

    # Check image documents for Instagram URLs
    print(f'\n2️⃣ CHECKING IMAGE DOCUMENTS FOR INSTAGRAM URLS')
    print(f'============================================')
    
    # Search through all image documents
    image_docs = list(db.post_images.find({}).limit(20))
    print(f'Checking {len(image_docs)} image documents...')
    
    for doc in image_docs:
        doc_id = str(doc['_id'])
        post_id = doc.get('post_id', 'unknown')
        
        # Get the post to find shortcode
        post = db.posts.find_one({"_id": doc.get('post_id')}) if doc.get('post_id') else None
        shortcode = post.get('shortcode', 'unknown') if post else 'unknown'
        
        # Check all generations for Instagram URLs
        if 'images' in doc:
            for img_idx, img in enumerate(doc['images']):
                if 'midjourney_generations' in img:
                    for gen_idx, gen in enumerate(img['midjourney_generations']):
                        image_url = gen.get('image_url', '')
                        if any(re.search(pattern, image_url) for pattern in instagram_patterns):
                            print(f'   🟡 INSTAGRAM ORIGINAL in {shortcode}: {image_url}')
                            posts_with_originals.append({
                                'shortcode': shortcode,
                                'field': f'image_doc.images[{img_idx}].midjourney_generations[{gen_idx}]',
                                'url': image_url,
                                'post_id': post_id,
                                'doc_id': doc_id
                            })
        
        # Check top-level generations array if it exists
        if 'generations' in doc:
            for gen_idx, gen in enumerate(doc['generations']):
                image_url = gen.get('image_url', '')
                if any(re.search(pattern, image_url) for pattern in instagram_patterns):
                    print(f'   🟡 INSTAGRAM ORIGINAL in {shortcode}: {image_url}')
                    posts_with_originals.append({
                        'shortcode': shortcode,
                        'field': f'image_doc.generations[{gen_idx}]',
                        'url': image_url,
                        'post_id': post_id,
                        'doc_id': doc_id
                    })

    # Check GridFS for any original Instagram images
    print(f'\n3️⃣ CHECKING GRIDFS FOR ORIGINAL IMAGES')
    print(f'====================================')
    
    try:
        gridfs_files = list(fs.find().limit(20))
        print(f'Checking {len(gridfs_files)} GridFS files...')
        
        for grid_file in gridfs_files:
            filename = grid_file.filename or 'unknown'
            metadata = getattr(grid_file, 'metadata', {}) or {}
            
            # Check filename for Instagram indicators
            if any(pattern.replace('\\', '') in filename.lower() for pattern in ['instagram', 'original', 'extracted']):
                print(f'   📁 Potential original: {filename}')
                print(f'      Metadata: {list(metadata.keys()) if metadata else "None"}')
            
            # Check metadata for source information
            if metadata:
                source = metadata.get('source', '')
                original_url = metadata.get('original_url', '')
                pipeline = metadata.get('pipeline', '')
                
                if any(re.search(pattern, source + original_url) for pattern in instagram_patterns):
                    print(f'   🟡 INSTAGRAM ORIGINAL in GridFS: {filename}')
                    print(f'      Source: {source}')
                    print(f'      Original URL: {original_url}')
                    
                # Check if it's from extraction pipeline
                if 'extract' in pipeline.lower() or 'carousel' in pipeline.lower():
                    print(f'   📸 Extraction pipeline file: {filename}')
                    print(f'      Pipeline: {pipeline}')
                    
    except Exception as e:
        print(f'❌ GridFS check failed: {e}')

    # Check extraction result files in the filesystem
    print(f'\n4️⃣ CHECKING EXTRACTION RESULT FILES')
    print(f'=================================')
    
    # Look for any downloaded/extracted images in the filesystem
    import os
    extraction_dirs = [
        'downloaded_verify_images',
        'extracted_images', 
        'test_results'
    ]
    
    for dirname in extraction_dirs:
        if os.path.exists(dirname):
            print(f'\n📁 Found extraction directory: {dirname}')
            for root, dirs, files in os.walk(dirname):
                for file in files[:10]:  # Show first 10 files
                    if file.endswith(('.jpg', '.png', '.jpeg')):
                        print(f'   📸 {os.path.join(root, file)}')

    # Summary
    print(f'\n📊 SUMMARY OF ORIGINAL INSTAGRAM IMAGES')
    print(f'======================================')
    
    if posts_with_originals:
        print(f'✅ Found {len(posts_with_originals)} posts with original Instagram images:')
        for orig in posts_with_originals[:10]:  # Show first 10
            print(f'   {orig["shortcode"]}: {orig["url"][:80]}...')
        
        print(f'\n🎯 THESE CAN BE USED FOR VLM ANALYSIS!')
        print(f'   Use these original Instagram images with your VLM-to-Flux pipeline')
        print(f'   VLM will analyze REAL Instagram content, not AI-generated images')
    else:
        print(f'❌ No original Instagram images found in database')
        print(f'   All saved images appear to be AI-generated')
        print(f'   Consider running carousel extractors to get original images first')
        print(f'   Or use caption-based generation instead of VLM analysis')

    client.close()

if __name__ == "__main__":
    search_original_images()