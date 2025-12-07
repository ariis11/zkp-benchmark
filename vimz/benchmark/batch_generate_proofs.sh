#!/bin/bash

# Batch generate proofs and extract timing metrics
# This script processes all JSON files in a directory and collects performance data

# Get the script directory and go to parent (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."  # Go to project root

PROJECT_ROOT="$(pwd)"

# Get parameters - they should be relative to PROJECT_ROOT
INPUT_DIR="${1:-image_converter/resize/outputs_hd}"  # Default to outputs_hd
OUTPUT_DIR="${2:-image_converter/resize/proofs}"     # Default to proofs directory
TRANSFORMATION="${3:-resize}"                        # Transformation type
RESOLUTION="${4:-HD}"                                # Resolution

# Construct full paths
FULL_INPUT_DIR="$PROJECT_ROOT/$INPUT_DIR"
FULL_OUTPUT_DIR="$PROJECT_ROOT/$OUTPUT_DIR"
# Set results file based on transformation
if [ "$TRANSFORMATION" == "crop" ]; then
    RESULTS_FILE="$PROJECT_ROOT/image_converter/crop/performance_results.json"
elif [ "$TRANSFORMATION" == "contrast" ]; then
    RESULTS_FILE="$PROJECT_ROOT/image_converter/contrast/performance_results.json"
elif [ "$TRANSFORMATION" == "grayscale" ]; then
    RESULTS_FILE="$PROJECT_ROOT/image_converter/grayscale/performance_results.json"
elif [ "$TRANSFORMATION" == "brightness" ]; then
    RESULTS_FILE="$PROJECT_ROOT/image_converter/brightness/performance_results.json"
elif [ "$TRANSFORMATION" == "sharpness" ]; then
    RESULTS_FILE="$PROJECT_ROOT/image_converter/sharpness/performance_results.json"
elif [ "$TRANSFORMATION" == "blur" ]; then
    RESULTS_FILE="$PROJECT_ROOT/image_converter/blur/performance_results.json"
else
    RESULTS_FILE="$PROJECT_ROOT/image_converter/resize/performance_results.json"
fi

# Create directories
mkdir -p "$FULL_OUTPUT_DIR"

# Circuit and witness generator paths (relative to project root)
# Special handling for crop (uses optimized_crop)
if [ "$TRANSFORMATION" == "crop" ]; then
    CIRCUIT_FILE="circuits/optimized_crop_step_${RESOLUTION}.r1cs"
    WITNESS_GEN="circuits/optimized_crop_step_${RESOLUTION}_cpp/optimized_crop_step_${RESOLUTION}"
else
    CIRCUIT_FILE="circuits/${TRANSFORMATION}_step_${RESOLUTION}.r1cs"
    WITNESS_GEN="circuits/${TRANSFORMATION}_step_${RESOLUTION}_cpp/${TRANSFORMATION}_step_${RESOLUTION}"
fi

echo "========================================="
echo "Batch Proof Generation"
echo "========================================="
echo "Input directory: $FULL_INPUT_DIR"
echo "Output directory: $FULL_OUTPUT_DIR"
echo "Transformation: $TRANSFORMATION"
echo "Resolution: $RESOLUTION"
echo "========================================="

# Check if vimz binary exists
if ! command -v vimz &> /dev/null; then
    echo "Error: vimz command not found"
    echo "Please make sure vimz is in your PATH"
    exit 1
fi

# Count total files
TOTAL=$(find "$FULL_INPUT_DIR" -name "*.json" | wc -l)
echo "Found $TOTAL JSON file(s) to process"
echo ""

# Array to store all results
declare -a JSON_RESULTS

# Counter for progress
COUNT=0

