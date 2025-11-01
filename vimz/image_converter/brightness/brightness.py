#!/usr/bin/env python3
"""
Convert an image to JSON format for brightness transformation.
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


def adjust_brightness_and_compress(image_array, brightness_factor):
    """
    Adjust brightness and return compressed result.
    Matches the algorithm from image_formatter.py
    """
    # Convert to float for calculations
    np_image_float = image_array.astype(float)
    
    # Multiply by brightness factor
    adjusted_image_float = np_image_float * brightness_factor
    
    # Clip to valid range [0, 255] and convert back to uint8
    adjusted_image = np.clip(adjusted_image_float, 0, 255).astype(np.uint8)
    
    # Compress
    compressed = compress(adjusted_image)
    
    return compressed


def main():
    parser = argparse.ArgumentParser(
        description='Convert an image to JSON format for brightness transformation'
    )
    parser.add_argument('--input', '-i', required=True, help='Input image file')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    parser.add_argument('--resolution', '-r', 
                       choices=['SD', 'HD', 'FHD', '4K'],
                       default='HD',
                       help='Image resolution (default: HD)')
    parser.add_argument('--factor', '-f', type=float, default=1.5,
                       help='Brightness factor (default: 1.5)')
    
    args = parser.parse_args()
    
    print(f"Processing: {args.input}")
    print(f"Resolution: {args.resolution}")
    print(f"Brightness factor: {args.factor}")
    
    try:
        # Load original image
        with Image.open(args.input) as image:
            image_np = np.array(image)
        
        # Compress original
        compressed_original = compress(image_np)
        
        # Apply brightness and compress
        compressed_transformed = adjust_brightness_and_compress(image_np, args.factor)
        
        # Create output structure
        output = {
            "original": compressed_original,
            "transformed": compressed_transformed,
            "factor": int(args.factor * 10)  # Store as integer (* 10 to match expected format)
        }
        
        # Save to JSON
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=4)
        
        print(f"✓ Saved: {args.output}")
        print(f"  Original rows: {len(compressed_original)}")
        print(f"  Transformed rows: {len(compressed_transformed)}")
        print(f"  Factor: {output['factor']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

