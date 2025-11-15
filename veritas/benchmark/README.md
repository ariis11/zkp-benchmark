# Veritas Benchmark Workflow

This directory contains scripts for the complete Veritas benchmarking workflow: image conversion and proof generation.

## Structure

```
benchmark/
├── batch_convert.sh          # Convert images to JSON format
├── batch_generate_proofs.sh  # Generate proofs and collect metrics
├── blur/
│   ├── blur.py              # Blur transformation converter
│   └── outputs_hd/          # Converted JSON files
└── passports_hd/            # Original PNG images
```

## Workflow

### Step 1: Convert Images to JSON

Convert all images in `passports_hd` to blur JSON format:

```bash
cd veritas/benchmark
./batch_convert.sh blur passports_hd blur/outputs_hd
```

This creates JSON files in `blur/outputs_hd/` with original and transformed image data.

### With Custom Blur Region

Specify a custom blur region (start_row start_col height width):

```bash
./batch_convert.sh blur passports_hd blur/outputs_hd --blur-region 1 1 6 6
```

This will blur only a 6×6 region starting at position [1,1].

### Output Format

Each JSON file contains:
```json
{
  "original": [[pixel values...], ...],
  "blurred": [[pixel values...], ...],
  "height": 720,
  "width": 1280,
  "blur_region": null,
  "resolution": "HD"
}
```

## Adding New Transformations

To add a new transformation (e.g., resize, crop):

1. Create a new directory: `benchmark/resize/`
2. Create converter script: `benchmark/resize/resize.py`
3. Add case to `batch_convert.sh`:
   ```bash
   elif [ "$TRANSFORMATION" == "resize" ]; then
       OUTPUT_FILE="$FULL_OUTPUT_DIR/${BASENAME}.json"
       python3 "$SCRIPT_DIR/resize/resize.py" \
           -i "$img" \
           -o "$OUTPUT_FILE" \
           -r HD
   ```

### Step 2: Generate Proofs and Collect Metrics

Generate proofs for all JSON files and collect performance metrics:

```bash
cd veritas/benchmark
./batch_generate_proofs.sh blur/outputs_hd blur/proofs blur
```

This will:
- Process each JSON file in `blur/outputs_hd/`
- Generate proofs using `blur-benchmark` example
- Save logs to `blur/proofs/`
- Extract metrics (timing, constraints, variables, memory)
- Save results to `blur/performance_results.json`

### Output Metrics

The script extracts the following metrics (matching VIMz format):
- Circuit build time (equivalent to VIMz "Key Generation")
- Proof generation time (equivalent to VIMz "RecursiveSNARK creation")
- Verification time (equivalent to VIMz "RecursiveSNARK verify")
- Number of constraints
- Number of variables
- Peak memory usage (KB and MB)
- CompressedSNARK: N/A (Plonky2 uses single-phase proof)

## Requirements

- Python 3
- PIL (Pillow): `pip install Pillow`
- NumPy: `pip install numpy`
- Rust and Cargo (for building veritas)
- `/usr/bin/time` (for memory statistics)

