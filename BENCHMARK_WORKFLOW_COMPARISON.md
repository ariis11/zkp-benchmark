# Veritas vs VIMz: Benchmarking Workflow Comparison

## Your VIMz Benchmarking Workflow (Current)

### **Phase 1: Image Preprocessing (Separate, Not Measured)**
```bash
# Run once per transformation type
./batch_convert.sh blur passports_hd blur/outputs_hd
```
- **Input:** HD PNG images in `passports_hd/`
- **Output:** JSON files in `blur/outputs_hd/` (one per image)
- **Each JSON contains:** `{"original": [...], "transformed": [...]}`
- **NOT measured:** This preprocessing time is excluded from benchmarks

### **Phase 2: Per-Image Proof Generation (Measured)**
```bash
./batch_generate_proofs.sh image_converter/blur/outputs_hd \
                           image_converter/blur/proofs \
                           blur HD
```
- **Process:** Generates proof for **each JSON file separately**
- **Output per image:**
  - `passport_0000_proof.json` - Proof file
  - `passport_0000_output.log` - Detailed metrics

### **Metrics Measured Per Image:**

1. **Key Generation Time:**
   ```
   Creating keys from R1CS took 3.844282476s
   ```

2. **Circuit Statistics:**
   ```
   Number of constraints per step (primary circuit): 157312
   Number of constraints per step (secondary circuit): 10347
   Number of variables per step (primary circuit): 156666
   Number of variables per step (secondary circuit): 10329
   ```

3. **RecursiveSNARK Creation Time:**
   ```
   RecursiveSNARK creation took 219.700533813s
   ```

4. **RecursiveSNARK Verification Time:**
   ```
   RecursiveSNARK::verify: ... took 126.225378ms
   ```

5. **CompressedSNARK Generation Time:**
   ```
   CompressedSNARK::prove: true, took 4.10984456s
   ```

6. **CompressedSNARK Verification Time:**
   ```
   CompressedSNARK::verify: true, took 188.476716ms
   ```

7. **Memory and Resource Statistics** (from `time -v`):
   ```
   Maximum resident set size (kbytes): 846852
   User time (seconds): 1182.55
   System time (seconds): 18.61
   Elapsed (wall clock) time: 3:48.12
   ```

---

## Current Veritas Workflow (What It Does Now)

### **Current Implementation:**

```rust
// examples/blur.rs
fn main() -> Result<()> {
    // 1. Generate random test data (in-memory)
    let mut w_r_vals = Vec::new();  // Original
    let mut x_r_vals = Vec::new();  // Blurred
    
    // 2. Build circuit
    let data = builder.build::<C>();
    last = print_time_since(last, "setup done");
    
    // 3. Generate proof
    let proof = data.prove(pw)?;
    last = print_time_since(last, "proof done");
    
    // 4. Verify
    let res = data.verify(proof);
    last = print_time_since(last, "verify done");
}
```

### **What Veritas Currently Measures:**

1. ✅ **"setup done"** - Circuit building time
2. ✅ **"proof done"** - Proof generation time  
3. ✅ **"verify done"** - Verification time

### **What Veritas Does NOT Measure:**

1. ❌ **Key generation time** (separate from circuit build)
2. ❌ **Number of constraints**
3. ❌ **Number of variables**
4. ❌ **Proof generation breakdown** (no separate phases)
5. ❌ **Memory statistics**
6. ❌ **Per-image processing** (single run, not batch)
7. ❌ **File I/O** (all in-memory)

---

## Detailed Comparison Table

