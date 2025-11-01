#!/bin/bash

# Batch convert images to JSON for different transformations
# Usage: ./batch_convert.sh <transformation> <input_dir> <output_dir> [additional_params]

TRANSFORMATION="${1:-resize}"  # Default to resize
INPUT_DIR="${2:-passports_hd}"
OUTPUT_DIR="${3:-contrast/outputs_hd}"
FACTOR="${4:-1.5}"  # For contrast/brightness

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FULL_INPUT_DIR="$SCRIPT_DIR/$INPUT_DIR"
FULL_OUTPUT_DIR="$SCRIPT_DIR/$OUTPUT_DIR"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Count total files
TOTAL=$(find "$FULL_INPUT_DIR" -name "*.png" | wc -l)
echo "Found $TOTAL image(s) to process"
echo "Transformation: $TRANSFORMATION"
echo ""

# Counter for progress
COUNT=0

# Create output directory
mkdir -p "$FULL_OUTPUT_DIR"

# Process each PNG file
for img in "$FULL_INPUT_DIR"/*.png; do
    if [ -f "$img" ]; then
        COUNT=$((COUNT + 1))
        BASENAME=$(basename "$img" .png)
        
        echo "[$COUNT/$TOTAL] Processing: $(basename "$img")"
        
        # Choose the appropriate converter and parameters
        if [ "$TRANSFORMATION" == "resize" ]; then
            OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
            python3 "$SCRIPT_DIR/resize/resize.py" \
                -i "$img" \
                -o "$OUTPUT_FILE" \
                --from-res HD \
                --to-res SD
        
        elif [ "$TRANSFORMATION" == "contrast" ]; then
            OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
            python3 "$SCRIPT_DIR/contrast/contrast.py" \
                -i "$img" \
                -o "$OUTPUT_FILE" \
                -r HD \
                -f "$FACTOR"
        
        elif [ "$TRANSFORMATION" == "crop" ]; then
            OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
            # Default crop coordinates (can be customized)
            CROP_X=${5:-0}
            CROP_Y=${6:-0}
            python3 "$SCRIPT_DIR/crop/crop.py" \
                -i "$img" \
                -o "$OUTPUT_FILE" \
                -r HD \
                --crop-x "$CROP_X" \
                --crop-y "$CROP_Y"
        
        elif [ "$TRANSFORMATION" == "grayscale" ]; then
            OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
            python3 "$SCRIPT_DIR/grayscale/grayscale.py" \
                -i "$img" \
                -o "$OUTPUT_FILE" \
                -r HD
        
        elif [ "$TRANSFORMATION" == "brightness" ]; then
            OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
            python3 "$SCRIPT_DIR/brightness/brightness.py" \
                -i "$img" \
                -o "$OUTPUT_FILE" \
                -r HD \
                -f "$FACTOR"
        
        elif [ "$TRANSFORMATION" == "sharpness" ]; then
            OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
            python3 "$SCRIPT_DIR/sharpness/sharpness.py" \
                -i "$img" \
                -o "$OUTPUT_FILE" \
                -r HD
        
        elif [ "$TRANSFORMATION" == "blur" ]; then
            OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
            python3 "$SCRIPT_DIR/blur/blur.py" \
                -i "$img" \
                -o "$OUTPUT_FILE" \
                -r HD
        
        else
            echo "  ✗ Unknown transformation: $TRANSFORMATION"
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

