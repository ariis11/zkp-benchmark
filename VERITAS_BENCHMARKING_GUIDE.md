# Veritas Benchmarking Guide - Matching VIMz Workflow

## Understanding Your VIMz Benchmarking

**Your Workflow:**
1. ✅ Pre-process images → JSON files (separate, not measured)
2. ✅ Generate proof per JSON file (measured)
3. ✅ Track 7 metrics per image
4. ✅ Save proof + log files

**What You Measure:**
- Key generation time
- Constraints/variables count
- RecursiveSNARK creation time
- RecursiveSNARK verification time
- CompressedSNARK generation time
- CompressedSNARK verification time
- Memory statistics

**What You DON'T Measure:**
- Image conversion time (done separately)

---

## Current Veritas vs Your VIMz Workflow

### **VIMz Per-Image Output:**
```
Creating keys from R1CS took 3.844282476s
Number of constraints per step (primary circuit): 157312
Number of constraints per step (secondary circuit): 10347
Number of variables per step (primary circuit): 156666
Number of variables per step (secondary circuit): 10329
RecursiveSNARK creation took 219.700533813s
RecursiveSNARK::verify: ... took 126.225378ms
CompressedSNARK::prove: true, took 4.10984456s
CompressedSNARK::verify: true, took 188.476716ms
Maximum resident set size (kbytes): 846852
```

### **Current Veritas Output:**
```
"setup done" - time since last check: X.XX
"proof done" - time since last check: X.XX
"verify done" - time since last check: X.XX
```

**Gap:** Veritas needs to match VIMz's detailed metrics and per-image processing.

---

## What Veritas Needs to Add

### **1. Per-Image Batch Processing** ⚠️ CRITICAL

**Current:** Single run, generates random data  
**Needed:** Process each JSON file separately (like VIMz)

**Solution:**
- Add command-line arguments for input/output files
- Loop through JSON files in directory
- Generate one proof per image

### **2. Detailed Metrics** ⚠️ CRITICAL

**Current:** 3 basic timing points  
**Needed:** Match VIMz's 7 metrics

**Metrics to Add:**
1. ✅ Circuit build time (equivalent to VIMz key gen)
2. ✅ Number of constraints
3. ✅ Number of variables
4. ✅ Proof generation time
5. ✅ Verification time
6. ❌ CompressedSNARK (N/A for Plonky2 - note as such)
7. ✅ Memory statistics

### **3. File I/O** ⚠️ CRITICAL

**Current:** All in-memory  
**Needed:** Load from JSON, save proof to file

**Solution:**
- Load image data from JSON (match VIMz format)
- Save proof to JSON file
- Save metrics to log file

### **4. Structured Output** ✅ NICE TO HAVE

**Current:** Simple println!  
**Needed:** Match VIMz log format

---

## Implementation Plan

### **Step 1: Modify blur.rs to Accept Files**

```rust
use clap::Parser;
use serde_json;
use std::fs;

#[derive(Parser)]
struct Args {
    #[arg(long)]
    input: Option<String>,  // Path to JSON file
    
    #[arg(long)]
    output: Option<String>,  // Path to save proof
}

// Load image data from JSON (VIMz format)
fn load_from_json(path: &str) -> Result<(Vec<Vec<u8>>, Vec<Vec<u8>>)> {
    let json_str = fs::read_to_string(path)?;
    let data: serde_json::Value = serde_json::from_str(&json_str)?;
    
    // Parse "original" and "transformed" arrays
    // Convert from compressed hex format to pixel arrays
    // ...
}
```

### **Step 2: Add Detailed Metrics**

```rust
use std::time::Instant;
use plonky2::plonk::circuit_data::CircuitData;

fn main() -> Result<()> {
    let total_start = Instant::now();
    
    // Circuit build (equivalent to VIMz key generation)
    let circuit_start = Instant::now();
    let data = builder.build::<C>();
    let circuit_time = circuit_start.elapsed();
    
    // Get circuit statistics
    // Note: Plonky2 API may vary, check actual methods
    let num_constraints = data.common.num_gates();  // Verify this method exists
    let num_variables = data.common.num_variables();  // Verify this method exists
    
    println!("Circuit build took: {:.9}s", circuit_time.as_secs_f64());
    println!("Number of constraints: {}", num_constraints);
    println!("Number of variables: {}", num_variables);
    
    // Proof generation
    let proof_start = Instant::now();
    let proof = data.prove(pw)?;
    let proof_time = proof_start.elapsed();
    println!("Proof generation took: {:.9}s", proof_time.as_secs_f64());
    
    // Verification
    let verify_start = Instant::now();
    let res = data.verify(proof.clone());
    let verify_time = verify_start.elapsed();
    println!("Verification took: {:.9}ms", verify_time.as_secs_f64() * 1000.0);
    
    // Note: Plonky2 doesn't have CompressedSNARK equivalent
    println!("CompressedSNARK: N/A (Plonky2 uses single-phase proof)");
    
    Ok(())
}
```

