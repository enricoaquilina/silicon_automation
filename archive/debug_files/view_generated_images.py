#!/usr/bin/env python3
"""
View Generated Images from Instagram DB

Shows the most recently generated images and allows downloading them locally.
"""

import os
from pymongo import MongoClient
from gridfs import GridFS
from datetime import datetime

def connect_to_mongodb():
    """Connect to MongoDB"""
    try:
        client = MongoClient('mongodb://192.168.0.22:27017/')
        db = client['instagram_db']
        fs = GridFS(db)
        
        client.admin.command('ping')
        print("✅ Connected to instagram_db")
        return db, fs
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return None, None

def show_recent_images(db, fs, limit=10):
    """Show recently generated images"""
    print(f"\n🖼️  RECENTLY GENERATED IMAGES (Last {limit})")
    print("=" * 60)
    
    # Get posts with images, sorted by update time
    posts_with_images = list(db.posts.find({
        "image_ref": {"$exists": True},
        "automation_data": {"$exists": True}
    }).sort("updated_at", -1).limit(limit))
    
    for i, post in enumerate(posts_with_images, 1):
        print(f"\n📸 Image {i}:")
        print(f"   📝 Post: {post.get('shortcode', 'unknown')}")
        print(f"   🎨 Prompt: {post['automation_data'].get('prompt', 'N/A')[:80]}...")
        print(f"   💰 Cost: ${post['automation_data'].get('cost', 0):.4f}")
        print(f"   📅 Generated: {post.get('updated_at', 'unknown')}")
        print(f"   🆔 Image Ref: {post['image_ref']}")
        
        # Check if file exists in GridFS
        try:
            image_docs = list(db.post_images.find({"_id": post['image_ref']}))
            if image_docs:
                file_id = image_docs[0]['images'][0]['midjourney_generations'][0]['file_id']
                if fs.exists(file_id):
                    print(f"   ✅ Image file found in GridFS: {file_id}")
                    
                    # Get file info
                    grid_file = fs.get(file_id)
                    print(f"   📏 File size: {grid_file.length} bytes")
                    print(f"   📁 Filename: {grid_file.filename}")
                else:
                    print(f"   ❌ Image file not found in GridFS")
            else:
                print(f"   ❌ No image document found")
        except Exception as e:
            print(f"   ❌ Error checking file: {e}")

def download_image(db, fs, post_shortcode, output_dir="downloaded_images"):
    """Download a specific image by post shortcode"""
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Find the post
        post = db.posts.find_one({"shortcode": post_shortcode})
        if not post:
            print(f"❌ Post {post_shortcode} not found")
            return
            
        if "image_ref" not in post:
            print(f"❌ Post {post_shortcode} has no image")
            return
            
        # Get image document
        image_doc = db.post_images.find_one({"_id": post["image_ref"]})
        if not image_doc:
            print(f"❌ Image document not found for {post_shortcode}")
            return
            
        # Get file ID
        file_id = image_doc['images'][0]['midjourney_generations'][0]['file_id']
        
        # Download from GridFS
        grid_file = fs.get(file_id)
        
        # Save to local file
        filename = f"{post_shortcode}_{file_id}.png"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(grid_file.read())
            
        print(f"✅ Downloaded: {filepath}")
        print(f"📏 Size: {os.path.getsize(filepath)} bytes")
        
        return filepath
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def main():
    print("🖼️  SILICONSENTIMENTS IMAGE VIEWER")
    print("=" * 50)
    
    db, fs = connect_to_mongodb()
    if db is None:
        return
        
    # Show recent images
    show_recent_images(db, fs, limit=5)
    
    print(f"\n" + "=" * 60)
    print("💡 OPTIONS:")
    print("   1. The images are also available at their Replicate URLs")
    print("   2. Run this script to download specific images locally")
    print("   3. Access them directly from GridFS in MongoDB")
    
    # Example: Download the first image
    posts_with_images = list(db.posts.find({
        "image_ref": {"$exists": True},
        "automation_data": {"$exists": True}
    }).sort("updated_at", -1).limit(1))
    
    if posts_with_images:
        shortcode = posts_with_images[0].get('shortcode')
        print(f"\n📥 Downloading latest image ({shortcode}) as example...")
        filepath = download_image(db, fs, shortcode)
        if filepath:
            print(f"🖼️  You can now view: {os.path.abspath(filepath)}")

if __name__ == "__main__":
    main()