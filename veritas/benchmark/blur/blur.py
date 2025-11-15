#!/usr/bin/env python3
"""
Convert an image to JSON format for Veritas blur transformation.
Uses 3x3 box blur kernel matching Veritas blur.rs implementation.
"""

import json
import sys
import argparse
from pathlib import Path
from PIL import Image
import numpy as np


def apply_blur(image_array, blur_region=None):
    """
    Apply 3x3 box blur to image array.
    Matches the algorithm from Veritas blur.rs.
    
    Args:
        image_array: 2D numpy array of pixel values (grayscale, 0-255)
        blur_region: Tuple (start_row, start_col, height, width) or None for full image
    
    Returns:
        2D numpy array of blurred pixels
    """
    height, width = image_array.shape
    blurred = np.zeros_like(image_array, dtype=np.uint8)
    
    # Determine blur region
    if blur_region:
        start_row, start_col, blur_h, blur_w = blur_region
        end_row = min(start_row + blur_h, height - 1)
        end_col = min(start_col + blur_w, width - 1)
    else:
        # Blur entire image (excluding borders)
        start_row, start_col = 1, 1
        end_row, end_col = height - 1, width - 1
    
    # Copy original image first
    blurred = image_array.copy()
    
    # Apply blur to specified region
    for i in range(start_row, end_row):
        for j in range(start_col, end_col):
            # 3x3 box blur: sum of 9 neighbors / 9
            # This matches Veritas blur.rs exactly
            # Convert to int to avoid uint8 overflow
            sum_val = (int(image_array[i-1][j-1]) + int(image_array[i-1][j]) + int(image_array[i-1][j+1]) +
                      int(image_array[i][j-1])   + int(image_array[i][j])   + int(image_array[i][j+1]) +
                      int(image_array[i+1][j-1]) + int(image_array[i+1][j]) + int(image_array[i+1][j+1]))
            
            # Round and clamp (matching Veritas: round(sum / 9.0))
            blurred[i][j] = int(round(sum_val / 9.0))
            blurred[i][j] = max(0, min(255, blurred[i][j]))
    
    return blurred


def main():
    parser = argparse.ArgumentParser(
        description='Convert an image to JSON format for Veritas blur transformation'
    )
    parser.add_argument('--input', '-i', required=True,
                       help='Input PNG image file')
    parser.add_argument('--output', '-o', required=True,
                       help='Output JSON file')
    parser.add_argument('--resolution', '-r',
                       choices=['SD', 'HD', 'FHD', '4K'],
                       default='HD',
                       help='Image resolution (default: HD)')
    parser.add_argument('--blur-region', nargs=4, type=int,
                       metavar=('START_ROW', 'START_COL', 'HEIGHT', 'WIDTH'),
                       help='Blur region: start_row start_col height width (default: full image excluding borders)')
    parser.add_argument('--resize', nargs=2, type=int,
                       metavar=('HEIGHT', 'WIDTH'),
                       help='Resize image to HEIGHT x WIDTH before processing')
    
    args = parser.parse_args()
    
    print(f"Processing: {args.input}")
    print(f"Resolution: {args.resolution}")
    
    try:
        # Load original image
        with Image.open(args.input) as image:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize if requested
            if args.resize:
                height, width = args.resize
                image = image.resize((width, height), Image.Resampling.LANCZOS)
                print(f"Resized image to {height}x{width}")
            
            image_np = np.array(image, dtype=np.uint8)
            print(f"Image size: {image_np.shape[0]}x{image_np.shape[1]} pixels")
        
        # Apply blur transformation
        blur_region = tuple(args.blur_region) if args.blur_region else None
        blurred_np = apply_blur(image_np, blur_region)
        
        if blur_region:
            print(f"Applied blur to region: row {blur_region[0]}-{blur_region[0]+blur_region[2]}, "
                  f"col {blur_region[1]}-{blur_region[1]+blur_region[3]}")
        else:
            print(f"Applied blur to entire image (excluding 1-pixel border)")
        
        # Convert to lists for JSON serialization
        original = image_np.tolist()
        blurred = blurred_np.tolist()
        
        # Create output structure (matching Veritas expected format)
        output = {
            "original": original,
            "blurred": blurred,
            "height": len(original),
            "width": len(original[0]) if original else 0,
            "blur_region": blur_region if blur_region else None,
            "resolution": args.resolution
        }
        
        # Save to JSON
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Saved: {args.output}")
        print(f"  Original rows: {len(original)}")
        print(f"  Blurred rows: {len(blurred)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