# Process each JSON file
for json_file in "$FULL_INPUT_DIR"/*.json; do
    if [ -f "$json_file" ]; then
        COUNT=$((COUNT + 1))
        BASENAME=$(basename "$json_file" .json)
        OUTPUT_PROOF="$FULL_OUTPUT_DIR/${BASENAME}_proof.json"
        LOG_FILE="$FULL_OUTPUT_DIR/${BASENAME}_output.log"
        
        echo "[$COUNT/$TOTAL] Processing: $BASENAME"
        
        # Create a temporary file for time statistics (stderr from time command)
        TIME_STATS="$FULL_OUTPUT_DIR/${BASENAME}_time_stats.log"
        
        # Run vimz with time -v to capture memory usage
        # /usr/bin/time -v outputs statistics to stderr (file descriptor 2)
        # vimz outputs to stdout (file descriptor 1) and some to stderr (2)
        # We capture everything and separate later, or use a wrapper
        # Simple approach: capture all to log, then extract time stats from end
        (/usr/bin/time -v vimz \
            --circuit "$CIRCUIT_FILE" \
            --function "$TRANSFORMATION" \
            --input "$json_file" \
            --output "$OUTPUT_PROOF" \
            --resolution "$RESOLUTION" \
            --witnessgenerator "$WITNESS_GEN") \
            > "$LOG_FILE" 2> "$TIME_STATS"
        VIMZ_EXIT=$?
        
        # Combine time stats into the log file for easier viewing
        echo "" >> "$LOG_FILE"
        echo "=== Memory and Resource Statistics ===" >> "$LOG_FILE"
        cat "$TIME_STATS" >> "$LOG_FILE"
        
        if [ $VIMZ_EXIT -eq 0 ]; then
            echo "  ✓ Proof saved: ${BASENAME}_proof.json"
            
            # Extract metrics from log file
            KEY_GEN=$(grep "Creating keys from R1CS took" "$LOG_FILE" | grep -oP "took \K[0-9.]+" || echo "N/A")
            RECURSIVE_CREATE=$(grep "RecursiveSNARK creation took" "$LOG_FILE" | grep -oP "took \K[0-9.]+" || echo "N/A")
            RECURSIVE_VERIFY=$(grep "RecursiveSNARK::verify.*took" "$LOG_FILE" | grep -oP "took \K[0-9.]+" || echo "N/A")
            COMPRESSED_PROVE=$(grep "CompressedSNARK::prove.*took" "$LOG_FILE" | grep -oP "took \K[0-9.]+" || echo "N/A")
            COMPRESSED_VERIFY=$(grep "CompressedSNARK::verify.*took" "$LOG_FILE" | grep -oP "took \K[0-9.]+" || echo "N/A")
            
            # Extract additional metrics
            PRIMARY_CONSTRAINTS=$(grep "Number of constraints per step (primary circuit):" "$LOG_FILE" | grep -oP ": \K[0-9]+" || echo "N/A")
            PRIMARY_VARIABLES=$(grep "Number of variables per step (primary circuit):" "$LOG_FILE" | grep -oP ": \K[0-9]+" || echo "N/A")
            
            # Extract peak memory from time statistics (Maximum resident set size in kbytes)
            # Convert to MB for easier reading (divide by 1024)
            PEAK_MEMORY_KB=$(grep "Maximum resident set size (kbytes):" "$TIME_STATS" 2>/dev/null | grep -oP ":\s*\K[0-9]+" || echo "N/A")
            if [ "$PEAK_MEMORY_KB" != "N/A" ] && [ -n "$PEAK_MEMORY_KB" ]; then
                # Calculate MB (kb / 1024), round to 2 decimal places
                PEAK_MEMORY_MB=$(echo "scale=2; $PEAK_MEMORY_KB / 1024" | bc 2>/dev/null || echo "N/A")
            else
                PEAK_MEMORY_MB="N/A"
            fi
            
            # Clean up time stats file (optional, or keep for debugging)
            # rm -f "$TIME_STATS"
            
            # Create JSON object for this result
            JSON_RESULT=$(cat <<EOF
{
  "file": "$BASENAME",
  "input_json": "$json_file",
  "proof_file": "$OUTPUT_PROOF",
  "resolution": "$RESOLUTION",
  "transformation": "$TRANSFORMATION",
  "key_generation_time_s": "$KEY_GEN",
  "recursive_creation_time_s": "$RECURSIVE_CREATE",
  "recursive_verify_time_s": "$RECURSIVE_VERIFY",
  "compressed_prove_time_s": "$COMPRESSED_PROVE",
  "compressed_verify_time_s": "$COMPRESSED_VERIFY",
  "primary_constraints": "$PRIMARY_CONSTRAINTS",
  "primary_variables": "$PRIMARY_VARIABLES",
  "peak_memory_kb": "$PEAK_MEMORY_KB",
  "peak_memory_mb": "$PEAK_MEMORY_MB"
}
EOF
)
            
            # Add to results array
            JSON_RESULTS+=("$JSON_RESULT")
            
        else
            echo "  ✗ Failed to generate proof for $BASENAME"
        fi
        
        echo ""
    fi
done

# Save all results to JSON file
if [ ${#JSON_RESULTS[@]} -gt 0 ]; then
    echo "Saving results to $RESULTS_FILE..."
    
    # Create JSON array
    echo "[" > "$RESULTS_FILE"
    for i in "${!JSON_RESULTS[@]}"; do
        echo "${JSON_RESULTS[$i]}" >> "$RESULTS_FILE"
        if [ $i -lt $((${#JSON_RESULTS[@]} - 1)) ]; then
            echo "," >> "$RESULTS_FILE"
        fi
    done
    echo "]" >> "$RESULTS_FILE"
    
    echo "✓ Results saved to: $RESULTS_FILE"
fi

echo ""
echo "========================================="
echo "Batch processing complete!"
echo "Processed $COUNT file(s)"
echo "Proofs saved to: $FULL_OUTPUT_DIR"
echo "Results saved to: $RESULTS_FILE"
echo "========================================="

