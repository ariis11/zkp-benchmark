#!/usr/bin/env python3
"""
Convert an image to JSON format for Veritas crop transformation.
Crops a region from the original image (simple format, matching Veritas crop.rs).
"""

import json
import sys
import argparse
from pathlib import Path
from PIL import Image
import numpy as np


def apply_crop(image_array, crop_x=0, crop_y=0, crop_width=None, crop_height=None, resolution='HD'):
    """
    Crop a region from the image array.
    Matches VIMz crop behavior: for HD, crops 1280x720 (full image).
    
    Args:
        image_array: 2D numpy array of pixel values (grayscale, 0-255)
        crop_x: X coordinate to start crop (default: 0)
        crop_y: Y coordinate to start crop (default: 0)
        crop_width: Width of crop region (default: based on resolution)
        crop_height: Height of crop region (default: based on resolution)
        resolution: Resolution string (SD, HD, FHD, 4K)
    
    Returns:
        2D numpy array of cropped pixels
    """
    height, width = image_array.shape
    
    # Get crop dimensions based on resolution (matching VIMz)
    sizes = {
        'SD': (640, 480),    # (width, height)
        'HD': (1280, 720),   # (width, height) - full image
        'FHD': (1920, 1080),
        '4K': (3840, 2160)
    }
    
    if crop_width is None or crop_height is None:
        default_width, default_height = sizes.get(resolution, sizes['HD'])
        if crop_width is None:
            crop_width = default_width
        if crop_height is None:
            crop_height = default_height
    
    # Ensure crop fits within image
    crop_width = min(crop_width, width - crop_x)
    crop_height = min(crop_height, height - crop_y)
    
    # Extract crop region
    cropped = image_array[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
    
    return cropped


def main():
    parser = argparse.ArgumentParser(
        description='Convert an image to JSON format for Veritas crop transformation'
    )
    parser.add_argument('--input', '-i', required=True,
                       help='Input PNG image file')
    parser.add_argument('--output', '-o', required=True,
                       help='Output JSON file')
    parser.add_argument('--resolution', '-r',
                       choices=['SD', 'HD', 'FHD', '4K'],
                       default='HD',
                       help='Image resolution (default: HD)')
    parser.add_argument('--crop-x', type=int, default=0,
                       help='Crop X coordinate (default: 0)')
    parser.add_argument('--crop-y', type=int, default=0,
                       help='Crop Y coordinate (default: 0)')
    parser.add_argument('--crop-width', type=int, default=None,
                       help='Crop width (default: 100 or available)')
    parser.add_argument('--crop-height', type=int, default=None,
                       help='Crop height (default: 100 or available)')
    
    args = parser.parse_args()
    
    print(f"Processing: {args.input}")
    print(f"Resolution: {args.resolution}")
    
    try:
        # Load original image
        with Image.open(args.input) as image:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            image_np = np.array(image, dtype=np.uint8)
            print(f"Image size: {image_np.shape[0]}x{image_np.shape[1]} pixels")
        
        # Apply crop transformation (matching VIMz: HD = 1280x720)
        cropped_np = apply_crop(image_np, args.crop_x, args.crop_y, 
                                args.crop_width, args.crop_height, args.resolution)
        
        print(f"Cropped region: {args.crop_x},{args.crop_y} size {cropped_np.shape[1]}x{cropped_np.shape[0]}")
        
        # Convert to lists for JSON serialization
        original = image_np.tolist()
        cropped = cropped_np.tolist()
        
        # Create output structure (matching Veritas expected format)
        output = {
            "original": original,
            "cropped": cropped,
            "height": len(original),
            "width": len(original[0]) if original else 0,
            "crop_x": args.crop_x,
            "crop_y": args.crop_y,
            "crop_width": len(cropped[0]) if cropped else 0,
            "crop_height": len(cropped),
            "resolution": args.resolution
        }
        
        # Save to JSON
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Saved: {args.output}")
        print(f"  Original rows: {len(original)}")
        print(f"  Cropped rows: {len(cropped)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

