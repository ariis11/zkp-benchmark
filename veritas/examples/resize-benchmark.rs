use anyhow::Result;
use plonky2::field::types::Field;
use plonky2::iop::witness::{PartialWitness, WitnessWrite};
use plonky2::plonk::circuit_builder::CircuitBuilder;
use plonky2::plonk::circuit_data::CircuitConfig;
use plonky2::plonk::config::{GenericConfig, PoseidonGoldilocksConfig};
use serde_json::Value;
use std::fs;
use std::time::Instant;

fn get_positions(i: usize, j: usize, w_orig: usize, h_orig: usize, w_new: usize, h_new: usize) -> (usize, usize, usize, usize) {
    let x_l = if w_new > 1 { (w_orig - 1) * j / (w_new - 1) } else { 0 };
    let y_l = if h_new > 1 { (h_orig - 1) * i / (h_new - 1) } else { 0 };

    let x_h = if w_new > 1 && x_l * (w_new - 1) == (w_orig - 1) * j { x_l } else { (x_l + 1).min(w_orig - 1) };
    let y_h = if h_new > 1 && y_l * (h_new - 1) == (h_orig - 1) * i { y_l } else { (y_l + 1).min(h_orig - 1) };

    return (x_l, y_l, x_h, y_h);
}

fn get_ratios(i: usize, j: usize, w_orig: usize, h_orig: usize, w_new: usize, h_new: usize) -> (usize, usize) {
    let x_ratio_weighted = if w_new > 1 {
        ((w_orig - 1) * j) - (w_new - 1) * ((w_orig - 1) * j / (w_new - 1))
    } else {
        0
    };
    let y_ratio_weighted = if h_new > 1 {
        ((h_orig - 1) * i) - (h_new - 1) * ((h_orig - 1) * i / (h_new - 1))
    } else {
        0
    };
    return (x_ratio_weighted, y_ratio_weighted);
}

