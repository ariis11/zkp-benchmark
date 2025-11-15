use anyhow::Result;
use plonky2::field::types::Field;
use plonky2::iop::witness::{PartialWitness, WitnessWrite};
use plonky2::plonk::circuit_builder::CircuitBuilder;
use plonky2::plonk::circuit_data::CircuitConfig;
use plonky2::plonk::config::{GenericConfig, PoseidonGoldilocksConfig};
use serde_json::Value;
use std::fs;
use std::time::Instant; 

fn main() -> Result<()> {
    const D: usize = 2;
    type C = PoseidonGoldilocksConfig;
    type F = <C as GenericConfig<D>>::F;

    // Load image data from JSON
    let json_path = std::env::args().nth(1).expect("Usage: crop-benchmark <json_file_path>");
    let json_str = fs::read_to_string(&json_path)?;
    let data: Value = serde_json::from_str(&json_str)?;

    let original = data["original"].as_array().unwrap();
    let cropped = data["cropped"].as_array().unwrap();
    let crop_x = data["crop_x"].as_u64().unwrap() as usize;
    let crop_y = data["crop_y"].as_u64().unwrap() as usize;

    let mut w_r_vals = Vec::new();
    let mut x_r_vals = Vec::new();

    // Load original image
    for row in original {
        let row_array = row.as_array().unwrap();
        let mut pixel_row = Vec::new();
        for pixel in row_array {
            pixel_row.push(pixel.as_u64().unwrap() as u32);
        }
        w_r_vals.push(pixel_row);
    }

    // Load cropped image
    for row in cropped {
        let row_array = row.as_array().unwrap();
        let mut pixel_row = Vec::new();
        for pixel in row_array {
            pixel_row.push(pixel.as_u64().unwrap() as u32);
        }
        x_r_vals.push(pixel_row);
    }

    let OLD_SIZE = w_r_vals.len() * w_r_vals[0].len();
    let NEW_SIZE = x_r_vals.len() * x_r_vals[0].len();

    // Flatten to 1D arrays (matching original crop.rs logic)
    let mut w_r_vals_flat = Vec::new();
    for row in &w_r_vals {
        for &pixel in row {
            w_r_vals_flat.push(pixel);
        }
    }

    let mut x_r_vals_flat = Vec::new();
    for row in &x_r_vals {
        for &pixel in row {
            x_r_vals_flat.push(pixel);
        }
    }

    // Extract the cropped region from original (starting at crop_x, crop_y)
    let orig_width = w_r_vals[0].len();
    let crop_width = x_r_vals[0].len();
    let crop_height = x_r_vals.len();
    
    let mut expected_cropped = Vec::new();
    for i in 0..crop_height {
        for j in 0..crop_width {
            let orig_row = crop_y + i;
            let orig_col = crop_x + j;
            expected_cropped.push(w_r_vals[orig_row][orig_col]);
        }
    }

    // Verify cropped matches expected
    if x_r_vals_flat != expected_cropped {
        panic!("Cropped values don't match expected region from original");
    }

    // Circuit build time (equivalent to VIMz "Key Generation")
    let circuit_start = Instant::now();
    let mut config = CircuitConfig::standard_recursion_config();
    config.zero_knowledge = true;
    let mut builder = CircuitBuilder::<F, D>::new(config);

    let mut pw = PartialWitness::new();

    let mut w_r_targets = Vec::new();

    for _ in 0..NEW_SIZE {
        let r = builder.add_virtual_target();
        w_r_targets.push(r);
        builder.register_public_input(r);    
    }

    let data = builder.build::<C>();
    let circuit_time = circuit_start.elapsed();

    // Get circuit statistics
    let num_gates = data.common.gates.len();
    let num_variables = NEW_SIZE;

    // Output metrics in VIMz-compatible format
    println!("Circuit build took: {:.9}s", circuit_time.as_secs_f64());
    println!("Number of constraints: {}", num_gates);
    println!("Number of variables: {}", num_variables);

    // Proof generation time (equivalent to VIMz "RecursiveSNARK creation")
    let proof_start = Instant::now();

    for i in 0..NEW_SIZE {
        pw.set_target(w_r_targets[i], F::from_canonical_u32(x_r_vals_flat[i]));
    }

    let proof = data.prove(pw)?;
    let proof_time = proof_start.elapsed();
    println!("Proof generation took: {:.9}s", proof_time.as_secs_f64());

    // Verification time (equivalent to VIMz "RecursiveSNARK verify")
    let verify_start = Instant::now();

    for i in 0..proof.public_inputs.len() {
        assert!((proof.public_inputs[i].0) as u32 == x_r_vals_flat[i]);
    }

    let res = data.verify(proof);
    let _ = res?;
    let verify_time = verify_start.elapsed();
    println!("Verification took: {:.9}ms", verify_time.as_secs_f64() * 1000.0);

    Ok(())
}
