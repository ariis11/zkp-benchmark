# Veritas Benchmark Image Conversion

This directory contains scripts to prepare image data for Veritas proof generation.

## Structure

```
benchmark/
├── batch_convert.sh      # Main batch conversion script
├── blur/
│   └── blur.py          # Blur transformation converter
└── passports_hd/        # Original PNG images
```

## Usage

### Basic Usage

Convert all images in `passports_hd` to blur JSON format:

```bash
cd veritas/benchmark
./batch_convert.sh blur passports_hd blur/outputs_hd
```

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

## Requirements

- Python 3
- PIL (Pillow): `pip install Pillow`
- NumPy: `pip install numpy`

