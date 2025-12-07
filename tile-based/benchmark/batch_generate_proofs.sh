#!/bin/bash

# Batch generate proofs and extract timing metrics for Veritas
# This script processes all JSON files in a directory and collects performance data

# Get the script directory and go to parent (tile-based root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."  # Go to tile-based root

TILE_BASED_ROOT="$(pwd)"

# Get parameters - they should be relative to TILE_BASED_ROOT
INPUT_DIR="${1:-benchmark/grayscale/outputs_hd}"  # Default to outputs_hd
OUTPUT_DIR="${2:-benchmark/grayscale/proofs}"     # Default to proofs directory
TRANSFORMATION="${3:-grayscale}"                  # Transformation type (grayscale, blur, crop, resize, etc.)

# Construct full paths
FULL_INPUT_DIR="$TILE_BASED_ROOT/$INPUT_DIR"
FULL_OUTPUT_DIR="$TILE_BASED_ROOT/$OUTPUT_DIR"

# Set results file based on transformation
RESULTS_FILE="$TILE_BASED_ROOT/benchmark/${TRANSFORMATION}/performance_results.json"

# Create directories
mkdir -p "$FULL_OUTPUT_DIR"

echo "========================================="
echo "Batch Proof Generation (Tile-Based)"
echo "========================================="
echo "Input directory: $FULL_INPUT_DIR"
echo "Output directory: $FULL_OUTPUT_DIR"
echo "Transformation: $TRANSFORMATION"
echo "========================================="

# Count total files
TOTAL=$(find "$FULL_INPUT_DIR" -name "*.json" 2>/dev/null | wc -l)

if [ "$TOTAL" -eq 0 ]; then
    echo "Error: No JSON files found in $FULL_INPUT_DIR"
    exit 1
