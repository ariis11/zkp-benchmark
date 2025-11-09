# VerITAS System - Detailed Pipeline Explanation

## Overview
VerITAS (Verifiable Image Transformation Authentication System) is a zero-knowledge proof system for proving properties about images and image transformations. It uses Plonky2 (a zk-SNARK system) with FRI (Fast Reed-Solomon Interactive Oracle Proofs) to create proofs.

## System Architecture

### Components:
1. **Image Generation Script** (`genpic.py`) - Generates test image data
2. **Basic Veritas** (`veritas.rs`) - Standard hash proof generation
3. **Opt-Veritas** (`opt-veritas.rs`) - Optimized version with pre-computed commitments
4. **Editing Proofs** (`blur.rs`, `resize.rs`, `crop.rs`, `gray.rs`) - Proofs for image transformations

---

## Pipeline 1: Basic VerITAS Hash Proof

### Purpose:
Prove that you know an image with specific properties (D pixels, max value 2^E) that hashes to a specific value.

### Step-by-Step Pipeline:

#### **Step 1: Generate Test Images**
- **Script**: `genpic.py`
- **Input**: Prefix ("orig" or "edited"), number of pixels (D), exponent (E)
- **Output**: 
  - `{prefix}_image_{D}_{E}.txt` - Contains D random pixel values (0 to 2^E-1)
  - `{prefix}_hash_{D}_{E}.txt` - Contains D random hash values (for reference)

#### **Step 2: Configure Parameters**
- Edit `veritas.rs`:
  - Line 35: `static PIXELS : usize = D;` (number of pixels)
  - Line 36: `static EXPONENT : u32 = E;` (max pixel value is 2^E)

#### **Step 3: Proof Generation (veritas.rs)**

**Phase 1: Polynomial Construction**
1. **w polynomial**: Represents the valid pixel range [0, PIXEL_RANGE-1]
   - `w_vals = [0, 1, 2, ..., PIXEL_RANGE-1, 0, 0, ...]` (padded to DEGREE)
   - Converted to polynomial via IFFT

2. **v polynomial**: Represents the actual image pixels
   - Reads from `orig_image_{D}_{E}.txt`
   - `v_vals = [pixel_0, pixel_1, ..., pixel_{D-1}, 0, 0, ...]` (padded)

3. **z polynomial**: Sorted concatenation of v and w
   - `z_vals = sort([pixel_0, ..., pixel_{D-1}, 0, 1, ..., PIXEL_RANGE-1])`
   - Used for permutation argument

**Phase 2: First Commitment (commit0)**
- Commits to polynomials: `[w, v, z]`
- Creates Merkle tree of polynomial evaluations
- Generates `gamma` from SHA256 hash of commitment (for permutation argument)

**Phase 3: Permutation Argument (commit1)**
Proves: `∏(v_i + γ) * ∏(w_i + γ) = ∏(z_i + γ)`

1. **w_prod**: Cumulative product of (w_i + γ)
2. **v_prod**: Cumulative product of (v_i + γ)
3. **z_prod**: Cumulative product of (z_i + γ)
4. **Quotient polynomials** (q_w, q_v, q_z): Prove the product relations hold
5. **q_range**: Proves range constraint (z[ω*x] - z[x]) ∈ {0,1}

**Phase 4: Hash Argument (commit2)**
Proves knowledge of hash value using lattice-based hashing:

1. **Hash coefficients**: Generated from SHA256 of commit1's Merkle cap
2. **a polynomial**: Linear combination of hash matrix rows
   - Matrix A generated via PRG (Pseudo-Random Generator)
   - `a[i] = Σ(r_j * A_{j,i})` where r_j are hash coefficients
3. **h_sum polynomial**: Cumulative sum of `v[i] * a[i]`
   - Proves: `h_sum[ω*x] = h_sum[x] + v[x] * a[x]`
4. **q_h_sum**: Quotient polynomial proving the sum relation

**Phase 5: FRI Proof Generation**
1. **Challenger**: Generates random challenge `zeta` from all commitments
2. **Opening points**: Polynomials opened at:
   - `zeta` and `g*zeta` (for product checks)
   - `g^PIXELS` (for pixel count)
   - `g^PIXEL_RANGE` (for range)
   - `g^(PIXELS+PIXEL_RANGE)` (for permutation check)
