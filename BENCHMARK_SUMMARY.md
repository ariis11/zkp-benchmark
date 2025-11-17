# Benchmark Summary: Veritas vs VIMz Zero-Knowledge Proof Systems

## Overview

This document provides a detailed summary of the benchmark experiments conducted on two zero-knowledge proof (ZKP) systems: **Veritas** (Plonky2-based) and **VIMz** (Circom-based). Both systems were evaluated on four image transformation operations using real HD passport images (720×1280 pixels, RGB source format).

## Test Dataset

- **Source Images**: 50 real HD passport images
- **Original Image Dimensions**: 720×1280 pixels (height × width)
- **Source Image Format**: RGB (3 channels per pixel)
- **Processing Format**: 
  - **Veritas**: Blur, Crop, Resize convert RGB to grayscale before processing; Grayscale keeps RGB input
  - **VIMz**: Processes RGB images directly (can handle both RGB and grayscale)
- **Image Type**: Real passport photographs

## Transformation Details

### 1. Blur Transformation

**Algorithm**: 3×3 box blur kernel (average of 9 neighboring pixels)

#### Veritas
- **Input Image**: 720×1280 pixels (grayscale, converted from RGB)
- **Output Image**: 720×1280 pixels (grayscale, full image)
- **JSON Blur Region**: Entire image excluding 1-pixel borders (rows 1-718, cols 1-1278) = ~917,004 pixels
  - The JSON files contain the fully blurred image (matching `blur.py` default behavior)
- **Circuit Verification Region** (varies by system):
  - **Laptop (4GB RAM)**: 80×80 pixel region (rows 1-80, cols 1-80) = 6,400 pixels
  - **Server (high RAM)**: 718×1278 pixel region (rows 1-718, cols 1-1278) = ~917,004 pixels (entire image excluding borders)
- **Processing**: Converts RGB to grayscale, then applies 3×3 box blur. The circuit verifies a subset of the blurred region based on available memory.
- **Circuit Variables**: 
  - Laptop: ~931,840 (720×1280 input + 80×80 blurred)
  - Server: ~1,839,204 (720×1280 input + 718×1278 blurred)
- **Note**: Border pixels (row 0, col 0 of each row) remain unchanged and are used as public inputs. The blur effect is subtle, with pixel values typically changing by 1-2 units. The JSON contains the full blurred image, but the circuit only verifies a region limited by memory constraints.

#### VIMz
- **Input Image**: 720×1280 pixels (RGB, compressed format: 10 pixels per hex value)
- **Output Image**: 720×1280 pixels (RGB, full image)
- **Blur Region**: Entire image blur (all pixels except borders)
- **Processing**: Applies 3×3 box blur convolution to every pixel in the image (excluding 1-pixel border due to padding)
- **Blurred Pixels**: ~(720-2) × (1280-2) = 718 × 1278 = 917,004 pixels
- **Data Format**: Compressed hex representation (128 hex values per row for HD)
- **Padding**: Original image is padded with zero rows at top and bottom for convolution

**Key Difference**: 
- **Veritas Circuit Verification**:
  - **Laptop (4GB RAM)**: Verifies 80×80 = 6,400 pixels (0.7% of blurred region, limited by memory)
  - **Server (high RAM)**: Verifies 718×1278 = ~917,004 pixels (100% of blurred region, matches VIMz)
- **VIMz**: Always verifies entire blurred image (~917,004 pixels, ~99.5% of total image)
- **Comparison**:
  - **Laptop**: VIMz processes ~143× more pixels than Veritas (917,004 vs 6,400)
  - **Server**: VIMz and Veritas process the same number of pixels (~917,004)
- **Visual Impact**: Both produce subtle blur effects (1-2 pixel value changes on average), making differences barely noticeable when viewing the raw JSON data

---

### 2. Crop Transformation

**Algorithm**: Extract a rectangular region from the original image

