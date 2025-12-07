#!/usr/bin/env python3
"""
Convert an image to JSON format for grayscale transformation.
Outputs: {
  "original": [[...]],
  "transformed": [[...]]
}
"""

import json
import sys
import argparse
from PIL import Image
import numpy as np


def compress(image_array):
    # Compress image array to hex format - groups of 10 pixels per hex value.
    array_in = image_array.tolist()
    output_array = []
    for i in range(len(array_in)):
        row = []
        hexValue = ''
        for j in range(len(array_in[i])):
            if np.isscalar(array_in[i][j]):
                hexValue = hex(int(array_in[i][j]))[2:].zfill(6) + hexValue
            else:
                for k in range(0, 3):
                    hexValue = hex(int(array_in[i][j][k]))[2:].zfill(2) + hexValue
            if j % 10 == 9:
                row.append("0x" + hexValue)
                hexValue = ''
        output_array.append(row)
    return output_array


def main():
    parser = argparse.ArgumentParser(
        description='Convert an image to JSON format for grayscale transformation'
    )
    parser.add_argument('--input', '-i', required=True, help='Input image file')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    parser.add_argument('--resolution', '-r', choices=['SD', 'HD', 'FHD', '4K'], default='HD')

    args = parser.parse_args()

    try:
        with Image.open(args.input) as image:
            image_np = np.array(image)
            grayscale_image = image.convert('L')
            grayscale_np = np.array(grayscale_image)

        original_compressed = compress(image_np)
        transformed_compressed = compress(grayscale_np)

        out = {
            "original": original_compressed,
            "transformed": transformed_compressed,
        }
        with open(args.output, 'w') as f:
            json.dump(out, f, indent=4)
        print(f"✓ Saved: {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
