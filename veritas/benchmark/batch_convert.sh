#!/bin/bash

# Batch convert images to JSON for Veritas transformations
# Usage: ./batch_convert.sh <transformation> <input_dir> <output_dir> [additional_params]
#
# Example:
#   ./batch_convert.sh blur passports_hd blur/outputs_hd
#   ./batch_convert.sh blur passports_hd blur/outputs_hd --blur-region 1 1 6 6

TRANSFORMATION="${1:-blur}"  # Default to blur
INPUT_DIR="${2:-passports_hd}"
OUTPUT_DIR="${3:-blur/outputs_hd}"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FULL_INPUT_DIR="$SCRIPT_DIR/$INPUT_DIR"
FULL_OUTPUT_DIR="$SCRIPT_DIR/$OUTPUT_DIR"

# Create output directory
mkdir -p "$FULL_OUTPUT_DIR"

# Count total files
TOTAL=$(find "$FULL_INPUT_DIR" -name "*.png" 2>/dev/null | wc -l)

if [ "$TOTAL" -eq 0 ]; then
    echo "Error: No PNG files found in $FULL_INPUT_DIR"
    exit 1
fi

echo "========================================="
echo "Batch Image Conversion for Veritas"
echo "========================================="
echo "Transformation: $TRANSFORMATION"
echo "Input directory: $FULL_INPUT_DIR"
echo "Output directory: $FULL_OUTPUT_DIR"
echo "Found $TOTAL image(s) to process"
echo "========================================="
echo ""

# Counter for progress
COUNT=0

# Process each PNG file
for img in "$FULL_INPUT_DIR"/*.png; do
    if [ -f "$img" ]; then
        COUNT=$((COUNT + 1))
        BASENAME=$(basename "$img" .png)
        
        echo "[$COUNT/$TOTAL] Processing: $(basename "$img")"
        
        # Choose the appropriate converter and parameters
        if [ "$TRANSFORMATION" == "blur" ]; then
            OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
            
            # Check if additional blur region parameters are provided
            if [ $# -ge 7 ] && [ "$4" == "--blur-region" ]; then
                # Custom blur region: --blur-region start_row start_col height width
                python3 "$SCRIPT_DIR/blur/blur.py" \
                    -i "$img" \
                    -o "$OUTPUT_FILE" \
                    -r HD \
                    --blur-region "$5" "$6" "$7" "$8"
            else
                # Default: blur entire image (excluding borders)
                python3 "$SCRIPT_DIR/blur/blur.py" \
                    -i "$img" \
                    -o "$OUTPUT_FILE" \
                    -r HD
            fi
        
        # Add other transformations here in the future
        # elif [ "$TRANSFORMATION" == "resize" ]; then
        #     OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
        #     python3 "$SCRIPT_DIR/resize/resize.py" \
        #         -i "$img" \
        #         -o "$OUTPUT_FILE" \
        #         -r HD
        #
        # elif [ "$TRANSFORMATION" == "crop" ]; then
        #     ...
        
        else
            echo "  ✗ Unknown transformation: $TRANSFORMATION"
            echo "  Supported transformations: blur"
            continue
        fi
        
        if [ $? -eq 0 ]; then
            echo "  ✓ Saved: $(basename "$OUTPUT_FILE")"
        else
            echo "  ✗ Failed to process $(basename "$img")"
        fi
        echo ""
    fi
done

echo "========================================="
echo "Batch processing complete!"
echo "Processed $COUNT image(s)"
echo "JSON files saved to: $FULL_OUTPUT_DIR"
echo "========================================="

