use anyhow::Result;
use plonky2::field::types::Field;
use plonky2::iop::witness::{PartialWitness, WitnessWrite};
use plonky2::plonk::circuit_builder::CircuitBuilder;
use plonky2::plonk::circuit_data::CircuitConfig;
use plonky2::plonk::config::{GenericConfig, PoseidonGoldilocksConfig};
use serde_json::Value;
use std::fs;
use std::time::Instant;

static H : usize = 720;
static W : usize = 1280;
static BLUR_H : usize = 6;
static BLUR_W : usize = 6;

fn main() -> Result<()> {
    const D: usize = 2;
    type C = PoseidonGoldilocksConfig;
    type F = <C as GenericConfig<D>>::F;

    // Load image data from JSON
    let json_path = std::env::args().nth(1).expect("Usage: blur-benchmark <json_file_path>");
    let json_str = fs::read_to_string(&json_path)?;
    let data: Value = serde_json::from_str(&json_str)?;

    let original = data["original"].as_array().unwrap();
    let blurred = data["blurred"].as_array().unwrap();

    let mut w_r_vals = Vec::new();
    let mut x_r_vals = Vec::new();

    // Load original image
    for row in original {
        let row_array = row.as_array().unwrap();
        let mut pixel_row = Vec::new();
        for pixel in row_array {
            pixel_row.push(pixel.as_u64().unwrap() as usize);
        }
        w_r_vals.push(pixel_row);
    }

    // Load blurred image
    for row in blurred {
        let row_array = row.as_array().unwrap();
        let mut pixel_row = Vec::new();
        for pixel in row_array {
            pixel_row.push(pixel.as_u64().unwrap() as usize);
        }
        x_r_vals.push(pixel_row);
    }

    // Verify dimensions match
    if w_r_vals.len() != H || w_r_vals[0].len() != W {
        panic!("Image dimensions mismatch: expected {}x{}, got {}x{}", 
               H, W, w_r_vals.len(), w_r_vals[0].len());
    }
    if x_r_vals.len() != H || x_r_vals[0].len() != W {
        panic!("Blurred image dimensions mismatch: expected {}x{}, got {}x{}", 
               H, W, x_r_vals.len(), x_r_vals[0].len());
    }

    // Circuit build time (equivalent to VIMz "Key Generation")
    let circuit_start = Instant::now();
    let config = CircuitConfig::standard_recursion_config();
    let mut builder = CircuitBuilder::<F, D>::new(config);

    let mut w_r_targets = Vec::new();
    for _ in 0..H {
        let mut w_r_target_row = Vec::new();
        for _ in 0..W {
            let w_r = builder.add_virtual_target();
            w_r_target_row.push(w_r);
        }  
        w_r_targets.push(w_r_target_row);       
    }

    let mut x_r_targets = Vec::new();
    for i in 0..H {
        let mut x_r_target_row = Vec::new();
        for j in 0..W {
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
                

                let s_r = builder.add_many(all_r);

                // add 4 this so that remainder moves from value in [-4,4] to value in [0,8]
                let s_r_shift = builder.add_const(s_r, F::from_canonical_u32(4));
                
                let x_r = builder.add_virtual_target();
                x_r_target_row.push(x_r);
                let x_r_times_9 = builder.mul_const(F::from_canonical_u32(9), x_r);

                let rem_r = builder.sub(s_r_shift, x_r_times_9);

                // To check that rem \in [0, 8], we must check that rem < 2^4 and that
                // rem + 7 < 2^4
                builder.range_check(rem_r, 4);
                let rem_r_plus_7 = builder.add_const(rem_r, F::from_canonical_u32(7));
                builder.range_check(rem_r_plus_7, 4);

            }
            else {
                builder.register_public_input(w_r_targets[i][j]);
            } 
        }
        if x_r_target_row.len() > 0 {
             x_r_targets.push(x_r_target_row);
        }
    }
    
    let data = builder.build::<C>();
    let circuit_time = circuit_start.elapsed();

    // Get circuit statistics
    let num_gates = data.common.gates.len();
    // Calculate number of variables: H*W input pixels + (BLUR_H*BLUR_W) blurred output pixels
    let num_variables = H * W + BLUR_H * BLUR_W;

    // Output metrics in VIMz-compatible format
    println!("Circuit build took: {:.9}s", circuit_time.as_secs_f64());
    println!("Number of constraints: {}", num_gates);
    println!("Number of variables: {}", num_variables);

    // Proof generation time (equivalent to VIMz "RecursiveSNARK creation")
    let proof_start = Instant::now();
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


    let proof = data.prove(pw)?;
    let proof_time = proof_start.elapsed();
    println!("Proof generation took: {:.9}s", proof_time.as_secs_f64());

    let mut ctr = 0;
    for i in 0..H {
        for j in 0..W {
            if !(i > 0 && i < 1 + BLUR_H && j > 0 && j < 1 + BLUR_W) {
                // Public inputs are the original border pixels (w_r_vals), not blurred ones
                assert!(w_r_vals[i][j] as u64 == proof.public_inputs[ctr].0,
                    "Public input mismatch at ({}, {}): expected {}, got {}", 
                    i, j, w_r_vals[i][j], proof.public_inputs[ctr].0);
                ctr += 1;
            }

        }
    }

    // Verification time (equivalent to VIMz "RecursiveSNARK verify")
    let verify_start = Instant::now();
    let res = data.verify(proof);
    let _ = res?;
    let verify_time = verify_start.elapsed();
    println!("Verification took: {:.9}ms", verify_time.as_secs_f64() * 1000.0);

    Ok(())
}
