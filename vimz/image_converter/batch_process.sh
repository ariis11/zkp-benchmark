#!/bin/bash

# Batch process all passport images
# Converts all images in passports_hd/ to JSON format

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="$SCRIPT_DIR/passports_hd"
OUTPUT_DIR="$SCRIPT_DIR/outputs"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Count total files
TOTAL=$(find "$INPUT_DIR" -name "*.png" | wc -l)
echo "Found $TOTAL image(s) to process"
echo ""

# Counter for progress
COUNT=0

# Process each PNG file
for img in "$INPUT_DIR"/*.png; do
    if [ -f "$img" ]; then
        COUNT=$((COUNT + 1))
        BASENAME=$(basename "$img" .png)
        OUTPUT_FILE="$OUTPUT_DIR/${BASENAME}.json"
        
        echo "[$COUNT/$TOTAL] Processing: $(basename "$img")"
        
        # Run the conversion
        python3 "$SCRIPT_DIR/resize/resize.py" \
            -i "$img" \
            -o "$OUTPUT_FILE" \
            --from-res HD \
            --to-res SD
        
        if [ $? -eq 0 ]; then
            echo "  ✓ Saved: ${BASENAME}.json"
        else
            echo "  ✗ Failed to process $(basename "$img")"
        fi
        echo ""
    fi
done

echo "========================================="
echo "Batch processing complete!"
echo "Processed $COUNT image(s)"
echo "JSON files saved to: $OUTPUT_DIR"
echo "========================================="

