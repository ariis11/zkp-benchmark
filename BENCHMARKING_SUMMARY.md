# Benchmarking Workflow Summary

## Overview

**VIMz**, **Veritas**, and **Tile-Based** follow a 2-step benchmarking process:
1. **Convert images to JSON** (prepare input data)
2. **Generate proofs** (run ZK proofs and collect metrics)

---

## VIMz Benchmarking

### Step 1: Convert Images to JSON

**Location:** `vimz/benchmark/`

**Command:**
```bash
cd vimz/benchmark
./batch_convert.sh <transformation> <input_dir> <output_dir> [params]
```

**Examples:**
- **Resize:** `./batch_convert.sh resize ../../assets/passports_hd resize/outputs_hd`
- **Grayscale:** `./batch_convert.sh grayscale ../../assets/passports_hd grayscale/outputs_hd`
- **Blur:** `./batch_convert.sh blur ../../assets/passports_hd blur/outputs_hd`
- **Crop:** `./batch_convert.sh crop ../../assets/passports_hd crop/outputs_hd`
- **Contrast:** `./batch_convert.sh contrast ../../assets/passports_hd contrast/outputs_hd 1.5`

**Outcome:**
- Creates JSON files in `vimz/benchmark/<transformation>/outputs_hd/` containing original and transformed image data
- Each JSON file: `passport_XXXX.json`

---

### Step 2: Generate Proofs

**Command:**
```bash
cd vimz/benchmark
./batch_generate_proofs.sh <input_dir> <output_dir> <transformation> <resolution>
```

**Examples:**
- **Resize:** `./batch_generate_proofs.sh benchmark/resize/outputs_hd benchmark/resize/proofs resize HD`
- **Grayscale:** `./batch_generate_proofs.sh benchmark/grayscale/outputs_hd benchmark/grayscale/proofs grayscale HD`
- **Blur:** `./batch_generate_proofs.sh benchmark/blur/outputs_hd benchmark/blur/proofs blur HD`
- **Crop:** `./batch_generate_proofs.sh benchmark/crop/outputs_hd benchmark/crop/proofs crop HD`

**Outcome:**
- Generates proof files: `vimz/benchmark/<transformation>/proofs/passport_XXXX_proof.json`
- Creates log files: `vimz/benchmark/<transformation>/proofs/passport_XXXX_output.log`
- Saves metrics JSON: `vimz/benchmark/<transformation>/performance_results.json`

**Metrics Collected:**
- Key generation time
- RecursiveSNARK creation time
- RecursiveSNARK verify time
- CompressedSNARK prove/verify time
- Constraints and variables (primary/secondary circuits)
- Peak memory usage (KB, MB)

---

### Optional: Extract Metrics to CSV

**Command:**
```bash
python3 extract_vimz_metrics.py <proofs_directory> [output_csv]
```

**Example:**
```bash
python3 extract_vimz_metrics.py vimz/benchmark/blur/proofs_laptop_hd
```

**Outcome:**
- Creates CSV file: `<proofs_directory>_metrics.csv` with all extracted metrics

---

## Veritas Benchmarking

### Step 1: Convert Images to JSON

**Location:** `veritas/benchmark/`

**Command:**
```bash
cd veritas/benchmark
./batch_convert.sh <transformation> <input_dir> <output_dir> [params]
```

**Examples:**
- **Blur:** `./batch_convert.sh blur ../../assets/passports_hd blur/outputs_hd`
- **Blur (custom region):** `./batch_convert.sh blur ../../assets/passports_hd blur/outputs_hd --blur-region 1 1 6 6`
- **Crop:** `./batch_convert.sh crop ../../assets/passports_hd crop/outputs_hd`
- **Resize:** `./batch_convert.sh resize ../../assets/passports_hd resize/outputs_hd`
- **Grayscale:** `./batch_convert.sh grayscale ../../assets/passports_hd grayscale/outputs_hd`

**Outcome:**
- Creates JSON files in `veritas/benchmark/<transformation>/outputs_hd/` containing original and transformed image data
- Each JSON file: `passport_XXXX.json`

---

### Step 2: Generate Proofs

**Command:**
```bash
cd veritas/benchmark
./batch_generate_proofs.sh <input_dir> <output_dir> <transformation>
```

**Examples:**
- **Blur:** `./batch_generate_proofs.sh benchmark/blur/outputs_hd benchmark/blur/proofs blur`
- **Crop:** `./batch_generate_proofs.sh benchmark/crop/outputs_hd benchmark/crop/proofs crop`
- **Resize:** `./batch_generate_proofs.sh benchmark/resize/outputs_hd benchmark/resize/proofs resize`
- **Grayscale:** `./batch_generate_proofs.sh benchmark/grayscale/outputs_hd benchmark/grayscale/proofs grayscale`

**Outcome:**
- Creates log files: `veritas/benchmark/<transformation>/proofs/passport_XXXX_output.log`
- Saves metrics JSON: `veritas/benchmark/<transformation>/performance_results.json`
- Note: Veritas uses Plonky2 (single-phase proof), no separate proof files

