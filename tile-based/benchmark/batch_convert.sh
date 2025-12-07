#!/bin/bash

# Batch convert images to JSON for Tile-Based transformations
# Usage: ./batch_convert.sh <transformation> <input_dir> <output_dir> [additional_params]
#
# Example:
#   ./batch_convert.sh grayscale ../../assets/passports_hd grayscale/outputs_hd
#   ./batch_convert.sh blur ../../assets/passports_hd blur/outputs_hd
#   ./batch_convert.sh crop ../../assets/passports_hd crop/outputs_hd

TRANSFORMATION="${1:-grayscale}"  # Default to grayscale
INPUT_DIR="${2:-../../assets/passports_hd}"
OUTPUT_DIR="${3:-grayscale/outputs_hd}"

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
echo "Batch Image Conversion for Tile-Based"
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
        OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
        
        echo "[$COUNT/$TOTAL] Processing: $(basename "$img")"
        
        # Choose the appropriate converter based on transformation
        if [ "$TRANSFORMATION" == "grayscale" ] || [ "$TRANSFORMATION" == "gray" ]; then
            # Convert RGB to grayscale (full image, matching Veritas/VIMz)
            # Region: 720x1280, for server memory
            python3 "$SCRIPT_DIR/grayscale/grayscale.py" \
                -i "$img" \
                -o "$OUTPUT_FILE" \
                -r HD \
                --process-region \
                --region-height 720 \
                --region-width 1280
        
        # Template for future transformations - uncomment and implement as needed
        # elif [ "$TRANSFORMATION" == "blur" ]; then
        #     OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
        #     # TODO: Implement tile-based blur conversion
        #     # python3 "$SCRIPT_DIR/blur/blur.py" \
        #     #     -i "$img" \
        #     #     -o "$OUTPUT_FILE" \
        #     #     -r HD
        # 
        # elif [ "$TRANSFORMATION" == "crop" ]; then
        #     OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
        #     # TODO: Implement tile-based crop conversion
        #     # python3 "$SCRIPT_DIR/crop/crop.py" \
        #     #     -i "$img" \
        #     #     -o "$OUTPUT_FILE" \
        #     #     -r HD
        # 
        # elif [ "$TRANSFORMATION" == "resize" ]; then
        #     OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
        #     # TODO: Implement tile-based resize conversion
        #     # python3 "$SCRIPT_DIR/resize/resize.py" \
        #     #     -i "$img" \
        #     #     -o "$OUTPUT_FILE" \
        #     #     --from-res HD \
        #     #     --to-res SD
        
        else
            echo "  ✗ Unknown transformation: $TRANSFORMATION"
            echo "  Supported transformations: grayscale"
            echo "  Note: Other transformations (blur, crop, resize) are planned for future implementation"
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

