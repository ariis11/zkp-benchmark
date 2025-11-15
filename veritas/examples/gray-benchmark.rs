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
    let json_path = std::env::args().nth(1).expect("Usage: gray-benchmark <json_file_path>");
    let json_str = fs::read_to_string(&json_path)?;
    let data: Value = serde_json::from_str(&json_str)?;

    let original = data["original"].as_array().unwrap();
    let grayscale = data["grayscale"].as_array().unwrap();

    let mut r_vals = Vec::new();
    let mut g_vals = Vec::new();
    let mut b_vals = Vec::new();
    let mut x_vals = Vec::new();
    let mut rem_vals = Vec::new();

    // Load original RGB image and grayscale
    let height = original.len();
    let width = original[0].as_array().unwrap().len();
    let total_pixels = height * width;

    for row in original {
        let row_array = row.as_array().unwrap();
        for pixel in row_array {
            let rgb = pixel.as_array().unwrap();
            r_vals.push(rgb[0].as_u64().unwrap() as u32);
            g_vals.push(rgb[1].as_u64().unwrap() as u32);
            b_vals.push(rgb[2].as_u64().unwrap() as u32);
        }
    }

    for row in grayscale {
        let row_array = row.as_array().unwrap();
        for pixel in row_array {
            x_vals.push(pixel.as_u64().unwrap() as u32);
        }
    }

    // Compute remainders using VIMz formula: (299*R + 587*G + 114*B) / 1000
    // Veritas circuit uses: (299*R + 587*G + 114*B) - 1000*x
    for i in 0..total_pixels {
        let sum = (r_vals[i] as u32 * 299 + g_vals[i] as u32 * 587 + b_vals[i] as u32 * 114) as i32;
        let expected = (sum / 1000) as u32;
        let remainder = sum - (expected as i32 * 1000);
        rem_vals.push(remainder);
        
        // Verify the grayscale value matches
        assert_eq!(x_vals[i], expected, "Grayscale value mismatch at pixel {}", i);
    }

    // Circuit build time (equivalent to VIMz "Key Generation")
    let circuit_start = Instant::now();
    let mut config = CircuitConfig::standard_recursion_config();
    config.zero_knowledge = true;
    let mut builder = CircuitBuilder::<F, D>::new(config);

    let mut pw = PartialWitness::new();

    let mut r_targets = Vec::new();
    let mut g_targets = Vec::new();
    let mut b_targets = Vec::new();

    for _ in 0..total_pixels {
        let r = builder.add_virtual_target();
        r_targets.push(r);

        let g = builder.add_virtual_target();
        g_targets.push(g);

        let b = builder.add_virtual_target();
        b_targets.push(b);

        let mut all = Vec::new();

        // VIMz formula: 299*R + 587*G + 114*B
        all.push(builder.mul_const(F::from_canonical_u32(299), r));
        all.push(builder.mul_const(F::from_canonical_u32(587), g));
        all.push(builder.mul_const(F::from_canonical_u32(114), b));

        let s = builder.add_many(all);
        builder.register_public_input(s);
    }

    let data = builder.build::<C>();
    let circuit_time = circuit_start.elapsed();

    // Get circuit statistics
    let num_gates = data.common.gates.len();
    let num_variables = total_pixels * 3; // R, G, B for each pixel

    // Output metrics in VIMz-compatible format
    println!("Circuit build took: {:.9}s", circuit_time.as_secs_f64());
    println!("Number of constraints: {}", num_gates);
    println!("Number of variables: {}", num_variables);

    // Proof generation time (equivalent to VIMz "RecursiveSNARK creation")
    let proof_start = Instant::now();

    for i in 0..total_pixels {
        pw.set_target(r_targets[i], F::from_canonical_u32(r_vals[i]));
        pw.set_target(g_targets[i], F::from_canonical_u32(g_vals[i]));
        pw.set_target(b_targets[i], F::from_canonical_u32(b_vals[i]));
    }

    let proof = data.prove(pw)?;
    let proof_time = proof_start.elapsed();
    println!("Proof generation took: {:.9}s", proof_time.as_secs_f64());

    // Verification time (equivalent to VIMz "RecursiveSNARK verify")
    let verify_start = Instant::now();

    for i in 0..total_pixels {
        let expected_sum = (r_vals[i] as i32 * 299 + g_vals[i] as i32 * 587 + b_vals[i] as i32 * 114) as u64;
        assert!(proof.public_inputs[i].0 == expected_sum,
            "Public input mismatch at pixel {}: expected {}, got {}",
            i, expected_sum, proof.public_inputs[i].0);
    }

    let res = data.verify(proof);
    let _ = res?;
    let verify_time = verify_start.elapsed();
    println!("Verification took: {:.9}ms", verify_time.as_secs_f64() * 1000.0);

    Ok(())
}