fi

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
        TIME_STATS="$FULL_OUTPUT_DIR/${BASENAME}_time_stats.log"
        
        echo "[$COUNT/$TOTAL] Processing: $BASENAME"
        
        # Map transformation name to example name
        # Template for future transformations - add cases as needed
        if [ "$TRANSFORMATION" == "grayscale" ] || [ "$TRANSFORMATION" == "gray" ]; then
            EXAMPLE_NAME="gray-benchmark"
        # elif [ "$TRANSFORMATION" == "blur" ]; then
        #     EXAMPLE_NAME="blur-benchmark"
        # elif [ "$TRANSFORMATION" == "crop" ]; then
        #     EXAMPLE_NAME="crop-benchmark"
        # elif [ "$TRANSFORMATION" == "resize" ]; then
        #     EXAMPLE_NAME="resize-benchmark"
        else
            echo "  ✗ Unknown transformation: $TRANSFORMATION"
            echo "  Supported transformations: grayscale"
            echo "  Note: Other transformations are planned for future implementation"
            continue
        fi
        
        # Optional: pass tile_height as argument (default is 64 in the code)
        TILE_HEIGHT="${4:-64}"
        
        # Run tile-based with time -v to capture memory usage
        # Capture stdout to log file and stderr (time stats) to separate file
        # Pass tile_height as optional second argument
        (/usr/bin/time -v cargo run --release --example "$EXAMPLE_NAME" -- "$json_file" "$TILE_HEIGHT" 2>&1) \
            > "$LOG_FILE" 2> "$TIME_STATS"
        VERITAS_EXIT=$?
        
        # Combine time stats into the log file for easier viewing (if file exists)
        if [ -f "$TIME_STATS" ]; then
            echo "" >> "$LOG_FILE"
            echo "=== Memory and Resource Statistics ===" >> "$LOG_FILE"
            cat "$TIME_STATS" >> "$LOG_FILE"
        fi
        
        # Check for OOM kill (exit code 137 = 128 + 9 (SIGKILL))
        if [ $VERITAS_EXIT -eq 137 ] || ([ -f "$TIME_STATS" ] && grep -q "Command terminated by signal 9" "$TIME_STATS" 2>/dev/null); then
            echo "  ✗ Process killed (OOM) - circuit too large for available memory"
            echo "  Note: Resize circuit requires ~5-6GB+ RAM for HD→SD transformation"
            
            # Still extract what we can from the log (if time stats file exists)
            if [ -f "$TIME_STATS" ]; then
                PEAK_MEMORY_KB=$(grep "Maximum resident set size (kbytes):" "$TIME_STATS" 2>/dev/null | grep -oP ":\s*\K[0-9]+" || echo "N/A")
            else
                PEAK_MEMORY_KB="N/A"
            fi
            if [ "$PEAK_MEMORY_KB" != "N/A" ] && [ -n "$PEAK_MEMORY_KB" ]; then
                PEAK_MEMORY_MB=$(echo "scale=2; $PEAK_MEMORY_KB / 1024" | bc 2>/dev/null || echo "N/A")
            else
                PEAK_MEMORY_MB="N/A"
            fi
            
            # Create JSON object for failed result
            JSON_RESULT=$(cat <<EOF
{
  "file": "$BASENAME",
  "input_json": "$json_file",
  "proof_file": "N/A (OOM)",
  "transformation": "$TRANSFORMATION",
  "circuit_build_time_s": "N/A (killed before completion)",
  "proof_generation_time_s": "N/A",
  "verification_time_ms": "N/A",
  "constraints": "N/A",
  "variables": "N/A",
  "compressed_snark": "N/A (Plonky2 single-phase)",
  "peak_memory_kb": "$PEAK_MEMORY_KB",
  "peak_memory_mb": "$PEAK_MEMORY_MB",
  "error": "OOM (Out of Memory) - circuit too large"
}
EOF
)
            JSON_RESULTS+=("$JSON_RESULT")
            continue
        fi
        
        if [ $VERITAS_EXIT -eq 0 ]; then
            echo "  ✓ Proof generated for ${BASENAME}"
            
            # Extract metrics from log file (tile-based specific)
            # Note: Metrics extraction is transformation-agnostic, but can be customized per transformation if needed
            CIRCUIT_BUILD=$(grep "Circuit build took" "$LOG_FILE" | grep -oP "took \K[0-9.]+" || echo "N/A")
            
            # Tile-based has total and average proof times
            TOTAL_PROOF_GEN=$(grep "Total proof generation time:" "$LOG_FILE" | grep -oP "time: \K[0-9.]+" || echo "N/A")
            AVG_PROOF_GEN=$(grep "Average proof time per tile:" "$LOG_FILE" | grep -oP "time: \K[0-9.]+" || echo "N/A")
            # Fallback to old format if new format not found (for backward compatibility)
            if [ "$TOTAL_PROOF_GEN" == "N/A" ]; then
                TOTAL_PROOF_GEN=$(grep "Proof generation took" "$LOG_FILE" | grep -oP "took \K[0-9.]+" || echo "N/A")
            fi
            
            TOTAL_VERIFY=$(grep "Total verification time:" "$LOG_FILE" | grep -oP "time: \K[0-9.]+" || echo "N/A")
            AVG_VERIFY=$(grep "Average verification time per tile:" "$LOG_FILE" | grep -oP "time: \K[0-9.]+" || echo "N/A")
            # Fallback to old format if new format not found (for backward compatibility)
            if [ "$TOTAL_VERIFY" == "N/A" ]; then
                TOTAL_VERIFY=$(grep "Verification took" "$LOG_FILE" | grep -oP "took \K[0-9.]+" || echo "N/A")
            fi
            
            # Extract tile-specific metrics
            NUM_TILES=$(grep "Total tiles processed:" "$LOG_FILE" | grep -oP ": \K[0-9]+" || echo "N/A")
            TILE_VARIABLES=$(grep "Variables per tile:" "$LOG_FILE" | grep -oP "tile: \K[0-9]+" || echo "N/A")
            
            # Extract constraints and variables
            CONSTRAINTS=$(grep "Number of constraints:" "$LOG_FILE" | grep -oP ": \K[0-9]+" || echo "N/A")
            VARIABLES=$(grep "Number of variables per tile:" "$LOG_FILE" | grep -oP "tile: \K[0-9]+" || echo "$TILE_VARIABLES")
            
            # Extract peak memory from time statistics (Maximum resident set size in kbytes)
            PEAK_MEMORY_KB=$(grep "Maximum resident set size (kbytes):" "$TIME_STATS" 2>/dev/null | grep -oP ":\s*\K[0-9]+" || echo "N/A")
            if [ "$PEAK_MEMORY_KB" != "N/A" ] && [ -n "$PEAK_MEMORY_KB" ]; then
                # Calculate MB (kb / 1024), round to 2 decimal places
                PEAK_MEMORY_MB=$(echo "scale=2; $PEAK_MEMORY_KB / 1024" | bc 2>/dev/null || echo "N/A")
            else
                PEAK_MEMORY_MB="N/A"
            fi
            
            # Create JSON object for this result (tile-based structure)
            JSON_RESULT=$(cat <<EOF
{
  "file": "$BASENAME",
  "input_json": "$json_file",
  "proof_file": "$OUTPUT_PROOF",
  "transformation": "$TRANSFORMATION",
  "tile_height": "$TILE_HEIGHT",
  "num_tiles": "$NUM_TILES",
  "circuit_build_time_s": "$CIRCUIT_BUILD",
  "total_proof_generation_time_s": "$TOTAL_PROOF_GEN",
  "average_proof_time_per_tile_s": "$AVG_PROOF_GEN",
  "total_verification_time_ms": "$TOTAL_VERIFY",
  "average_verification_time_per_tile_ms": "$AVG_VERIFY",
  "constraints": "$CONSTRAINTS",
  "variables_per_tile": "$VARIABLES",
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
    
    # Create output directory if needed
    mkdir -p "$(dirname "$RESULTS_FILE")"
    
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
echo "Logs saved to: $FULL_OUTPUT_DIR"
echo "Results saved to: $RESULTS_FILE"
echo "========================================="