#### Veritas
- **Input Image**: 720×1280 pixels (grayscale, converted from RGB)
- **Output Image**: 640×480 pixels (grayscale, cropped region)
- **JSON Crop Region**: 640×480 pixels (640 columns × 480 rows)
- **JSON Crop Position**: Top-left at (236, 105) - matching VIMz
- **Exact Intervals**: Rows [105, 584], Columns [236, 875] (inclusive)
- **Circuit Verification**: Verifies cropped region (640×480 = 307,200 pixels)
- **Circuit Variables**: 307,200 (NEW_SIZE = cropped image size)
- **Data Format**: Uncompressed pixel arrays (stores both original and cropped)
- **Note**: JSON and circuit match - both process the same 640×480 crop region as VIMz

#### VIMz (optimized_crop)
- **Input Image**: 720×1280 pixels (RGB, compressed hex format: 10 pixels per hex value)
- **Circuit Verification**: Verifies fixed region crop (hardcoded, ignores JSON)
  - **Crop Region**: 640×480 pixels (640 columns × 480 rows)
  - **Crop Position**: Top-left at (236, 105) - hardcoded in circuit
  - **Exact Intervals**: Rows [105, 584], Columns [236, 875] (inclusive)
  - **Total Pixels**: 307,200 pixels (33.3% of full image)
- **Circuit Parameters**: `CropHash(128, 64, 480, 236, 105)` - all parameters hardcoded
- **Data Format**: Compressed hex representation (only stores original, circuit extracts crop on-the-fly)
- **Note**: JSON `info` field (would indicate crop_x=0, crop_y=0) is completely ignored. Circuit always crops the same fixed region regardless of JSON content.

**Key Differences**: 
- **Circuit Approach**:
  - **Veritas**: Single circuit verifies entire crop in one go
  - **VIMz**: Folding-based, processes row-by-row (720 iterations)
- **Data Storage**:
  - **Veritas**: Stores both original and cropped arrays (uncompressed)
  - **VIMz**: Stores only original array (compressed hex), circuit extracts crop on-the-fly

---

### 3. Resize Transformation

**Algorithm**: Image downscaling using interpolation

#### Veritas
- **Input Image**: 720×1280 pixels (grayscale, converted from RGB, height × width)
- **Output Image** (varies by system):
  - **4GB RAM System**: 360×480 pixels (720→360 height, 1280→480 width)
  - **Server (high RAM)**: 480×640 pixels (720→480 height, 1280→640 width) - matches VIMz
- **Algorithm**: Standard bilinear interpolation
  - For each output pixel, calculates fractional source positions and uses 4 corner pixels
  - Formula: weighted average of 4 corner pixels based on fractional distances
- **Circuit Variables**:
  - **4GB System**: 691,200 (360×480×4 corner pixels)
  - **Server**: 1,228,800 (480×640×4 corner pixels)
- **Data Format**: Uncompressed pixel arrays (stores both original and resized)
- **Note**: 4GB system uses 360×480 to fit memory constraints. Server uses 480×640 matching VIMz.

#### VIMz
- **Input Image**: 720×1280 pixels (RGB, height × width)
- **Output Image**: 480×640 pixels (RGB, 720→480 height, 1280→640 width)
- **Algorithm**: Simplified weighted average (NOT standard bilinear)
  - Uses integer source positions (not fractional)
  - Fixed weights based on row parity (alternates between 2/3 and 1/3)
  - Uses 2 input pixels per output pixel horizontally
- **Circuit Template**: `ResizeHash(128, 64, 3, 2)` - processes 3 input rows → 2 output rows iteratively
- **Data Format**: Compressed hex representation (10 pixels per hex value)
- **Processing**: Folding-based (row-by-row iteration)

**Key Differences**:
- **Output Size**:
  - **Veritas (4GB)**: 360×480 = 172,800 pixels
  - **Veritas (Server)**: 480×640 = 307,200 pixels (matches VIMz)
  - **VIMz**: 480×640 = 307,200 pixels
- **Algorithm**:
  - **Veritas**: Standard bilinear interpolation (4 corner pixels, fractional positions)
  - **VIMz**: Simplified weighted average (2 pixels, integer positions, fixed weights)
- **Input Format**: Veritas uses grayscale (1 channel), VIMz uses RGB (3 channels)
- **Data Format**: Veritas uses uncompressed arrays, VIMz uses compressed hex (10 pixels/hex)
- **Circuit**: Veritas verifies entire resize at once; VIMz uses folding (row-by-row)

---

### 4. Grayscale Transformation