| Metric                        | VIMz                          | Veritas            | Match?                |
|--------                       |------                         |---------           |-------                |
| **Key Generation Time**       | ✅ Measured separately        | ❌ Not measured   | ❌ Need to add        |
| **Circuit Build Time**        | Included in key gen           | ✅ "setup done"   | ⚠️ Different scope    |
| **Number of Constraints**     | ✅ Primary + Secondary        | ❌ Not measured   | ❌ Need to add        |
| **Number of Variables**       | ✅ Primary + Secondary        | ❌ Not measured   | ❌ Need to add        |
| **Proof Generation Time**     | ✅ RecursiveSNARK creation    | ✅ "proof done"   | ⚠️ Different phases   |
| **Proof Verification Time**   | ✅ RecursiveSNARK verify      | ✅ "verify done"  | ⚠️ Different phases   |
| **Compressed Proof Gen**      | ✅ CompressedSNARK::prove     | ❌ Not applicable | ❌ Different system   |
| **Compressed Proof Verify**   | ✅ CompressedSNARK::verify    | ❌ Not applicable | ❌ Different system   |
| **Memory Usage**              | ✅ Max RSS from `time -v`     | ❌ Not measured   | ❌ Need to add        |
| **Per-Image Processing**      | ✅ One proof per JSON         | ❌ Single run     | ❌ Need batch mode    |
| **File I/O**                  | ✅ JSON input/output          | ❌ In-memory only | ❌ Need file support  |

---

## What Needs to Be Added to Veritas

### **Critical (For Fair Comparison):**

1. **Per-Image Batch Processing:**
   - Load images from files (like VIMz JSON files)
   - Process each image separately
   - Generate one proof per image
   - Save proof to file

2. **Detailed Timing Breakdown:**
   - Separate key generation time (if applicable in Plonky2)
   - Separate circuit build time
   - Separate proof generation time
   - Separate verification time

3. **Circuit Statistics:**
   - Number of constraints
   - Number of variables
   - Circuit size metrics

4. **Memory Statistics:**
   - Peak memory usage
   - Use `time -v` or equivalent Rust memory tracking

### **Nice to Have:**

5. **File I/O:**
   - Load image data from JSON (match VIMz format)
   - Save proofs to JSON files
   - Save metrics to log files

6. **Structured Output:**
   - JSON format for proofs
   - Structured log format matching VIMz

---

## Plonky2 vs Nova: Metric Mapping

### **VIMz (Nova) Metrics:**
- **Key Generation:** Creating keys from R1CS
- **RecursiveSNARK Creation:** Folding-based proof generation
- **RecursiveSNARK Verify:** Verify folded proof
- **CompressedSNARK::prove:** Compress to final proof
- **CompressedSNARK::verify:** Verify compressed proof

### **Veritas (Plonky2) Equivalent:**
- **Key Generation:** `CircuitData::build()` - This is the "setup done"
- **Proof Generation:** `data.prove(pw)` - Single step (no folding)
- **Verification:** `data.verify(proof)` - Single step

**Key Difference:** Plonky2 doesn't have the same two-phase structure (RecursiveSNARK + CompressedSNARK). It's a single proof generation step.

**What to Compare:**
- ✅ **Circuit Build/Key Gen:** VIMz key gen ≈ Veritas circuit build
- ✅ **Proof Generation:** VIMz RecursiveSNARK creation ≈ Veritas `prove()`
- ✅ **Verification:** VIMz RecursiveSNARK verify ≈ Veritas `verify()`
- ⚠️ **CompressedSNARK:** No direct equivalent in Plonky2 (can note as N/A)

---

## Recommended Veritas Modifications

### **1. Add Batch Processing Script**

Create `veritas/image_converter/batch_generate_proofs.sh` (similar to VIMz):

```bash
#!/bin/bash
INPUT_DIR="${1:-image_converter/blur/outputs_hd}"
OUTPUT_DIR="${2:-image_converter/blur/proofs}"
TRANSFORMATION="${3:-blur}"

for json_file in "$INPUT_DIR"/*.json; do
    BASENAME=$(basename "$json_file" .json)
    OUTPUT_PROOF="$OUTPUT_DIR/${BASENAME}_proof.json"
    LOG_FILE="$OUTPUT_DIR/${BASENAME}_output.log"
    
    (/usr/bin/time -v cargo run --release --example blur \
        -- --input "$json_file" \
        --output "$OUTPUT_PROOF") \
        > "$LOG_FILE" 2>&1
done
```

### **2. Modify blur.rs to Accept File Input**

