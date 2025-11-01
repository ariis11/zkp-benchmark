#!/usr/bin/env python3
"""
Convert an image to JSON format for resize transformation.
This is Step 1 of the implementation plan - RESIZE only.
"""

import json
import sys
import argparse
from PIL import Image
import numpy as np


def compress(image_array):
    """
    Compress image array to hex format - groups of 10 pixels per hex value.
    This matches the compression algorithm used in image_formatter.py
    """
    array_in = image_array.tolist()
    output_array = []
    
    for i in range(len(array_in)):
        row = []
        hexValue = ''
        for j in range(len(array_in[i])):
            if np.isscalar(array_in[i][j]):
                # Grayscale - uses 6 hex characters
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


def resize_image(image_array, new_height, new_width):
    """
    Resize an image using bilinear interpolation.
    Matches the algorithm from image_formatter.py
    """
    height, width, channels = image_array.shape
    
    x_ratio = float(width) / float(new_width)
    y_ratio = float(height) / float(new_height)
    
    new_img_array = np.zeros((new_height, new_width, channels), dtype=np.uint8)
    
    if height == 720:
        # Special case for 720p
        for i in range(new_height):
            for j in range(new_width):
                x_l = int(j * x_ratio)
                x_h = int(j * x_ratio) + 1
                y_l = int(i * y_ratio)
                y_h = int(i * y_ratio) + 1
                
                a = image_array[y_l, x_l]
                b = image_array[y_l, x_h]
                c = image_array[y_h, x_l]
                d = image_array[y_h, x_h]
                
                weight = 2 if i % 2 == 0 else 1
                weight = float(weight) / 3
                summ = a * weight + b * weight + c * (1 - weight) + d * (1 - weight)
                new_img_array[i, j] = summ / 2
    else:
        # Standard bilinear interpolation
        for i in range(new_height):
            for j in range(new_width):
                x_l = int(j * x_ratio)
                x_h = int(j * x_ratio) + 1
                y_l = int(i * y_ratio)
                y_h = int(i * y_ratio) + 1
                
                a = image_array[y_l, x_l]
                b = image_array[y_l, x_h]
                c = image_array[y_h, x_l]
                d = image_array[y_h, x_h]
                
                weight = float(1) / 2
                summ = a * weight + b * weight + c * weight + d * weight
                new_img_array[i, j] = summ / 2
    
    return new_img_array


def main():
    parser = argparse.ArgumentParser(
        description='Convert an image to JSON format for resize transformation'
    )
    parser.add_argument('--input', '-i', required=True, help='Input image file')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    parser.add_argument('--from-res', choices=['HD', '4K'], default='HD', 
                       help='Source resolution (default: HD)')
    parser.add_argument('--to-res', choices=['SD', 'FHD'], required=True,
                       help='Target resolution')
    
    args = parser.parse_args()
    
    # Get dimensions based on resolutions
    from_sizes = {
        'HD': (1280, 720),
        '4K': (3840, 2160)
    }
    
    to_sizes = {
        'SD': (640, 480),   # Downscale from HD or 4K
        'FHD': (1920, 1080) # Downscale from 4K
    }
    
    from_width, from_height = from_sizes.get(args.from_res, from_sizes['HD'])
    to_width, to_height = to_sizes.get(args.to_res)
    
    print(f"Processing: {args.input}")
    print(f"Resizing from {args.from_res} ({from_width}x{from_height})")
    print(f"         to {args.to_res} ({to_width}x{to_height})")
    
    try:
        # Load original image
        with Image.open(args.input) as image:
            image_np = np.array(image)
        
        # Check dimensions match expected source
        actual_height, actual_width = image_np.shape[:2]
        if actual_width != from_width or actual_height != from_height:
            print(f"Warning: Image dimensions are {actual_width}x{actual_height}, expected {from_width}x{from_height}")
        
        # Compress original
        compressed_original = compress(image_np)
        
        # Resize and compress transformed
        resized_image = resize_image(image_np, to_height, to_width)
        compressed_transformed = compress(resized_image)
        
        # Create output structure
        output = {
            "original": compressed_original,
            "transformed": compressed_transformed
        }
        
        # Save to JSON
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=4)
        
        print(f"✓ Saved: {args.output}")
        print(f"  Original rows: {len(compressed_original)}")
        print(f"  Transformed rows: {len(compressed_transformed)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

