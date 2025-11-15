#!/usr/bin/env python3
"""
Convert an image to JSON format for Veritas grayscale transformation.
Converts RGB image to grayscale using standard formula: 0.299*R + 0.587*G + 0.114*B
Matches VIMz behavior: processes full image.
"""

import json
import sys
import argparse
from pathlib import Path
from PIL import Image
import numpy as np


def rgb_to_grayscale(image_array):
    """
    Convert RGB image to grayscale using standard formula.
    Matches VIMz: 299*R + 587*G + 114*B, then divided by 1000.
    
    Args:
        image_array: 3D numpy array of RGB pixel values (height, width, 3)
    
    Returns:
        2D numpy array of grayscale pixel values (height, width)
    """
    if len(image_array.shape) == 2:
        # Already grayscale
        return image_array
    
    # Standard grayscale conversion: 0.299*R + 0.587*G + 0.114*B
    # VIMz uses: (299*R + 587*G + 114*B) / 1000
    r, g, b = image_array[:, :, 0], image_array[:, :, 1], image_array[:, :, 2]
    grayscale = (299 * r.astype(np.uint32) + 587 * g.astype(np.uint32) + 114 * b.astype(np.uint32)) // 1000
    return grayscale.astype(np.uint8)


def main():
    parser = argparse.ArgumentParser(
        description='Convert an image to JSON format for Veritas grayscale transformation'
    )
    parser.add_argument('--input', '-i', required=True,
                       help='Input PNG image file')
    parser.add_argument('--output', '-o', required=True,
                       help='Output JSON file')
    parser.add_argument('--resolution', '-r',
                       choices=['SD', 'HD', 'FHD', '4K'],
                       default='HD',
                       help='Image resolution (default: HD)')
    parser.add_argument('--process-region', action='store_true',
                       help='Process only a region to fit memory (240x320)')
    parser.add_argument('--region-height', type=int, default=240,
                       help='Region height (default: 240)')
    parser.add_argument('--region-width', type=int, default=320,
                       help='Region width (default: 320)')
    
    args = parser.parse_args()
    
    print(f"Processing: {args.input}")
    print(f"Resolution: {args.resolution}")
    
    try:
        # Load original image
        with Image.open(args.input) as image:
            # Keep original as RGB (or convert to RGB if needed)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            image_np = np.array(image, dtype=np.uint8)
            print(f"Image size: {image_np.shape[0]}x{image_np.shape[1]} pixels")
        
        # Apply grayscale transformation to full image first
        grayscale_np_full = rgb_to_grayscale(image_np)
        
        # Extract region if requested (to fit memory constraints)
        if args.process_region:
            region_h = min(args.region_height, image_np.shape[0])
            region_w = min(args.region_width, image_np.shape[1])
            image_np = image_np[0:region_h, 0:region_w]
            grayscale_np = grayscale_np_full[0:region_h, 0:region_w]
            print(f"Processing region: {region_h}x{region_w} pixels (from top-left)")
        else:
            grayscale_np = grayscale_np_full
        
        print(f"Grayscale size: {grayscale_np.shape[0]}x{grayscale_np.shape[1]} pixels")
        
        # Convert to lists for JSON serialization
        # Original: RGB format (height, width, 3) -> list of [R, G, B] per pixel
        original = []
        for i in range(image_np.shape[0]):
            row = []
            for j in range(image_np.shape[1]):
                pixel = [int(image_np[i, j, 0]), int(image_np[i, j, 1]), int(image_np[i, j, 2])]
                row.append(pixel)
            original.append(row)
        
        # Grayscale: single value per pixel
        grayscale = grayscale_np.tolist()
        
        # Create output structure (matching Veritas expected format)
        output = {
            "original": original,  # RGB format: [[[R,G,B], ...], ...]
            "grayscale": grayscale,  # Grayscale format: [[value, ...], ...]
            "height": len(original),
            "width": len(original[0]) if original else 0,
            "resolution": args.resolution
        }
        
        # Save to JSON
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Saved: {args.output}")
        print(f"  Original rows: {len(original)} (RGB)")
        print(f"  Grayscale rows: {len(grayscale)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

