#!/usr/bin/env python3
"""
Convert an image to JSON format for crop transformation.
Uses optimized_crop circuit which only needs original image and info field.
"""

import json
import sys
import argparse
from PIL import Image
import numpy as np


def compress(image_array):
    """
    Compress image array to hex format - groups of 10 pixels per hex value.
    """
    array_in = image_array.tolist()
    output_array = []
    
    for i in range(len(array_in)):
        row = []
        hexValue = ''
        for j in range(len(array_in[i])):
            if np.isscalar(array_in[i][j]):
                # Grayscale
                hexValue = hex(int(array_in[i][j]))[2:].zfill(6) + hexValue
            else:
                # RGB - pack B, G, R in reverse order
                for k in range(0, 3):
                    hexValue = hex(int(array_in[i][j][k]))[2:].zfill(2) + hexValue
            if j % 10 == 9:
                row.append("0x" + hexValue)
                hexValue = ''
        output_array.append(row)
    return output_array


def main():
    parser = argparse.ArgumentParser(
        description='Convert an image to JSON format for crop transformation'
    )
    parser.add_argument('--input', '-i', required=True, help='Input image file')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    parser.add_argument('--resolution', '-r', 
                       choices=['SD', 'HD', 'FHD', '4K'],
                       default='HD',
                       help='Image resolution (default: HD)')
    parser.add_argument('--crop-x', type=int, default=0, help='Crop X coordinate (default: 0)')
    parser.add_argument('--crop-y', type=int, default=0, help='Crop Y coordinate (default: 0)')
    
    args = parser.parse_args()
    
    # Get crop dimensions based on resolution
    sizes = {
        'SD': (640, 480),
        'HD': (1280, 720),
        'FHD': (1920, 1080),
        '4K': (3840, 2160)
    }
    
    width, height = sizes.get(args.resolution, sizes['HD'])
    
    print(f"Processing: {args.input}")
    print(f"Resolution: {args.resolution} ({width}x{height})")
    print(f"Crop coordinates: ({args.crop_x}, {args.crop_y})")
    
    try:
        # Load original image
        with Image.open(args.input) as image:
            image_np = np.array(image)
        
        # Check dimensions
        actual_height, actual_width = image_np.shape[:2]
        if actual_width < args.crop_x + width or actual_height < args.crop_y + height:
            print(f"Error: Image too small for crop. Image is {actual_width}x{actual_height}, need at least {args.crop_x + width}x{args.crop_y + height}")
            sys.exit(1)
        
        # Compress original (full image, not cropped)
        compressed_original = compress(image_np)
        
        # Encode crop coordinates as: x * 2^24 + y * 2^12
        info = args.crop_x * 2**24 + args.crop_y * 2**12
        
        # Create output structure
        output = {
            "original": compressed_original,
            "info": info
        }
        
        # Save to JSON
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=4)
        
        print(f"✓ Saved: {args.output}")
        print(f"  Original rows: {len(compressed_original)}")
        print(f"  Info: {info}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

