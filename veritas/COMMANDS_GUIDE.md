# VerITAS - Step-by-Step Command Guide

This guide will walk you through running the VerITAS system from scratch.

## Prerequisites

1. **Python 3** - For generating test images
2. **Rust & Cargo** - For compiling and running the proof system
3. **Navigate to veritas directory**:
   ```bash
   cd veritas
   ```

---

## Option 1: Basic VerITAS (Hash Proof)

### Step 1: Generate Test Image Data

Generate an original image with 14 pixels, max value 2^3 = 8:

```bash
python3 genpic.py orig 14 3
```

This creates:
- `orig_image_14_3.txt` - Contains 14 random pixel values (0-7)

### Step 2: Configure Parameters

Edit `examples/veritas.rs`:
- Line 35: Set `static PIXELS : usize = 14;`
- Line 36: Set `static EXPONENT : u32 = 3;`

### Step 3: Build and Run

```bash
cargo run --release --example veritas
```

**What happens:**
1. Reads `orig_image_14_3.txt`
2. Generates polynomial commitments
3. Creates FRI proof
4. Verifies the proof
5. Prints timing information

---

## Option 2: Opt-VerITAS (Optimized Hash Proof)

### Step 1: Generate Test Image Data

```bash
python3 genpic.py orig 14 3
```

### Step 2: Configure Parameters

Edit `examples/generate-a-coms.rs`:
- Line 15: Set `static PIXELS : usize = 14;`
- Line 16: Set `static EXPONENT : u32 = 3;`

### Step 3: Generate Pre-computed Commitments

```bash
cargo run --release --example generate-a-coms
```

**What happens:**
- Generates hash matrix A in batches
- Creates 4 files: `A_256_14_3_0.txt`, `A_256_14_3_1.txt`, `A_256_14_3_2.txt`, `A_256_14_3_3.txt`

### Step 4: Configure Opt-Veritas Parameters

Edit `examples/opt-veritas.rs`:
- Line 36: Set `static PIXELS : usize = 14;`
- Line 37: Set `static EXPONENT : u32 = 3;`

### Step 5: Run Optimized Proof

```bash
cargo run --release --example opt-veritas
```

**What happens:**
1. Reads `orig_image_14_3.txt`
2. Reads pre-computed A matrix commitments
3. Generates optimized proof
4. Verifies the proof

---

## Option 3: Image Editing Proofs

### Example: Blur Proof

#### Step 1: Configure Blur Parameters

Edit `examples/blur.rs`:
- Line 12: `static H : usize = 14;` (image height)
- Line 13: `static W : usize = 14;` (image width)
- Line 14: `static BLUR_H : usize = 6;` (blur region height)
- Line 15: `static BLUR_W : usize = 6;` (blur region width)

#### Step 2: Run Blur Proof

```bash
cargo run --release --example blur
```

**What happens:**
1. Generates random test image
2. Applies 3x3 blur kernel to specified region
3. Creates Plonky2 circuit
4. Generates proof
5. Verifies proof

### Example: Resize Proof

```bash
# Edit examples/resize.rs to set dimensions
cargo run --release --example resize
```

### Example: Crop Proof

```bash
# Edit examples/crop.rs to set crop region
cargo run --release --example crop
```

### Example: Grayscale Proof

```bash
# Edit examples/gray.rs to set image dimensions
cargo run --release --example gray
```

---

## Quick Test Run (Recommended First Steps)

### Minimal Example - Basic VerITAS:

```bash
# 1. Navigate to veritas directory
cd veritas

# 2. Generate small test image (14 pixels, values 0-7)
python3 genpic.py orig 14 3

# 3. Verify the file was created
cat orig_image_14_3.txt

# 4. Run basic VerITAS (parameters already set to 14 and 3 in code)
cargo run --release --example veritas
```

### Expected Output:
- Timing information for each phase
- "proving done"
- "verification done"
- No assertion errors (proof verified successfully)

---

## Troubleshooting

### Issue: "Unable to open file"
- **Solution**: Make sure you're in the `veritas` directory
- Check that `orig_image_{D}_{E}.txt` exists

### Issue: Parameter mismatch
- **Solution**: Ensure PIXELS and EXPONENT in Rust code match the values used in `genpic.py`

### Issue: Compilation errors
- **Solution**: Run `cargo clean` then `cargo build --release`

### Issue: Out of memory
- **Solution**: Reduce PIXELS value or increase system memory

---

## Customizing Parameters

### For Different Image Sizes:

1. **Small test** (14 pixels, 8 values):
   ```bash
   python3 genpic.py orig 14 3
   # Set PIXELS=14, EXPONENT=3
   ```

2. **Medium test** (100 pixels, 256 values):
   ```bash
   python3 genpic.py orig 100 8
   # Set PIXELS=100, EXPONENT=8
   ```

3. **Large test** (1000 pixels, 256 values):
   ```bash
   python3 genpic.py orig 1000 8
   # Set PIXELS=1000, EXPONENT=8
   # Note: May require adjusting DEGREE constant
   ```

### Important Constants:
- `DEGREE`: Must be power of 2, >= PIXELS + PIXEL_RANGE
- `HASH_LENGTH`: Number of hash bits (default 128)
- `BATCH_SIZE`: For opt-Veritas, number of rows per batch (default 32)

---

## Understanding the Output

### Timing Output Format:
```
"phase_name"; time since start X.XX; time since last check: X.XX
```

### Success Indicators:
- No assertion panics
- "verification done" message
- All polynomial checks pass

### What Gets Generated:
- **Basic Veritas**: No files (proof verified in memory)
- **Opt-Veritas**: Creates `A_256_{D}_{E}_{i}.txt` files
- **Editing Proofs**: No files (proof verified in memory)

---

## Next Steps

1. **Modify to save proofs**: Edit the code to serialize proofs to files
2. **Benchmark**: Measure performance with different image sizes
3. **Custom transformations**: Create new editing proof examples
4. **Integration**: Use proofs in your application