**Algorithm**: RGB to grayscale conversion using ITU-R BT.601 formula

#### Veritas
- **Input Image**: 720×1280 pixels (RGB, full image)
- **Output Image** (varies by system):
  - **4GB RAM System**: 480×640 pixels (grayscale, top-left region)
  - **Server (high RAM)**: 720×1280 pixels (grayscale, full image)
- **JSON Processing Region**:
  - **4GB System**: 480×640 pixels (top-left region) = 307,200 pixels
  - **Server**: 720×1280 pixels (full image) = 921,600 pixels
- **JSON Format**: 
  - `original`: [[[R,G,B], ...], ...] (uncompressed)
  - `grayscale`: [[value, ...], ...] (uncompressed)
- **Formula**: (299×R + 587×G + 114×B) // 1000 (integer division)
- **Circuit Verification**: 
  - Reads dimensions dynamically from JSON
  - Computes `sum = 299×R + 587×G + 114×B` for each pixel
  - Verifies exact sum matches expected calculation
- **Circuit Variables**:
  - **4GB System**: 921,600 (480×640 pixels × 3 RGB channels)
  - **Server**: 2,764,800 (720×1280 pixels × 3 RGB channels)
- **Circuit Approach**: Single circuit verifies all pixels at once
- **Data Format**: Uncompressed pixel arrays

#### VIMz
- **Input Image**: 720×1280 pixels (RGB, full image)
- **Output Image**: 720×1280 pixels (grayscale, full image)
- **JSON Processing Region**: Full image (720×1280 pixels)
- **JSON Format**:
  - `original`: [[hex_value, ...], ...] (720 rows, 128 hex values per row)
  - `transformed`: [[hex_value, ...], ...] (720 rows, 128 hex values per row)
  - Each hex value = 10 pixels (compressed format)
- **Formula**: PIL `convert('L')` uses ITU-R BT.601
  - Equivalent to (299×R + 587×G + 114×B) / 1000 (floating point, then rounded)
- **Circuit Template**: `GrayScaleHash(128)`
  - `width = 128` (compressed hex values per row)
  - Each hex = 10 pixels → 1280 pixels per row
  - Processes all 720 rows (full image)
- **Circuit Verification**:
  - For each pixel: computes `inter = 299×orig[i][0] + 587×orig[i][1] + 114×orig[i][2]`
  - Checks: `|inter - 1000×gray[i]| <= 1000` (allows ±1 pixel rounding error)
  - Checks: `|1000×gray[i] - inter| <= 1000`
- **Circuit Approach**: Folding-based, processes row-by-row (720 iterations)
- **Data Format**: Compressed hex representation (10 pixels per hex value)
- **Total Pixels**: 720 × 1280 = 921,600 pixels

**Key Differences**:
- **Processing Region**:
  - **Veritas (4GB)**: 480×640 = 307,200 pixels (top-left region)
  - **Veritas (Server)**: 720×1280 = 921,600 pixels (full image, matches VIMz)
  - **VIMz**: 720×1280 = 921,600 pixels (full image)
  - **Ratio**: VIMz processes 3× more pixels than Veritas on 4GB systems
- **Formula Implementation**:
  - **Veritas**: Integer division `//` (exact)
  - **VIMz**: PIL floating point then rounded (may differ by ±1)
- **Circuit Verification**:
  - **Veritas**: Verifies exact sum
  - **VIMz**: Allows ±1000 rounding error (equivalent to ±1 pixel value)
- **Circuit Approach**: Veritas uses single circuit; VIMz uses folding (row-by-row)
- **Data Format**: Veritas uses uncompressed arrays; VIMz uses compressed hex (10 pixels/hex)

---

## System-Specific Characteristics

### Veritas (Plonky2)
- **ZKP Framework**: Plonky2 (Rust implementation)
- **Proof System**: Single-phase proof (no separate compressed SNARK phase)
- **Data Format**: Uncompressed pixel arrays (direct pixel values)
- **Memory Constraints**: Required reduction of processing regions for resize and grayscale due to circuit size limitations
- **Circuit Representation**: Direct arithmetic circuits over field elements

