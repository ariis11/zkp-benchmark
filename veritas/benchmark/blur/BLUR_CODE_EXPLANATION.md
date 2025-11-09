# Veritas Blur Transformation - Detailed Code Explanation

## Overview

This code proves that a blurred image was correctly computed from an original image using a 3×3 box blur kernel, without revealing the original image pixels.

---

## Section 1: Imports and Constants (Lines 1-15)

```rust
use anyhow::Result;
use plonky2::field::types::Field;
use plonky2::iop::witness::{PartialWitness, WitnessWrite};
use plonky2::plonk::circuit_builder::CircuitBuilder;
use plonky2::plonk::circuit_data::CircuitConfig;
use plonky2::plonk::config::{GenericConfig, PoseidonGoldilocksConfig};
use std::time::{SystemTime, UNIX_EPOCH};
use rand::rngs::OsRng;
use rand::Rng;

static H : usize = 14;
static W : usize = 14;
static BLUR_H : usize = 6;
static BLUR_W : usize = 6;
```

**What this does:**
- **Imports:** Plonky2 libraries for building zero-knowledge circuits
- **Constants:**
  - `H = 14`: Image height (14 pixels)
  - `W = 14`: Image width (14 pixels)
  - `BLUR_H = 6`: Height of blurred region
  - `BLUR_W = 6`: Width of blurred region

**Note:** Only a 6×6 region (from position [1,1] to [6,6]) will be blurred. The rest stays unchanged.

---

## Section 2: Helper Function (Lines 17-25)

```rust
fn print_time_since(last: u128, tag: &str) -> u128 {
    let now = SystemTime::now();
    let now_epoc = now
        .duration_since(UNIX_EPOCH)
        .expect("Time went backwards");
    let now = now_epoc.as_millis();
    println!("{:?} - time since last check: {:?}", tag, (now - last) as f32 / 60000.0); 
    return now;
}
```

**What this does:**
- **Purpose:** Timing utility to measure performance
- **Input:** Last timestamp and a label
- **Output:** Current timestamp
- **Action:** Prints elapsed time in minutes since last checkpoint

---

## Section 3: Main Function Setup (Lines 27-31)

```rust
fn main() -> Result<()> {
    const D: usize = 2;
    type C = PoseidonGoldilocksConfig;
    type F = <C as GenericConfig<D>>::F;
```

**What this does:**
- **`D = 2`:** Extension degree (for field arithmetic)
- **`C`:** Plonky2 configuration using Poseidon hash and Goldilocks field
- **`F`:** Field type (Goldilocks field elements)
- **Purpose:** Sets up the mathematical foundation for the zero-knowledge proof

---

## Section 4: Generate Test Data (Lines 32-43)

```rust
let mut rng = OsRng;
let mut w_r_vals = Vec::new();
let mut x_r_vals = Vec::new();

for _ in 0..H {
    let mut r_row = Vec::new();
    for _ in 0..W {
        r_row.push(rng.gen_range(0..256) as usize);
    }
    w_r_vals.push(r_row);
}
```

**What this does:**
- **Purpose:** Generates random test image data
- **`w_r_vals`:** Original image pixels (14×14 matrix)
- **Process:** 
  - Creates 14 rows
  - Each row has 14 random pixel values (0-255)
  - This simulates an original image
- **Note:** In real usage, this would load from a file instead

**Result:** `w_r_vals` contains the original image:
```
w_r_vals[0][0] = 123  w_r_vals[0][1] = 45  ...
w_r_vals[1][0] = 200  w_r_vals[1][1] = 67  ...
...
```

---

## Section 5: Apply Blur Transformation (Lines 45-63)

```rust
for i in 0..H {
    let mut r_row = Vec::new();
    for j in 0..W {
        if i > 0 && i < 1 + BLUR_H && j > 0 && j < 1 + BLUR_W {
            // in blur region
            let sum_r = w_r_vals[i-1][j-1] + w_r_vals[i-1][j] + w_r_vals[i-1][j+1]
                        + w_r_vals[i][j-1] + w_r_vals[i][j] + w_r_vals[i][j+1]
                        + w_r_vals[i+1][j-1] + w_r_vals[i+1][j] + w_r_vals[i+1][j+1]; 

            let blur_r = (sum_r as f64 / 9.0).round() as usize;
            r_row.push(blur_r);
        }
        else {
            r_row.push(w_r_vals[i][j]);
        }
    }
    x_r_vals.push(r_row);
}
```