3. **FRI proof**: Proves polynomial evaluations are consistent with commitments

**Phase 6: Verification**
- Verifies FRI proof
- Checks polynomial relations at challenge point `zeta`
- Validates all constraints

---

## Pipeline 2: Opt-VerITAS (Optimized Version)

### Purpose:
Same as basic Veritas but with pre-computed hash matrix commitments for efficiency.

### Additional Steps:

#### **Step 1: Generate Row Commitments**
- **Script**: `generate-a-coms.rs`
- **Process**:
  - Generates hash matrix A in batches (BATCH_SIZE = 32 rows at a time)
  - For each batch:
    - Creates polynomials for each row
    - Commits to them
    - Saves Merkle caps to files: `A_256_{PIXELS}_{EXPONENT}_{batch}.txt`
- **Output**: 4 files (128 hash length / 32 batch size = 4 batches)

#### **Step 2: Proof Generation (opt-veritas.rs)**
- Similar to basic Veritas but:
  - Reads pre-computed A matrix commitments from files
  - Opens A matrix rows at challenge point `zeta`
  - Combines them: `a[zeta] = Σ(r_i * A_i[zeta])`
  - More efficient for large images

---

## Pipeline 3: Image Editing Proofs

### Purpose:
Prove that an edited image was correctly transformed from the original.

### Examples:

#### **Blur Proof (blur.rs)**
1. **Input**: Original image pixels `w_r_vals[H][W]`
2. **Transformation**: Applies 3x3 blur kernel to specified region
3. **Output**: Blurred image `x_r_vals[H][W]`
4. **Circuit**: 
   - Takes original pixels as private inputs
   - Computes blur operation
   - Outputs blurred pixels as public inputs
5. **Proof**: Proves blur was computed correctly

#### **Resize Proof (resize.rs)**
- Proves bilinear interpolation for image resizing
- Uses 4 corner pixels to compute each new pixel

#### **Crop Proof (crop.rs)**
- Proves a cropped region was extracted from original

#### **Grayscale Proof (gray.rs)**
- Proves RGB to grayscale conversion

---

## Key Concepts

### Polynomial Commitments
- Uses FRI (Fast Reed-Solomon IOP)
- Polynomials are committed via Merkle trees of evaluations
- Rate = 2^rate_bits (oversampling factor)
- Cap height = Merkle tree root height

### Permutation Argument
- Proves two multisets are equal using product argument
- Uses random challenge `gamma` to make it binding

### Range Checks
- Proves pixel values are in valid range [0, PIXEL_RANGE-1]
- Uses: `(z[ω*x] - z[x]) * (1 - (z[ω*x] - z[x])) = 0`

### Hash Argument
- Uses lattice-based hashing
- Proves knowledge of preimage without revealing it
- Matrix A is public, coefficients r are derived from commitments

### FRI Protocol
- Interactive proof that committed polynomials satisfy constraints
- Uses multiple rounds of polynomial evaluation
- Final proof is non-interactive (via Fiat-Shamir)

---

## File Structure

```
veritas/
├── genpic.py                    # Image generator
├── examples/
│   ├── veritas.rs               # Basic hash proof
│   ├── opt-veritas.rs           # Optimized hash proof
│   ├── generate-a-coms.rs       # Pre-compute A matrix
│   ├── blur.rs                  # Blur transformation proof
│   ├── resize.rs                # Resize transformation proof
│   ├── crop.rs                  # Crop transformation proof
│   └── gray.rs                  # Grayscale transformation proof
└── Cargo.toml                   # Rust dependencies
```

---

## Generated Files

### Input Files:
- `orig_image_{D}_{E}.txt` - Original image pixels
- `edited_image_{D}_{E}.txt` - Edited image pixels (for editing proofs)

### Output Files (opt-Veritas):
- `A_256_{D}_{E}_{i}.txt` - Pre-computed hash matrix commitments (i = 0..3)

### Proof Output:
- Proofs are generated in memory and verified immediately
- No persistent proof files are saved (can be modified to save)