### **Step 3: Add Memory Tracking**

**Option A: Use external `time` command (matches VIMz)**
```bash
/usr/bin/time -v cargo run --release --example blur \
    -- --input image.json --output proof.json
```

**Option B: Use Rust memory tracking**
```rust
// Add to Cargo.toml: procfs = "0.15"
use procfs::process::Process;

fn get_peak_memory() -> Result<u64> {
    let process = Process::myself()?;
    let stat = process.stat()?;
    Ok(stat.rss_bytes() / 1024)  // Convert to KB
}
```

### **Step 4: Create Batch Processing Script**

Create `veritas/image_converter/batch_generate_proofs.sh`:

```bash
#!/bin/bash

INPUT_DIR="${1:-image_converter/blur/outputs_hd}"
OUTPUT_DIR="${2:-image_converter/blur/proofs}"
TRANSFORMATION="${3:-blur}"

mkdir -p "$OUTPUT_DIR"

for json_file in "$INPUT_DIR"/*.json; do
    if [ -f "$json_file" ]; then
        BASENAME=$(basename "$json_file" .json)
        OUTPUT_PROOF="$OUTPUT_DIR/${BASENAME}_proof.json"
        LOG_FILE="$OUTPUT_DIR/${BASENAME}_output.log"
        
        echo "Processing: $BASENAME"
        
        (/usr/bin/time -v cargo run --release --example "$TRANSFORMATION" \
            -- --input "$json_file" \
            --output "$OUTPUT_PROOF") \
            > "$LOG_FILE" 2>&1
        
        if [ $? -eq 0 ]; then
            echo "  ✓ Saved: ${BASENAME}_proof.json"
        else
            echo "  ✗ Failed: $BASENAME"
        fi
    fi
done
```

---

## Metric Mapping: VIMz → Veritas

| VIMz Metric | Veritas Equivalent | Notes |
|-------------|-------------------|-------|
| **Key Generation Time** | Circuit Build Time | `builder.build()` |
| **Constraints (primary)** | Number of Gates | `data.common.num_gates()` |
| **Constraints (secondary)** | N/A | Plonky2 doesn't have secondary circuit |
| **Variables (primary)** | Number of Variables | `data.common.num_variables()` |
| **Variables (secondary)** | N/A | Plonky2 doesn't have secondary circuit |
| **RecursiveSNARK Creation** | Proof Generation | `data.prove(pw)` |
| **RecursiveSNARK Verify** | Verification | `data.verify(proof)` |
| **CompressedSNARK::prove** | N/A | Plonky2 single-phase |
| **CompressedSNARK::verify** | N/A | Plonky2 single-phase |
| **Memory (Max RSS)** | Memory (Max RSS) | `time -v` or procfs |

---

## Output Format to Match

**Target Veritas Output (matching VIMz style):**
```
Circuit build took: 3.844282476s
Number of constraints: 157312
Number of variables: 156666
Proof generation took: 219.700533813s
Verification took: 126.225378ms
CompressedSNARK: N/A (Plonky2 uses single-phase proof)

=== Memory and Resource Statistics ===
Maximum resident set size (kbytes): 846852
User time (seconds): 1182.55
System time (seconds): 18.61
Elapsed (wall clock) time: 3:48.12
```

---

## What to Compare

### **✅ Comparable Metrics:**
1. Circuit Build / Key Generation time
2. Number of constraints
3. Number of variables
4. Proof generation time
5. Verification time
6. Memory usage

### **⚠️ Different (Note in Comparison):**
- **CompressedSNARK:** VIMz has this, Veritas doesn't (Plonky2 architecture)
- **Secondary Circuit:** VIMz has this, Veritas doesn't (Nova folding)

### **❌ Exclude from Comparison:**
- Image conversion time (you exclude this in VIMz too)

---

## Quick Checklist

**To make Veritas match your VIMz benchmarking:**

- [ ] Add file input/output (JSON format)
- [ ] Add per-image batch processing
- [ ] Add circuit build time measurement
- [ ] Add constraint count reporting
- [ ] Add variable count reporting
- [ ] Add proof generation time measurement
- [ ] Add verification time measurement
- [ ] Add memory statistics (via `time -v` or procfs)
- [ ] Create batch processing script
- [ ] Format output to match VIMz style
- [ ] Note CompressedSNARK as N/A

---

## Next Steps

1. **Modify `blur.rs`** to accept JSON input
2. **Add metrics collection** (timing, constraints, variables)
3. **Create batch script** for per-image processing
4. **Test with one image** to validate output format
5. **Run batch** on all images
6. **Compare results** with VIMz metrics

This will give you a fair comparison between the two systems!