**What this does:**
- **Purpose:** Computes the blurred image from the original
- **Process:**
  1. **For each pixel [i,j]:**
     - **If in blur region** (1 ≤ i ≤ 6, 1 ≤ j ≤ 6):
       - **3×3 Box Blur:** Sums 9 neighboring pixels:
         ```
         [i-1][j-1]  [i-1][j]  [i-1][j+1]
         [i][j-1]    [i][j]    [i][j+1]
         [i+1][j-1]  [i+1][j]  [i+1][j+1]
         ```
       - **Average:** Divides sum by 9 and rounds
       - **Result:** Blurred pixel value
     - **If outside blur region:**
       - **Copy:** Keeps original pixel value unchanged

**Example:**
- Original pixel at [2,2] = 100
- Neighbors: [50, 60, 70, 80, 100, 120, 130, 140, 150]
- Sum = 900
- Blurred = 900 / 9 = 100

**Result:** `x_r_vals` contains the blurred image (same size as original)

---

## Section 6: Circuit Builder Setup (Lines 65-74)

```rust
// Timing setup
let start = SystemTime::now();
let start_epoch = start
    .duration_since(UNIX_EPOCH)
    .expect("Time went backwards");
let start = start_epoch.as_millis();
let mut last = start;
        
let config = CircuitConfig::standard_recursion_config();
let mut builder = CircuitBuilder::<F, D>::new(config);
```

**What this does:**
- **Timing:** Starts performance measurement
- **Circuit Config:** Creates standard Plonky2 configuration
- **Circuit Builder:** Creates a builder to construct the zero-knowledge circuit
- **Purpose:** Sets up the "blueprint" for the proof system

**Think of it as:** Creating an empty circuit that will define the constraints

---

## Section 7: Define Private Inputs (Lines 76-84)

```rust
let mut w_r_targets = Vec::new();
for _ in 0..H {
    let mut w_r_target_row = Vec::new();
    for _ in 0..W {
        let w_r = builder.add_virtual_target();
        w_r_target_row.push(w_r);
    }  
    w_r_targets.push(w_r_target_row);       
}
```

**What this does:**
- **Purpose:** Creates circuit variables for the original image pixels
- **`add_virtual_target()`:** Creates a placeholder variable in the circuit
- **Process:** Creates 14×14 = 196 variables, one per pixel
- **`w_r_targets`:** Matrix of circuit variables representing original image

**Important:** These are **private inputs** - the verifier won't see the actual values, only that the proof is valid.

**Think of it as:** Creating 196 "slots" in the circuit where the original pixel values will be placed (but kept secret).

---

## Section 8: Define Circuit Constraints for Blur (Lines 86-130)

This is the **core** of the zero-knowledge proof - it defines what computation must be proven.

### **8a: Setup Loop (Lines 86-89)**
```rust
let mut x_r_targets = Vec::new();
for i in 0..H {
    let mut x_r_target_row = Vec::new();
    for j in 0..W {
```

**What this does:** Iterates through each pixel position

### **8b: Blur Region - Collect Neighbors (Lines 90-102)**
```rust
if i > 0 && i < 1 + BLUR_H && j > 0 && j < 1 + BLUR_W {
    // in blur region
    let mut all_r = Vec::new();

    all_r.push(w_r_targets[i-1][j-1]);
    all_r.push(w_r_targets[i-1][j]);
    all_r.push(w_r_targets[i-1][j+1]);
    all_r.push(w_r_targets[i][j-1]);
    all_r.push(w_r_targets[i][j]);
    all_r.push(w_r_targets[i][j+1]);
    all_r.push(w_r_targets[i+1][j-1]);
    all_r.push(w_r_targets[i+1][j]);
    all_r.push(w_r_targets[i+1][j+1]);
```

**What this does:**
- **Purpose:** Collects the 9 neighboring pixel variables
- **Process:** Creates a vector of circuit variables representing the 3×3 neighborhood
- **Result:** `all_r` contains 9 circuit variables (the neighbors)

