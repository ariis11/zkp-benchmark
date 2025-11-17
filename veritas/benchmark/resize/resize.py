#!/usr/bin/env python3
"""
Convert an image to JSON format for Veritas resize transformation.
Resizes from HD (720x1280) to SD (480x640), matching VIMz behavior.
"""

import json
import sys
import argparse
from pathlib import Path
from PIL import Image
import numpy as np


def resize_image_bilinear(image_array, new_height, new_width):
    """
    Resize an image using bilinear interpolation.
    Matches the algorithm from Veritas resize.rs.
    
    Args:
        image_array: 2D numpy array of pixel values (grayscale, 0-255)
        new_height: Target height
        new_width: Target width
    
    Returns:
        2D numpy array of resized pixels
    """
    height, width = image_array.shape
    
    # Calculate ratios
    x_ratio = float(width - 1) / float(new_width - 1) if new_width > 1 else 0
    y_ratio = float(height - 1) / float(new_height - 1) if new_height > 1 else 0
    
    resized = np.zeros((new_height, new_width), dtype=np.uint8)
    
    for i in range(new_height):
        for j in range(new_width):
            # Calculate source positions (matching Veritas resize.rs logic)
            x_l = int((width - 1) * j / (new_width - 1)) if new_width > 1 else 0
            y_l = int((height - 1) * i / (new_height - 1)) if new_height > 1 else 0
            
            x_h = x_l if x_l * (new_width - 1) == (width - 1) * j else min(x_l + 1, width - 1)
            y_h = y_l if y_l * (new_height - 1) == (height - 1) * i else min(y_l + 1, height - 1)
            
            # Get 4 corner pixels
            a = image_array[y_l, x_l]
            b = image_array[y_l, x_h]
            c = image_array[y_h, x_l]
            d = image_array[y_h, x_h]
            
            # Calculate weighted ratios (matching Veritas resize.rs)
            x_ratio_weighted = ((width - 1) * j) - (new_width - 1) * ((width - 1) * j // (new_width - 1)) if new_width > 1 else 0
            y_ratio_weighted = ((height - 1) * i) - (new_height - 1) * ((height - 1) * i // (new_height - 1)) if new_height > 1 else 0
            
            # Bilinear interpolation (matching Veritas resize.rs formula)
            denom = (new_width - 1) * (new_height - 1) if (new_width > 1 and new_height > 1) else 1
            s = (a * (new_width - 1 - x_ratio_weighted) * (new_height - 1 - y_ratio_weighted) +
                 b * x_ratio_weighted * (new_height - 1 - y_ratio_weighted) +
                 c * y_ratio_weighted * (new_width - 1 - x_ratio_weighted) +
                 d * x_ratio_weighted * y_ratio_weighted)
            
            new_val = int(round(s / denom)) if denom > 0 else int(round((a + b + c + d) / 4))
            resized[i, j] = max(0, min(255, new_val))
    
    return resized


def main():
    parser = argparse.ArgumentParser(
        description='Convert an image to JSON format for Veritas resize transformation'
    )
    parser.add_argument('--input', '-i', required=True,
                       help='Input PNG image file')
    parser.add_argument('--output', '-o', required=True,
                       help='Output JSON file')
    parser.add_argument('--from-res', 
                       choices=['HD', '4K'],
                       default='HD',
                       help='Source resolution (default: HD)')
    parser.add_argument('--to-res',
                       choices=['SD', 'FHD'],
                       default='SD',
                       help='Target resolution (default: SD)')
    
    args = parser.parse_args()
    
    # Get dimensions based on resolutions (matching VIMz)
    from_sizes = {
        'HD': (720, 1280),   # (height, width)
        '4K': (2160, 3840)
    }
    
    to_sizes = {
        #'SD': (360, 480),    # (height, width) - for 4GB RAM system
        'SD': (480, 640),    # (height, width) - for server
        'FHD': (1080, 1920)  # (height, width) - downscale from 4K
    }
    
    from_height, from_width = from_sizes.get(args.from_res, from_sizes['HD'])
    to_height, to_width = to_sizes.get(args.to_res, to_sizes['SD'])
    
    print(f"Processing: {args.input}")
    print(f"Resizing from {args.from_res} ({from_height}x{from_width})")
    print(f"         to {args.to_res} ({to_height}x{to_width})")
    
    try:
        # Load original image
        with Image.open(args.input) as image:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            image_np = np.array(image, dtype=np.uint8)
            print(f"Image size: {image_np.shape[0]}x{image_np.shape[1]} pixels")
        
        # Apply resize transformation
        resized_np = resize_image_bilinear(image_np, to_height, to_width)
        
        print(f"Resized to: {resized_np.shape[0]}x{resized_np.shape[1]} pixels")
        
        # Convert to lists for JSON serialization
        original = image_np.tolist()
        resized = resized_np.tolist()
        
        # Create output structure (matching Veritas expected format)
        output = {
            "original": original,
            "resized": resized,
            "original_height": len(original),
            "original_width": len(original[0]) if original else 0,
            "resized_height": len(resized),
            "resized_width": len(resized[0]) if resized else 0,
            "from_resolution": args.from_res,
            "to_resolution": args.to_res
        }
        
        # Save to JSON
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Saved: {args.output}")
        print(f"  Original rows: {len(original)}")
        print(f"  Resized rows: {len(resized)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