fn main() -> Result<()> {
    const D: usize = 2;
    type C = PoseidonGoldilocksConfig;
    type F = <C as GenericConfig<D>>::F;

    // Load image data from JSON
    let json_path = std::env::args().nth(1).expect("Usage: resize-benchmark <json_file_path>");
    let json_str = fs::read_to_string(&json_path)?;
    let data: Value = serde_json::from_str(&json_str)?;

    let original = data["original"].as_array().unwrap();
    let resized = data["resized"].as_array().unwrap();

    let mut w_r_vals = Vec::new();
    let mut x_r_vals = Vec::new();
    let mut rem_r_vals = Vec::new();

    // Load original image
    for row in original {
        let row_array = row.as_array().unwrap();
        let mut pixel_row = Vec::new();
        for pixel in row_array {
            pixel_row.push(pixel.as_u64().unwrap() as u32);
        }
        w_r_vals.push(pixel_row);
    }

    // Load resized image
    for row in resized {
        let row_array = row.as_array().unwrap();
        let mut pixel_row = Vec::new();
        for pixel in row_array {
            pixel_row.push(pixel.as_u64().unwrap() as u32);
        }
        x_r_vals.push(pixel_row);
    }

    let H_ORIG = w_r_vals.len();
    let W_ORIG = w_r_vals[0].len();
    let H_NEW = x_r_vals.len();
    let W_NEW = x_r_vals[0].len();

    // Compute expected resized values and remainders (matching resize.rs logic)
    for i in 0..H_NEW {
        let mut rem_r_row = Vec::new();
        for j in 0..W_NEW {
            let (x_l, y_l, x_h, y_h) = get_positions(i, j, W_ORIG, H_ORIG, W_NEW, H_NEW);
            let (x_ratio_weighted, y_ratio_weighted) = get_ratios(i, j, W_ORIG, H_ORIG, W_NEW, H_NEW);

            let a = w_r_vals[y_l][x_l] as usize;
            let b = w_r_vals[y_l][x_h] as usize;
            let c = w_r_vals[y_h][x_l] as usize;
            let d = w_r_vals[y_h][x_h] as usize;

            let denom = if W_NEW > 1 && H_NEW > 1 { (W_NEW - 1) * (H_NEW - 1) } else { 1 };
            let s = a * (W_NEW - 1 - x_ratio_weighted) * (H_NEW - 1 - y_ratio_weighted) 
                    + b * x_ratio_weighted * (H_NEW - 1 - y_ratio_weighted) 
                    + c * y_ratio_weighted * (W_NEW - 1 - x_ratio_weighted) 
                    + d * x_ratio_weighted * y_ratio_weighted;

            let new = ((s as f64) / (denom as f64)).round() as usize;
            let r = s as i64 - (new * denom) as i64;
            
            rem_r_row.push(r);
        }
        rem_r_vals.push(rem_r_row);
    }

    // Circuit build time (equivalent to VIMz "Key Generation")
    let circuit_start = Instant::now();
    let mut config = CircuitConfig::standard_recursion_config();
    config.zero_knowledge = true;
    let mut builder = CircuitBuilder::<F, D>::new(config);

    let mut pw = PartialWitness::new();

    let mut w_r_targets = Vec::new();

    for i in 0..H_NEW {
        for j in 0..W_NEW {
            let a = builder.add_virtual_target();
            let b = builder.add_virtual_target();
            let c = builder.add_virtual_target();
            let d = builder.add_virtual_target();
            
            w_r_targets.push(a);
            w_r_targets.push(b);
            w_r_targets.push(c);
            w_r_targets.push(d);

            let (x_ratio_weighted, y_ratio_weighted) = get_ratios(i, j, W_ORIG, H_ORIG, W_NEW, H_NEW);

            let mut all = Vec::new();

            let _denom = if W_NEW > 1 && H_NEW > 1 { (W_NEW - 1) * (H_NEW - 1) } else { 1 };
            let a_const = ((W_NEW - 1 - x_ratio_weighted) * (H_NEW - 1 - y_ratio_weighted)) as u32;
            let b_const = (x_ratio_weighted * (H_NEW - 1 - y_ratio_weighted)) as u32;
            let c_const = (y_ratio_weighted * (W_NEW - 1 - x_ratio_weighted)) as u32;
            let d_const = (x_ratio_weighted * y_ratio_weighted) as u32;
            all.push(builder.mul_const(F::from_canonical_u32(a_const), a));
            all.push(builder.mul_const(F::from_canonical_u32(b_const), b));
            all.push(builder.mul_const(F::from_canonical_u32(c_const), c));
            all.push(builder.mul_const(F::from_canonical_u32(d_const), d));

            let s = builder.add_many(all);
            builder.register_public_input(s);
        }         
    }

    let data = builder.build::<C>();
    let circuit_time = circuit_start.elapsed();

    // Get circuit statistics
    let num_gates = data.common.gates.len();
    let num_variables = H_NEW * W_NEW * 4; // 4 corner pixels per output pixel

    // Output metrics in VIMz-compatible format
    println!("Circuit build took: {:.9}s", circuit_time.as_secs_f64());
    println!("Number of constraints: {}", num_gates);
    println!("Number of variables: {}", num_variables);

    // Proof generation time (equivalent to VIMz "RecursiveSNARK creation")
    let proof_start = Instant::now();

    for i in 0..H_NEW {
        for j in 0..W_NEW {
            let (x_l, y_l, x_h, y_h) = get_positions(i, j, W_ORIG, H_ORIG, W_NEW, H_NEW);

            pw.set_target(w_r_targets[4 * i * W_NEW + 4 * j], F::from_canonical_u32(w_r_vals[y_l][x_l]));
            pw.set_target(w_r_targets[4 * i * W_NEW + 4 * j + 1], F::from_canonical_u32(w_r_vals[y_l][x_h]));
            pw.set_target(w_r_targets[4 * i * W_NEW + 4 * j + 2], F::from_canonical_u32(w_r_vals[y_h][x_l]));
            pw.set_target(w_r_targets[4 * i * W_NEW + 4 * j + 3], F::from_canonical_u32(w_r_vals[y_h][x_h]));
        }
    }

    let proof = data.prove(pw)?;
    let proof_time = proof_start.elapsed();
    println!("Proof generation took: {:.9}s", proof_time.as_secs_f64());

    // Verification time (equivalent to VIMz "RecursiveSNARK verify")
    let verify_start = Instant::now();

    let denom = if W_NEW > 1 && H_NEW > 1 { (W_NEW - 1) * (H_NEW - 1) } else { 1 };

    for i in 0..H_NEW {
        for j in 0..W_NEW {
            let x = (x_r_vals[i][j] as usize * denom) as i64 + rem_r_vals[i][j];
            assert!(x as u64 == proof.public_inputs[W_NEW * i + j].0,
                "Public input mismatch at ({}, {}): expected {}, got {}",
                i, j, x, proof.public_inputs[W_NEW * i + j].0);
        }
    }

    let res = data.verify(proof);
    let _ = res?;
    let verify_time = verify_start.elapsed();
    println!("Verification took: {:.9}ms", verify_time.as_secs_f64() * 1000.0);

    Ok(())
}