### **8c: Sum the Neighbors (Line 105)**
```rust
let s_r = builder.add_many(all_r);
```

**What this does:**
- **Purpose:** Adds all 9 neighbor values together in the circuit
- **`add_many()`:** Creates a constraint: `s_r = sum of all 9 neighbors`
- **Result:** `s_r` is a circuit variable representing the sum

**Circuit constraint created:** `s_r = w[i-1][j-1] + w[i-1][j] + ... + w[i+1][j+1]`

### **8d: Division with Remainder Trick (Lines 107-114)**
```rust
// add 4 this so that remainder moves from value in [-4,4] to value in [0,8]
let s_r_shift = builder.add_const(s_r, F::from_canonical_u32(4));

let x_r = builder.add_virtual_target();
x_r_target_row.push(x_r);
let x_r_times_9 = builder.mul_const(F::from_canonical_u32(9), x_r);

let rem_r = builder.sub(s_r_shift, x_r_times_9);
```

**What this does:**
- **Problem:** We need to prove `blurred = sum / 9`, but division is expensive in circuits
- **Solution:** Use the division-with-remainder trick:
  - **Step 1:** Shift sum by +4: `s_r_shift = s_r + 4`
    - This moves remainder range from [-4, 4] to [0, 8]
  - **Step 2:** Create blurred pixel variable: `x_r` (the result)
  - **Step 3:** Multiply by 9: `x_r_times_9 = x_r * 9`
  - **Step 4:** Compute remainder: `rem_r = s_r_shift - x_r_times_9`

**Mathematical relationship:**
- `s_r_shift = 9 * x_r + rem_r`
- This proves: `x_r = (s_r_shift - rem_r) / 9`
- Which is: `x_r = (s_r + 4 - rem_r) / 9`
- So: `x_r ≈ s_r / 9` (with remainder handling)

**Why +4?** When dividing by 9, the remainder can be negative. Adding 4 ensures remainder is always in [0, 8].

### **8e: Range Check Remainder (Lines 116-120)**
```rust
// To check that rem \in [0, 8], we must check that rem < 2^4 and that
// rem + 7 < 2^4
builder.range_check(rem_r, 4);
let rem_r_plus_7 = builder.add_const(rem_r, F::from_canonical_u32(7));
builder.range_check(rem_r_plus_7, 4);
```

**What this does:**
- **Purpose:** Ensures the remainder is valid (between 0 and 8)
- **Range Check 1:** `rem_r < 2^4 = 16`
  - This ensures `rem_r ≤ 15`
- **Range Check 2:** `rem_r + 7 < 16`
  - This ensures `rem_r ≤ 8`
- **Combined:** Proves `0 ≤ rem_r ≤ 8`

**Why two checks?** A single range check can't prove both bounds. Two checks ensure the remainder is in the valid range [0, 8].

### **8f: Non-Blurred Region (Lines 122-125)**
```rust
else {
    builder.register_public_input(w_r_targets[i][j]);
}
```

