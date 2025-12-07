#!/usr/bin/env python3
"""
Convert an image to JSON format for blur transformation.
Uses convolution kernel to blur the image.
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


def conv2d(array, kernel, weight=1):
    """
    2D convolution operation.
    Matches the algorithm from image_formatter.py
    """
    array_height, array_width = len(array), len(array[0])
    kernel_height, kernel_width = len(kernel), len(kernel[0])
    
    # Extend the array with zeros
    border_size = kernel_height // 2
    extended = [[0 for _ in range(array_width + border_size * 2)] 
                for _ in range(array_height + border_size * 2)]
    for i in range(array_height):
        for j in range(array_width):
            extended[i+border_size][j+border_size] = array[i][j]
    
    # Initialize the output (convolved) array
    convolved_array = [[0 for _ in range(array_width)] for _ in range(array_height)]
    
    # Perform the convolution
    for i in range(array_height):
        for j in range(array_width):
            conv_value = 0
            for m in range(kernel_height):
                for n in range(kernel_width):
                    conv_value += extended[i + m][j + n] * kernel[m][n]
            convolved_array[i][j] = conv_value // weight
            if convolved_array[i][j] > 255:
                convolved_array[i][j] = 255
            elif convolved_array[i][j] < 0:
                convolved_array[i][j] = 0
    
    return convolved_array


def blur_and_compress(image_array):
    """
    Blur image using convolution kernel and return compressed result.
    """
    kernel = np.array([
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]
    ])
    
    r_channel, g_channel, b_channel = np.rollaxis(image_array, axis=-1)
    
    # Use weight 9 for averaging (3x3 kernel = 9 values)
    r_adjusted = conv2d(r_channel, kernel, 9)
    g_adjusted = conv2d(g_channel, kernel, 9)
    b_adjusted = conv2d(b_channel, kernel, 9)
    
    adjusted_image = np.dstack((r_adjusted, g_adjusted, b_adjusted))
    
    # Compress
    compressed = compress(adjusted_image)
    
    return compressed


def main():
    parser = argparse.ArgumentParser(
        description='Convert an image to JSON format for blur transformation'
    )
    parser.add_argument('--input', '-i', required=True, help='Input image file')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    parser.add_argument('--resolution', '-r', 
                       choices=['SD', 'HD', 'FHD', '4K'],
                       default='HD',
                       help='Image resolution (default: HD)')
    
    args = parser.parse_args()
    
    print(f"Processing: {args.input}")
    print(f"Resolution: {args.resolution}")
    
    try:
        # Load original image
        with Image.open(args.input) as image:
            image_np = np.array(image)
        
        # Compress original
        compressed_original = compress(image_np)
        
        # Create compressed zeros row (one row of zeros for padding)
        # Number of zeros = image width / 10 (one hex value per 10 pixels)
        width = len(image_np[0])
        zeros_per_row = width // 10
        compressed_zeros = [["0x00"] * zeros_per_row]
        
        # Blur and compress transformed
        compressed_transformed = blur_and_compress(image_np)
        
        # Create output structure
        # Original is padded with zeros: zeros + original + zeros
        output = {
            "original": compressed_zeros + compressed_original + compressed_zeros,
            "transformed": compressed_transformed
        }
        
        # Save to JSON
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=4)
        
        print(f"✓ Saved: {args.output}")
        print(f"  Original rows: {len(output['original'])} (with padding)")
        print(f"  Transformed rows: {len(compressed_transformed)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