**Metrics Collected:**
- Circuit build time (equivalent to VIMz key generation)
- Proof generation time (equivalent to VIMz RecursiveSNARK creation)
- Verification time
- Constraints and variables
- Peak memory usage (KB, MB)

---

### Optional: Extract Metrics to CSV

**Command:**
```bash
python3 extract_veritas_metrics.py <proofs_directory> [output_csv]
```

**Example:**
```bash
python3 extract_veritas_metrics.py veritas/benchmark/blur/proofs_laptop_hd
```

**Outcome:**
- Creates CSV file: `<proofs_directory>_metrics.csv` with all extracted metrics

---

## Tile-Based Benchmarking

### Step 1: Convert Images to JSON

**Location:** `tile-based/benchmark/`

**Command:**
```bash
cd tile-based/benchmark
./batch_convert.sh <transformation> <input_dir> <output_dir> [params]
```

**Examples:**
- **Grayscale:** `./batch_convert.sh grayscale ../../assets/passports_hd grayscale/outputs_hd`

**Outcome:**
- Creates JSON files in `tile-based/benchmark/<transformation>/outputs_hd/` containing original and transformed image data
- Each JSON file: `passport_XXXX.json`

---

### Step 2: Generate Proofs

**Command:**
```bash
cd tile-based/benchmark
./batch_generate_proofs.sh <input_dir> <output_dir> <transformation> [tile_height]
```

**Examples:**
- **Grayscale:** `./batch_generate_proofs.sh benchmark/grayscale/outputs_hd benchmark/grayscale/proofs_laptop_hd grayscale 64`

**Outcome:**
- Creates log files: `tile-based/benchmark/<transformation>/proofs/passport_XXXX_output.log`
- Saves metrics JSON: `tile-based/benchmark/<transformation>/performance_results.json`
- Note: Tile-Based uses Plonky2 with tiling strategy (multiple proofs per image, one per tile)

**Metrics Collected:**
- Circuit build time (once, reused for all tiles)
- Total proof generation time (sum of all tiles)
- Average proof time per tile
- Total verification time
- Average verification time per tile
- Number of tiles
- Constraints and variables per tile
- Peak memory usage (KB, MB)

**Key Feature:**
- Generates **N proofs per image** (one per tile) instead of 1 proof per image
- Much lower memory usage: variables per tile (~245K) vs full image (~2.7M)
- Enables running on resource-constrained systems (8GB laptops)

---

### Optional: Extract Metrics to CSV

**Command:**
```bash
python3 extract_tile_metrics.py <proofs_directory> [output_csv]
```

**Example:**
```bash
python3 extract_tile_metrics.py tile-based/benchmark/grayscale/proofs_laptop_hd
```

**Outcome:**
- Creates CSV file: `<proofs_directory>_metrics.csv` with all extracted metrics

---

## Key Differences

| Aspect | VIMz | Veritas | Tile-Based |
|--------|------|---------|------------|
| **Proof System** | Nova (RecursiveSNARK + CompressedSNARK) | Plonky2 (single-phase) | Plonky2 (tiled, single-phase) |
| **Output Files** | Proof JSON + Log files | Log files only | Log files only |
| **Metrics** | 2-phase proof times | Single-phase proof times | Single-phase + per-tile metrics |
| **Circuits** | Uses `.r1cs` files | Built at runtime | Built at runtime (tile size) |
| **Witness Generator** | C++ compiled binaries | N/A (built-in) | N/A (built-in) |
| **Proofs per Image** | 1 | 1 | N (one per tile) |
| **Memory Usage** | Medium | High (full image) | Low (per tile) |

| Aspect | VIMz | Veritas |
|--------|------|---------|
| **Proof System** | Nova (RecursiveSNARK + CompressedSNARK) | Plonky2 (single-phase) |
| **Output Files** | Proof JSON + Log files | Log files only |
| **Metrics** | 2-phase proof times | Single-phase proof times |
| **Circuits** | Uses `.r1cs` files | Built at runtime |
| **Witness Generator** | C++ compiled binaries | N/A (built-in) |

---

## Supported Transformations

**VIMz:** resize, grayscale, blur, crop, contrast, brightness, sharpness

**Veritas:** blur, crop, resize, grayscale

**Tile-Based:** grayscale (blur, crop, resize planned for future)

---

## Input Requirements

- **Images:** PNG files in `assets/passports_hd/` directory at project root (50 passport images)
- **Resolution:** HD (1280×720) by default
- **Tools:** Python 3, Rust/Cargo, `/usr/bin/time` for memory stats

## Important Notes

- **Image Location:** All passport images are stored in `assets/passports_hd/` at the project root, not in individual benchmark directories
- **Path Reference:** When running commands from `vimz/benchmark/`, `veritas/benchmark/`, or `tile-based/benchmark/`, use `../../assets/passports_hd` to reference the images
- **Output Structure:** Each transformation creates its own subdirectory with `outputs_hd/` (JSON files) and `proofs/` (proof/log files)
- **Tile-Based Specific:** Uses tiling strategy to reduce memory usage. Default tile height is 64 rows, configurable via command-line argument





