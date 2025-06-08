#!/usr/bin/env python3
"""
Check GridFS thoroughly for any downloaded Instagram original images
Look for files that might be from extraction pipelines
"""

from pymongo import MongoClient
from gridfs import GridFS
import json
import re
from datetime import datetime

def check_gridfs_originals():
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

    print(f'\n🔍 COMPREHENSIVE GRIDFS ORIGINAL IMAGE SEARCH')
    print(f'============================================')

    # Get total count first
    try:
        total_files = fs.find().count()
        print(f'Total GridFS files: {total_files}')
    except:
        # Fallback for newer PyMongo versions
        total_files = len(list(fs.find()))
        print(f'Total GridFS files: {total_files}')

    # Categories to track
    categories = {
        'midjourney_generated': [],
        'replicate_generated': [],
        'extracted_originals': [],
        'carousel_extractions': [],
        'vlm_pipeline': [],
        'unknown_source': []
    }

    # Search patterns
    instagram_patterns = [
        r'instagram\.com',
        r'cdninstagram\.com', 
        r'scontent.*\.fbcdn\.net',
        r'ig\.fbcdn\.net',
        r'fmla1-1\.fna\.fbcdn\.net'
    ]

    extraction_indicators = [
        'extract', 'carousel', 'original', 'downloaded', 'scraped'
    ]

    print(f'\n📁 ANALYZING ALL GRIDFS FILES...')
    print(f'================================')

    # Get all files
    all_files = list(fs.find())
    
    for i, grid_file in enumerate(all_files, 1):
        if i % 50 == 0:  # Progress indicator
            print(f'   Processed {i}/{len(all_files)} files...')
            
        file_id = grid_file._id
        filename = grid_file.filename or f'file_{file_id}'
        
        # Get metadata
        metadata = getattr(grid_file, 'metadata', {}) or {}
        
        # File info
        file_info = {
            'file_id': str(file_id),
            'filename': filename,
            'size': grid_file.length,
            'upload_date': grid_file.upload_date,
            'content_type': getattr(grid_file, 'content_type', 'unknown'),
            'metadata_keys': list(metadata.keys()) if metadata else []
        }
        
        # Analyze filename for clues
        filename_lower = filename.lower()
        
        # Check for generation sources
        if 'midjourney' in filename_lower or 'discord' in filename_lower:
            categories['midjourney_generated'].append(file_info)
        elif 'replicate' in filename_lower or 'flux' in filename_lower:
            categories['replicate_generated'].append(file_info)
        elif any(indicator in filename_lower for indicator in extraction_indicators):
            categories['extracted_originals'].append(file_info)
        elif 'carousel' in filename_lower:
            categories['carousel_extractions'].append(file_info)
        elif 'vlm' in filename_lower:
            categories['vlm_pipeline'].append(file_info)
        else:
            # Check metadata for more clues
            source_found = False
            
            if metadata:
                metadata_str = json.dumps(metadata, default=str).lower()
                
                # Check for Instagram original URLs in metadata
                if any(re.search(pattern, metadata_str) for pattern in instagram_patterns):
                    file_info['metadata_extract'] = 'Contains Instagram URLs'
                    categories['extracted_originals'].append(file_info)
                    source_found = True
                elif 'midjourney' in metadata_str or 'discord' in metadata_str:
                    categories['midjourney_generated'].append(file_info)
                    source_found = True
                elif 'replicate' in metadata_str or 'flux' in metadata_str:
                    categories['replicate_generated'].append(file_info)
                    source_found = True
                elif any(indicator in metadata_str for indicator in extraction_indicators):
                    categories['extracted_originals'].append(file_info)
                    source_found = True
                elif 'vlm' in metadata_str or 'pipeline' in metadata_str:
                    categories['vlm_pipeline'].append(file_info)
                    source_found = True
            
            if not source_found:
                categories['unknown_source'].append(file_info)

    # Report findings
    print(f'\n📊 GRIDFS ANALYSIS RESULTS')
    print(f'=========================')
    
    for category, files in categories.items():
        if files:
            print(f'\n🔷 {category.upper().replace("_", " ")}: {len(files)} files')
            
            # Show first 3 files as examples
            for file_info in files[:3]:
                print(f'   📄 {file_info["filename"]}')
                print(f'      Size: {file_info["size"]:,} bytes')
                print(f'      Uploaded: {file_info["upload_date"]}')
                if file_info["metadata_keys"]:
                    print(f'      Metadata: {file_info["metadata_keys"]}')
                if 'metadata_extract' in file_info:
                    print(f'      🟡 {file_info["metadata_extract"]}')
            
            if len(files) > 3:
                print(f'   ... and {len(files) - 3} more files')

    # Focus on extracted originals
    print(f'\n🎯 EXTRACTED ORIGINALS DETAILED ANALYSIS')
    print(f'=======================================')
    
    extracted_files = categories['extracted_originals']
    if extracted_files:
        print(f'Found {len(extracted_files)} potentially extracted original files:')
        
        for file_info in extracted_files:
            print(f'\n📸 {file_info["filename"]}')
            print(f'   File ID: {file_info["file_id"]}')
            print(f'   Size: {file_info["size"]:,} bytes')
            print(f'   Uploaded: {file_info["upload_date"]}')
            
            # Get the actual metadata
            try:
                grid_file = fs.get(file_info["file_id"])
                metadata = getattr(grid_file, 'metadata', {}) or {}
                
                if metadata:
                    print(f'   📋 Metadata:')
                    for key, value in metadata.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f'      {key}: {value[:100]}...')
                        else:
                            print(f'      {key}: {value}')
                    
                    # Check for Instagram URLs
                    metadata_str = json.dumps(metadata, default=str)
                    instagram_urls = []
                    for pattern in instagram_patterns:
                        matches = re.findall(pattern + r'[^\s"]*', metadata_str)
                        instagram_urls.extend(matches)
                    
                    if instagram_urls:
                        print(f'   🟡 Instagram URLs found:')
                        for url in instagram_urls[:3]:
                            print(f'      - {url}')
                            
            except Exception as e:
                print(f'   ❌ Error reading metadata: {e}')
                
    else:
        print(f'❌ No extracted original files found in GridFS')

    # Summary and recommendations
    print(f'\n📋 SUMMARY & RECOMMENDATIONS')
    print(f'============================')
    
    total_generated = len(categories['midjourney_generated']) + len(categories['replicate_generated'])
    total_originals = len(categories['extracted_originals']) + len(categories['carousel_extractions'])
    
    print(f'🤖 AI Generated images in GridFS: {total_generated}')
    print(f'📸 Original Instagram images in GridFS: {total_originals}')
    print(f'🔧 VLM pipeline images: {len(categories["vlm_pipeline"])}')
    print(f'❓ Unknown source: {len(categories["unknown_source"])}')
    
    if total_originals > 0:
        print(f'\n✅ GOOD NEWS: You have {total_originals} original Instagram images in GridFS!')
        print(f'   🎯 These can be used immediately for VLM analysis')
        print(f'   🔍 VLM will analyze real Instagram content (not AI-generated)')
        print(f'   🎨 Perfect source for SiliconSentiments transformations')
        
        print(f'\n🚀 IMMEDIATE ACTION PLAN:')
        print(f'1. Extract these GridFS originals for VLM analysis')
        print(f'2. Run VLM-to-Flux pipeline on original images')
        print(f'3. Generate SiliconSentiments branded versions')
    else:
        print(f'\n⚠️  NO ORIGINAL INSTAGRAM IMAGES IN GRIDFS')
        print(f'   Only AI-generated content found')
        print(f'   Need to extract original Instagram images first')
        
    print(f'\n📝 FILESYSTEM VS GRIDFS:')
    print(f'   Filesystem: 5 original Instagram images (downloaded_verify_images/)')
    print(f'   GridFS: {total_originals} original Instagram images')
    print(f'   Total originals available: {5 + total_originals}')

    client.close()

if __name__ == "__main__":
    check_gridfs_originals()