**What this does:**
- **Purpose:** For pixels outside the blur region
- **Action:** Makes the original pixel value a **public input**
- **Result:** Verifier can see these pixels (they're not secret)

**Why public?** Since these pixels don't change, there's no need to hide them.

### **8g: Store Blurred Pixels (Lines 127-129)**
```rust
if x_r_target_row.len() > 0 {
     x_r_targets.push(x_r_target_row);
}
```

**What this does:** Stores the blurred pixel variables for later use

---

## Section 9: Build Circuit (Lines 132-133)

```rust
let data = builder.build::<C>();
last = print_time_since(last, "setup done");
```

**What this does:**
- **Purpose:** Finalizes the circuit construction
- **`build()`:** Compiles all constraints into a circuit data structure
- **Result:** `data` contains the complete circuit ready for proving
- **Timing:** Records how long circuit building took

**Think of it as:** Compiling the "blueprint" into an executable circuit.

---

## Section 10: Create Witness (Lines 135-147)

```rust
let mut pw = PartialWitness::new();

for i in 0..H {
    for j in 0..W {
        pw.set_target(w_r_targets[i][j], F::from_canonical_u32(w_r_vals[i][j] as u32));
   }
}

for i in 0..BLUR_H {
    for j in 0..BLUR_W {
        pw.set_target(x_r_targets[i][j], F::from_canonical_u32(x_r_vals[i+1][j+1] as u32));
    }
}
```

**What this does:**
- **Purpose:** Fills in the actual values for the circuit variables
- **`PartialWitness`:** Container for the secret values
- **Loop 1:** Sets all original pixel values (private)
  - `w_r_targets[i][j]` ← `w_r_vals[i][j]`
- **Loop 2:** Sets blurred pixel values (private, but will be proven)
  - `x_r_targets[i][j]` ← `x_r_vals[i+1][j+1]`
  - Note: `i+1, j+1` because blur region starts at [1,1]

**Think of it as:** Filling in the "slots" we created earlier with actual pixel values.

---

## Section 11: Generate Proof (Lines 150-151)

```rust
let proof = data.prove(pw)?;
last = print_time_since(last, "proof done");
```

**What this does:**
- **Purpose:** Generates the zero-knowledge proof
- **`prove()`:** 
  - Takes the circuit and witness
  - Computes a proof that the witness satisfies all constraints
  - **Without revealing the witness values**
- **Result:** `proof` is a cryptographic proof that can be verified
- **Timing:** Records proof generation time

**This is the magic:** The proof proves the blur was computed correctly, but doesn't reveal the original image!

---

## Section 12: Verify Public Inputs (Lines 153-162)

```rust
let mut ctr = 0;
for i in 0..H {
    for j in 0..W {
        if !(i > 0 && i < 1 + BLUR_H && j > 0 && j < 1 + BLUR_W) {
            assert!(x_r_vals[i][j] as u64 == proof.public_inputs[ctr].0);
            ctr += 1;
        }
    }
}
```

**What this does:**
- **Purpose:** Checks that public inputs match expected values
- **Process:**
  - For pixels **outside** blur region
  - Verifies that the proof's public inputs match the original pixels
  - (Since these pixels don't change, they should be public)
- **Assertion:** Ensures correctness

**Why check?** This ensures the proof is consistent with the expected output.

---

## Section 13: Verify Proof (Lines 164-167)

```rust
let res = data.verify(proof);
let _ = res.unwrap();

_ = print_time_since(last, "verify done");
```

**What this does:**
- **Purpose:** Verifies the proof is valid
- **`verify()`:** 
  - Checks that the proof is cryptographically valid
  - Verifies all constraints are satisfied
  - **Does NOT reveal the private inputs**
- **Result:** Returns `Ok(())` if proof is valid, error otherwise
- **Timing:** Records verification time

**This is what a verifier would do:** They can verify the proof without seeing the original image!

---

## Complete Flow Summary

1. **Generate Test Data:** Create random 14×14 image
2. **Apply Blur:** Compute blurred version (6×6 region)
3. **Build Circuit:** Define constraints (sum neighbors, divide by 9, range check)
4. **Create Witness:** Fill in actual pixel values
5. **Generate Proof:** Create zero-knowledge proof
6. **Verify:** Check proof is valid

**Key Insight:** The circuit proves:
- "I know original pixels that, when blurred, produce these blurred pixels"
- "The blur was computed correctly (sum of 9 neighbors / 9)"
- "The remainder is valid (0-8)"
- **Without revealing the original pixels!**

---

## Mathematical Details

### **Blur Formula:**
```
blurred[i][j] = round((sum of 9 neighbors) / 9)
```

### **Circuit Constraint:**
```
s_r_shift = 9 * x_r + rem_r
where:
- s_r_shift = sum of neighbors + 4
- x_r = blurred pixel
- rem_r ∈ [0, 8]
```

### **Why This Works:**
- Division by 9 is expensive in circuits
- Using remainder trick: `x = (sum - rem) / 9`
- Range checking `rem` ensures it's valid
- This proves division was done correctly without actually dividing!

---

## Security Properties

✅ **Zero-Knowledge:** Original image pixels are never revealed  
✅ **Correctness:** Proof ensures blur was computed correctly  
✅ **Completeness:** Valid proofs always verify  
✅ **Soundness:** Invalid computations can't produce valid proofs

