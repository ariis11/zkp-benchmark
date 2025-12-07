use anyhow::Result;
use plonky2::field::types::Field;
use plonky2::iop::witness::{PartialWitness, WitnessWrite};
use plonky2::plonk::circuit_builder::CircuitBuilder;
use plonky2::plonk::circuit_data::{CircuitConfig, CircuitData};
use plonky2::plonk::config::{GenericConfig, PoseidonGoldilocksConfig};
use plonky2::iop::target::Target;
use serde_json::Value;
use std::fs;
use std::time::Instant;

const D: usize = 2;
type C = PoseidonGoldilocksConfig;
type F = <C as GenericConfig<D>>::F;

/// Calculate tile boundaries for a given image height and tile height.
/// Returns a vector of (row_start, row_end) tuples.
/// Example: height=720, tile_height=64 → [(0,64), (64,128), ..., (704,720)]
fn calculate_tiles(height: usize, tile_height: usize) -> Vec<(usize, usize)> {
    let mut tiles = Vec::new();
    let mut row_start = 0;
    
    while row_start < height {
        let row_end = (row_start + tile_height).min(height);
        tiles.push((row_start, row_end));
        row_start = row_end;
    }
    
    tiles
}

/// Build a grayscale tile circuit for a given tile size.
/// Returns the circuit data and target vectors for R, G, B channels.
fn build_grayscale_tile_circuit(
    config: CircuitConfig,
    tile_height: usize,
    width: usize,
) -> (
    CircuitData<F, C, D>,
    Vec<Target>,
    Vec<Target>,
    Vec<Target>,
) {
    let mut builder = CircuitBuilder::<F, D>::new(config);
    
    let tile_pixels = tile_height * width;
    let mut r_targets = Vec::new();
    let mut g_targets = Vec::new();
    let mut b_targets = Vec::new();
    
    for _ in 0..tile_pixels {
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
    
    let circuit_data = builder.build::<C>();
    (circuit_data, r_targets, g_targets, b_targets)
}

fn main() -> Result<()> {
    // Parse command-line arguments
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: gray-tiled-benchmark <json_file_path> [tile_height]");
        eprintln!("  tile_height: Height of each tile in rows (default: 64)");
        std::process::exit(1);
    }
    
    let json_path = &args[1];
    let tile_height: usize = args.get(2)
        .and_then(|s| s.parse().ok())
        .unwrap_or(64);  // Default: 64 rows per tile

    println!("=========================================");
    println!("Tile-Based Grayscale Proof Generation");
    println!("=========================================");
    println!("JSON file: {}", json_path);
    println!("Tile height: {} rows", tile_height);
    println!("=========================================");

    // Load image data from JSON
    let json_str = fs::read_to_string(json_path)?;
    let data: Value = serde_json::from_str(&json_str)?;

    let original = data["original"].as_array().unwrap();
    let grayscale = data["grayscale"].as_array().unwrap();

    // Load original RGB image and grayscale as 2D arrays (rows)
    let height = original.len();
    let width = original[0].as_array().unwrap().len();
    
    // Store image data as 2D: [row][col]
    let mut original_rgb: Vec<Vec<(u32, u32, u32)>> = Vec::new();
    let mut grayscale_vals: Vec<Vec<u32>> = Vec::new();

    for row in original {
        let row_array = row.as_array().unwrap();
        let mut rgb_row = Vec::new();
        for pixel in row_array {
            let rgb = pixel.as_array().unwrap();
            rgb_row.push((
                rgb[0].as_u64().unwrap() as u32,
                rgb[1].as_u64().unwrap() as u32,
                rgb[2].as_u64().unwrap() as u32,
            ));
        }
        original_rgb.push(rgb_row);
    }

    for row in grayscale {
        let row_array = row.as_array().unwrap();
        let mut gray_row = Vec::new();
        for pixel in row_array {
            gray_row.push(pixel.as_u64().unwrap() as u32);
        }
        grayscale_vals.push(gray_row);
    }

    // Verify grayscale values match expected formula
    for i in 0..height {
        for j in 0..width {
            let (r, g, b) = original_rgb[i][j];
            let sum = (r as u32 * 299 + g as u32 * 587 + b as u32 * 114) as i32;
            let expected = (sum / 1000) as u32;
            assert_eq!(grayscale_vals[i][j], expected, 
                "Grayscale value mismatch at ({}, {})", i, j);
        }
    }

    println!("Image dimensions: {}x{} pixels", height, width);
    
    // Calculate tiles
    let tiles = calculate_tiles(height, tile_height);
    let num_tiles = tiles.len();
    println!("Number of tiles: {}", num_tiles);
    println!("");

    // Build circuit once (reusable for all tiles)
    println!("Building tile circuit ({}x{} pixels per tile)...", tile_height, width);
    let circuit_start = Instant::now();
    let mut config = CircuitConfig::standard_recursion_config();
    config.zero_knowledge = true;
    
    let (circuit_data, r_targets, g_targets, b_targets) = build_grayscale_tile_circuit(
        config,
        tile_height,
        width,
    );
    let circuit_time = circuit_start.elapsed();
    
    let num_gates = circuit_data.common.gates.len();
    let tile_pixels = tile_height * width;
    let num_variables = tile_pixels * 3; // R, G, B for each pixel

    println!("Circuit build took: {:.9}s", circuit_time.as_secs_f64());
    println!("Number of constraints: {}", num_gates);
    println!("Number of variables per tile: {}", num_variables);
    println!("");

    // Process each tile
    let mut total_proof_time = std::time::Duration::ZERO;
    let mut total_verify_time = std::time::Duration::ZERO;
    let mut all_proofs = Vec::new();

    for (tile_idx, (row_start, row_end)) in tiles.iter().enumerate() {
        let actual_tile_height = row_end - row_start;
        println!("Processing tile {}/{} (rows {}..{})", 
                 tile_idx + 1, num_tiles, row_start, row_end);

        // Extract tile data
        let mut tile_r_vals = Vec::new();
        let mut tile_g_vals = Vec::new();
        let mut tile_b_vals = Vec::new();

        for row_idx in *row_start..*row_end {
            for col_idx in 0..width {
                let (r, g, b) = original_rgb[row_idx][col_idx];
                tile_r_vals.push(r);
                tile_g_vals.push(g);
                tile_b_vals.push(b);
            }
        }

        let tile_pixel_count = actual_tile_height * width;
        
        // If this tile is smaller than tile_height, pad with zeros to match circuit size
        // (The circuit expects tile_height * width pixels, but last tile might be smaller)
        let mut padded_r = tile_r_vals.clone();
        let mut padded_g = tile_g_vals.clone();
        let mut padded_b = tile_b_vals.clone();
        
        if actual_tile_height < tile_height {
            let padding_needed = (tile_height - actual_tile_height) * width;
            padded_r.extend(vec![0; padding_needed]);
            padded_g.extend(vec![0; padding_needed]);
            padded_b.extend(vec![0; padding_needed]);
        }
        
        // Build witness for this tile (using full tile_height * width size)
        let mut pw = PartialWitness::new();
        for i in 0..tile_pixels {
            pw.set_target(r_targets[i], F::from_canonical_u32(padded_r[i]));
            pw.set_target(g_targets[i], F::from_canonical_u32(padded_g[i]));
            pw.set_target(b_targets[i], F::from_canonical_u32(padded_b[i]));
        }

        // Generate proof
        let proof_start = Instant::now();
        let proof = circuit_data.prove(pw)?;
        let proof_time = proof_start.elapsed();
        total_proof_time += proof_time;

        // Verify proof
        let verify_start = Instant::now();
        
        // Verify public inputs match expected values (only check actual pixels, not padding)
        for i in 0..tile_pixel_count {
            let expected_sum = (tile_r_vals[i] as i32 * 299 + 
                               tile_g_vals[i] as i32 * 587 + 
                               tile_b_vals[i] as i32 * 114) as u64;
            assert!(proof.public_inputs[i].0 == expected_sum,
                "Public input mismatch at tile {} pixel {}: expected {}, got {}",
                tile_idx, i, expected_sum, proof.public_inputs[i].0);
        }
        
        // For padded pixels, verify they compute to 0 (since we padded with zeros)
        if actual_tile_height < tile_height {
            for i in tile_pixel_count..tile_pixels {
                assert!(proof.public_inputs[i].0 == 0,
                    "Padded pixel at tile {} index {} should be 0, got {}",
                    tile_idx, i, proof.public_inputs[i].0);
            }
        }

        let verify_result = circuit_data.verify(proof.clone());
        verify_result?;
        let verify_time = verify_start.elapsed();
        total_verify_time += verify_time;

        println!("  Proof generation: {:.9}s", proof_time.as_secs_f64());
        println!("  Verification: {:.9}ms", verify_time.as_secs_f64() * 1000.0);
        
        all_proofs.push((tile_idx, *row_start, *row_end, proof));
        println!("");
    }

    // Summary
    println!("=========================================");
    println!("Summary");
    println!("=========================================");
    println!("Total tiles processed: {}", num_tiles);
    println!("Circuit build time: {:.9}s", circuit_time.as_secs_f64());
    println!("Total proof generation time: {:.9}s", total_proof_time.as_secs_f64());
    println!("Average proof time per tile: {:.9}s", 
             total_proof_time.as_secs_f64() / num_tiles as f64);
    println!("Total verification time: {:.9}ms", total_verify_time.as_secs_f64() * 1000.0);
    println!("Average verification time per tile: {:.9}ms", 
             total_verify_time.as_secs_f64() * 1000.0 / num_tiles as f64);
    println!("Variables per tile: {} (vs {} for full image)", 
             num_variables, height * width * 3);
    println!("=========================================");

    Ok(())
}
