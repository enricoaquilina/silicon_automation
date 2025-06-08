#!/usr/bin/env python3
"""
Quick script to download a single Instagram image
"""
import requests
import os

def download_image(url, filename):
    """Download image from URL to filename"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded: {filename} ({os.path.getsize(filename)} bytes)")
        return True
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False

if __name__ == "__main__":
    # Third image URL from the fixed carousel extractor
    image_url = "https://instagram.fmla1-1.fna.fbcdn.net/v/t51.29350-15/462044130_154268679996982_8885298950885675070_n.jpg?stp=dst-jpg_e35_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0uaW1hZ2VfdXJsZ2VuLjE0NDB4MTgwMC5zZHIuZjI5MzUwLmRlZmF1bHRfaW1hZ2UifQ&_nc_ht=instagram.fmla1-1.fna.fbcdn.net&_nc_cat=105&_nc_ohc=8d5wglrJSh0Q7kNvwHy4qBd&_nc_gid=avIYtM2aTrqJAZcdLsHHmA&edm=APs17CUBAAAA&ccb=7-5&ig_cache_key=MzQ2Mzg4ODM4NjQ4NDI4MjM0Nw%3D%3D.3-ccb7-5&oh=00_AfD9a5D6xT5Qr5tLQFyHhPdlXoZNYGvLTi42HKTMWevjZg&oe=6845E5B6&_nc_sid=10d13b"
    
    output_path = "/Users/enricoaquilina/Documents/Fraud/silicon_automation/downloaded_verify_images/verify_C0xFHGOrBN7/C0xFHGOrBN7_image_3.jpg"
    
    success = download_image(image_url, output_path)
    if success:
        print(f"✅ Successfully downloaded third image for C0xFHGOrBN7")
    else:
        print(f"❌ Failed to download third image")