```rust
// Add command-line arguments
use clap::Parser;

#[derive(Parser)]
struct Args {
    #[arg(long)]
    input: Option<String>,  // JSON file path
    
    #[arg(long)]
    output: Option<String>,  // Proof output path
}

fn main() -> Result<()> {
    let args = Args::parse();
    
    // Load from JSON if provided, else generate random
    let (w_r_vals, x_r_vals) = if let Some(input_path) = args.input {
        load_from_json(&input_path)?
    } else {
        generate_random_data()
    };
    
    // ... rest of proof generation ...
    
    // Save proof if output path provided
    if let Some(output_path) = args.output {
        save_proof(&proof, &output_path)?;
    }
}
```

### **3. Add Detailed Metrics Collection**

```rust
use std::time::Instant;

fn main() -> Result<()> {
    let start = Instant::now();
    
    // Key generation / Circuit build
    let circuit_start = Instant::now();
    let data = builder.build::<C>();
    let circuit_time = circuit_start.elapsed();
    
    // Get circuit statistics
    let num_constraints = data.common.num_gates();
    let num_variables = data.common.num_variables();
    
    println!("Circuit build took: {:?}", circuit_time);
    println!("Number of constraints: {}", num_constraints);
    println!("Number of variables: {}", num_variables);
    
    // Proof generation
    let proof_start = Instant::now();
    let proof = data.prove(pw)?;
    let proof_time = proof_start.elapsed();
    println!("Proof generation took: {:?}", proof_time);
    
    // Verification
    let verify_start = Instant::now();
    let res = data.verify(proof);
    let verify_time = verify_start.elapsed();
    println!("Verification took: {:?}", verify_time);
    
    // Total time
    let total_time = start.elapsed();
    println!("Total time: {:?}", total_time);
}
```

### **4. Add Memory Tracking**

```rust
// Option 1: Use time command (external)
// Run with: /usr/bin/time -v cargo run ...

// Option 2: Use Rust memory tracking crate
// Add to Cargo.toml: procfs = "0.15"
use procfs::process::Process;

fn get_memory_usage() -> Result<u64> {
    let process = Process::myself()?;
    let stat = process.stat()?;
    Ok(stat.rss_bytes())
}
```

---

## Comparison Strategy

### **What to Compare:**

1. ✅ **Circuit Build Time** (VIMz key gen vs Veritas circuit build)
2. ✅ **Proof Generation Time** (VIMz RecursiveSNARK vs Veritas prove)
3. ✅ **Verification Time** (VIMz RecursiveSNARK verify vs Veritas verify)
4. ✅ **Memory Usage** (Both measure peak RSS)
5. ✅ **Constraint Count** (Both report circuit size)
6. ⚠️ **CompressedSNARK** (Note: N/A for Plonky2)

### **What NOT to Compare:**

1. ❌ **Image Conversion Time** (You exclude this in VIMz)
2. ❌ **CompressedSNARK phases** (Plonky2 doesn't have this)

### **Fair Comparison Approach:**

**For each image:**
1. Load pre-processed JSON (same format as VIMz)
2. Measure circuit build time
3. Measure proof generation time
4. Measure verification time
5. Measure memory usage
6. Report constraint/variable counts

**Output format matching VIMz:**
```
Circuit build took: X.XXXs
Number of constraints: XXXXX
Number of variables: XXXXX
Proof generation took: X.XXXs
Verification took: X.XXXms
Maximum resident set size: XXXXX KB
```

---

## Summary

**Your VIMz Workflow:**
- ✅ Per-image processing
- ✅ Detailed metrics (7 categories)
- ✅ Memory statistics
- ✅ File-based I/O
- ✅ Batch processing

**Current Veritas:**
- ❌ Single run only
- ❌ Basic timing (3 phases)
- ❌ No memory stats
- ❌ In-memory only
- ❌ No batch processing

**To Match VIMz:**
1. Add batch processing (per-image)
2. Add detailed metrics (constraints, variables, memory)
3. Add file I/O (JSON input/output)
4. Add structured logging (match VIMz format)

**Key Insight:** The proof system difference (Nova vs Plonky2) means some metrics won't have direct equivalents, but you can still compare the core operations (circuit build, proof gen, verify, memory).

