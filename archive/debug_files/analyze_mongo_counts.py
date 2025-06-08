#!/usr/bin/env python3
"""
Quick analysis of MongoDB posts and images to determine VLM-to-Flux potential
"""

from pymongo import MongoClient
import os

def analyze_mongodb():
    # Connect to MongoDB (try local first, then pi)
    try:
        client = MongoClient('mongodb://localhost:27017/')
        client.admin.command('ping')
        db_name = 'silicon_sentiments'
        print('✅ Connected to local MongoDB')
    except:
        try:
            client = MongoClient('mongodb://192.168.0.22:27017/')
            client.admin.command('ping')
            db_name = 'instagram_db'
            print('✅ Connected to Pi MongoDB')
        except Exception as e:
            print(f'❌ MongoDB connection failed: {e}')
            return

    db = client[db_name]

    # Analyze posts collection
    posts = list(db.posts.find({}))
    post_images = list(db.post_images.find({}))

    print(f'\n📊 DATABASE ANALYSIS')
    print(f'==================')
    print(f'Total posts: {len(posts)}')
    print(f'Total post_images documents: {len(post_images)}')

    # Count posts with images
    posts_with_image_ref = 0
    posts_with_actual_images = 0
    posts_ready_to_publish = 0
    vlm_ready_posts = []

    for post in posts:
        if post.get('image_ref'):
            posts_with_image_ref += 1
            
            # Check if image_ref actually has valid images
            image_doc = db.post_images.find_one({'_id': post['image_ref']})
            if image_doc and image_doc.get('images'):
                for img in image_doc['images']:
                    if img.get('midjourney_generations'):
                        for gen in img['midjourney_generations']:
                            if gen.get('midjourney_image_id') or gen.get('image_url'):
                                posts_with_actual_images += 1
                                if post.get('instagram_status') == 'ready_to_publish':
                                    posts_ready_to_publish += 1
                                
                                # Check if this post has accessible image URL for VLM
                                if gen.get('image_url'):
                                    vlm_ready_posts.append({
                                        'shortcode': post.get('shortcode', 'unknown'),
                                        'image_url': gen['image_url'],
                                        'post_id': str(post['_id'])
                                    })
                                break
                        break

    posts_missing_images = len(posts) - posts_with_actual_images

    print(f'\n🖼️  IMAGE ANALYSIS')
    print(f'================')
    print(f'Posts with image_ref: {posts_with_image_ref}')
    print(f'Posts with actual images: {posts_with_actual_images}')
    print(f'Posts missing images: {posts_missing_images}')
    print(f'Posts ready to publish: {posts_ready_to_publish}')
    
    print(f'\n📈 PERCENTAGES')
    print(f'============')
    print(f'Posts with images: {(posts_with_actual_images/len(posts)*100):.1f}%')
    print(f'Posts missing images: {(posts_missing_images/len(posts)*100):.1f}%')

    print(f'\n🚀 VLM PIPELINE POTENTIAL')
    print(f'========================')
    print(f'Posts with accessible image URLs: {len(vlm_ready_posts)}')
    print(f'Can analyze existing images and generate {posts_missing_images} new images')
    print(f'Cost estimate (Flux Schnell): ${posts_missing_images * 0.003:.2f}')
    
    # Show sample VLM-ready posts
    print(f'\n📋 VLM-READY SAMPLES (first 5):')
    for i, post in enumerate(vlm_ready_posts[:5], 1):
        print(f'{i}. {post["shortcode"]} - {post["image_url"][:60]}...')
    
    print(f'\n💡 RECOMMENDATION:')
    print(f'================')
    if len(vlm_ready_posts) > 10:
        print(f'✅ You have {len(vlm_ready_posts)} posts with images that can be analyzed by VLM')
        print(f'✅ VLM can extract descriptions from these images')
        print(f'✅ Generate {posts_missing_images} new images using VLM-extracted prompts')
        print(f'✅ Total cost would be ~${posts_missing_images * 0.003:.2f} with Flux Schnell')
        print(f'\n🎯 START WITH: Run vlm_to_flux_pipeline.py to begin generation!')
    else:
        print(f'⚠️  Only {len(vlm_ready_posts)} posts have accessible images for VLM analysis')
        print(f'⚠️  Consider first extracting more images or using caption-based generation')

    client.close()

if __name__ == "__main__":
    analyze_mongodb()