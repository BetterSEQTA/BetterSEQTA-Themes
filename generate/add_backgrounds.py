#!/usr/bin/env python3
"""
Script to add new background images to the store.
Takes images from an input folder, converts them to webp, creates thumbnails,
and adds entries to backgrounds.json with placeholder values.
"""

from PIL import Image
import os
import json
import re
from pathlib import Path
from tqdm import tqdm

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

INPUT_FOLDER = PROJECT_ROOT / "input_images"
BACKGROUNDS_DIR = PROJECT_ROOT / "store" / "backgrounds"
FULL_DIR = BACKGROUNDS_DIR / "images" / "full"
THUMB_DIR = BACKGROUNDS_DIR / "images" / "thumb"
BACKGROUNDS_JSON = PROJECT_ROOT / "store" / "backgrounds.json"
BASE_URL = "https://raw.githubusercontent.com/BetterSEQTA/BetterSEQTA-Themes/main/store/backgrounds"

THUMB_SIZE = (340, 170)

def create_thumbnail(image, size=THUMB_SIZE):
    width, height = image.size
    aspect_ratio = width / height
    target_ratio = size[0] / size[1]

    if aspect_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    else:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))

    return image.resize(size, Image.Resampling.LANCZOS)

def get_next_image_id():
    existing_ids = set()
    
    if FULL_DIR.exists():
        for file in FULL_DIR.glob("image-*.webp"):
            match = re.search(r'image-(\d+)', file.name)
            if match:
                existing_ids.add(int(match.group(1)))
    
    if BACKGROUNDS_JSON.exists():
        try:
            with open(BACKGROUNDS_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for bg in data.get('backgrounds', []):
                    bg_id = bg.get('id', '')
                    match = re.search(r'image-(\d+)', bg_id)
                    if match:
                        existing_ids.add(int(match.group(1)))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse backgrounds.json: {e}")
    
    if existing_ids:
        next_id = max(existing_ids) + 1
    else:
        next_id = 1
    
    return next_id

def load_backgrounds_json():
    if BACKGROUNDS_JSON.exists():
        try:
            with open(BACKGROUNDS_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Could not parse backgrounds.json: {e}")
            return {"backgrounds": []}
    return {"backgrounds": []}

def save_backgrounds_json(data):
    BACKGROUNDS_JSON.parent.mkdir(parents=True, exist_ok=True)
    
    with open(BACKGROUNDS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    with open(BACKGROUNDS_JSON, 'a', encoding='utf-8') as f:
        f.write('\n')

def process_images(input_folder):
    if isinstance(input_folder, str):
        input_path = Path(input_folder)
        if not input_path.is_absolute():
            input_path = PROJECT_ROOT / input_path
    else:
        input_path = Path(input_folder)
    
    if not input_path.exists():
        print(f"Error: Input folder '{input_folder}' does not exist!")
        print(f"Please create the folder and add your images there.")
        return
    
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif')
    
    image_files = [f for f in input_path.iterdir() 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"No image files found in '{input_folder}'!")
        print(f"Supported formats: {', '.join(image_extensions)}")
        return
    
    print(f"Found {len(image_files)} image(s) to process")
    
    FULL_DIR.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    
    backgrounds_data = load_backgrounds_json()
    
    current_id = get_next_image_id()
    print(f"Starting with image ID: image-{current_id}")
    
    new_entries = []
    
    for image_file in tqdm(image_files, desc="Processing images"):
        try:
            with Image.open(image_file) as img:
                if img.mode in ('RGBA', 'P', 'LA'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                    else:
                        rgb_img.paste(img)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                image_id = f"image-{current_id}"
                
                full_path = FULL_DIR / f"{image_id}.webp"
                img.save(
                    full_path,
                    'WEBP',
                    quality=85,
                    method=6  # Highest compression method
                )
                
                thumb = create_thumbnail(img.copy())
                thumb_path = THUMB_DIR / f"{image_id}.webp"
                thumb.save(
                    thumb_path,
                    'WEBP',
                    quality=85,
                    method=6
                )
                
                entry = {
                    "id": image_id,
                    "category": "Uncategorized", 
                    "type": "image",
                    "lowResUrl": f"{BASE_URL}/images/thumb/{image_id}.webp",
                    "highResUrl": f"{BASE_URL}/images/full/{image_id}.webp",
                    "name": "No Tags",  
                    "featured": False  
                }
                
                new_entries.append(entry)
                backgrounds_data['backgrounds'].append(entry)
                
                current_id += 1
                
        except Exception as e:
            print(f"\nError processing {image_file.name}: {e}")
            continue
    
    if new_entries:
        save_backgrounds_json(backgrounds_data)
        print(f"\n✓ Successfully processed {len(new_entries)} image(s)")
        print(f"✓ Added entries to {BACKGROUNDS_JSON}")
        print(f"\nNext steps:")
        print(f"  1. Edit {BACKGROUNDS_JSON} to update:")
        print(f"     - 'category' (currently set to 'Uncategorized')")
        print(f"     - 'name' (currently using filename)")
        print(f"     - 'featured' (currently set to false)")
        print(f"\n  2. The following entries were added:")
        for entry in new_entries:
            print(f"     - {entry['id']}: {entry['name']}")
    else:
        print("\nNo images were successfully processed.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_folder_arg = sys.argv[1]
        input_folder = Path(input_folder_arg)
        if not input_folder.is_absolute():
            input_folder = PROJECT_ROOT / input_folder
    else:
        input_folder = INPUT_FOLDER
    
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Adding backgrounds from: {input_folder}")
    print(f"Output directory: {BACKGROUNDS_DIR}")
    print()
    
    process_images(input_folder)