### VIMz (Circom)
- **ZKP Framework**: Circom (R1CS constraint system)
- **Proof System**: Two-phase proof (RecursiveSNARK + CompressedSNARK)
- **Data Format**: Compressed hex representation (10 pixels per hex value for efficiency)
- **Memory Efficiency**: Can process full images due to compressed data format
- **Circuit Representation**: R1CS constraints with hash-based verification

---

## Benchmark Metrics Collected

For each transformation, the following metrics were collected:

1. **Circuit Build Time** (Key Generation): Time to construct the ZKP circuit
2. **Number of Constraints**: Total constraint count in the circuit
3. **Number of Variables**: Total variable count in the circuit
4. **Proof Generation Time**: Time to generate the zero-knowledge proof
5. **Verification Time**: Time to verify the generated proof
6. **Peak Memory Usage**: Maximum resident set size during proof generation
7. **CompressedSNARK Time** (VIMz only): Time for compressed proof phase (N/A for Veritas)

---

## Experimental Setup

- **Hardware**: Standard benchmarking environment
- **Images**: 50 real HD passport images (720×1280 pixels)
- **Repetitions**: Single run per image (50 total proofs per transformation)
- **Measurement Tool**: `/usr/bin/time -v` for resource usage statistics
- **Output Format**: JSON files containing aggregated performance metrics

---

## Notes for Scientific Comparison

1. **Processing Scale Differences**: Veritas processes smaller regions on 4GB systems (80×80 blur region, 360×480 resize, 480×640 grayscale) compared to VIMz (full image) due to memory constraints. For resize, Veritas on 4GB outputs 360×480 (172,800 pixels) while VIMz outputs 480×640 (307,200 pixels) - a 1.78× difference. For grayscale, Veritas on 4GB processes 480×640 (307,200 pixels) while VIMz processes 720×1280 (921,600 pixels) - a 3× difference. On server systems, Veritas matches VIMz with 480×640 output for resize and 720×1280 for grayscale. This should be considered when comparing absolute performance metrics.

2. **Data Format Impact**: VIMz uses compressed hex representation (10 pixels/hex), while Veritas uses uncompressed pixel arrays. This affects memory usage and may impact proof generation times.

3. **Proof System Architecture**: VIMz uses a two-phase proof system (RecursiveSNARK + CompressedSNARK), while Veritas uses a single-phase proof. The "CompressedSNARK" metric is N/A for Veritas.

4. **Fair Comparison**: When comparing metrics, consider:
   - Different processing scales (region vs. full image)
   - Different data representations (compressed vs. uncompressed)
   - Different proof system architectures (two-phase vs. single-phase)

5. **Memory Constraints**: Veritas on 4GB systems required dimension reductions for resize (360×480 instead of 480×640) and grayscale (480×640 region instead of full 720×1280) to fit available memory, indicating higher memory requirements for large circuits. On server systems with sufficient RAM, Veritas matches VIMz's output dimensions (480×640 for resize, 720×1280 for grayscale).

6. **Algorithm Differences**: For resize, Veritas uses standard bilinear interpolation with fractional position calculations, while VIMz uses a simplified weighted average with fixed weights based on row parity. This fundamental algorithmic difference means the two systems produce different interpolation results even for the same input image.

---

## Summary Table

| Transformation | Veritas Input | Veritas Output | VIMz Input | VIMz Output | Key Difference |
|---------------|--------------|----------------|------------|-------------|----------------|
| **Blur** | 720×1280 | 720×1280 | 720×1280 | 720×1280 | Veritas: 80×80 (4GB) / 718×1278 (server); VIMz: full image |
| **Crop** | 720×1280 | 640×480 | 720×1280 | 640×480 | Both: same crop region (236, 105, 640×480) |
| **Resize** | 720×1280 (HD) | 360×480 (4GB) / 480×640 (server) | 720×1280 (HD) | 480×640 (SD) | Veritas: std bilinear; VIMz: simplified weighted avg |
| **Grayscale** | 720×1280 (RGB) | 480×640 (4GB) / 720×1280 (server) | 720×1280 (RGB) | 720×1280 (Gray) | Veritas: 480×640 (4GB) / 720×1280 (server); VIMz: full image; Veritas: exact sum; VIMz: allows ±1 rounding |

---

*This summary provides the necessary details for scientific comparison and analysis of the two ZKP systems' performance on image transformation proofs.*

