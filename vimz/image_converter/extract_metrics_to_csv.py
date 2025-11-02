#!/usr/bin/env python3
"""
Extract timing metrics from proof generation logs and save as CSV.
"""

import json
import csv
import sys
import glob
from pathlib import Path


def extract_metrics_from_log(log_file):
    """Extract metrics from a single log file."""
    metrics = {
        "file": Path(log_file).stem.replace("_output", ""),
        "key_generation_s": None,
        "recursive_creation_s": None,
        "recursive_verify_ms": None,
        "compressed_prove_s": None,
        "compressed_verify_ms": None,
        "primary_constraints": None,
        "primary_variables": None,
        "peak_memory_kb": None,
        "peak_memory_mb": None,
    }
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            
        for line in lines:
            if "Creating keys from R1CS took" in line:
                try:
                    time_str = line.split("took")[1].strip().replace("s", "")
                    metrics["key_generation_s"] = float(time_str)
                except:
                    pass
            
            elif "RecursiveSNARK creation took" in line:
                try:
                    time_str = line.split("took")[1].strip().replace("s", "")
                    metrics["recursive_creation_s"] = float(time_str)
                except:
                    pass
            
            elif "RecursiveSNARK::verify:" in line and "took" in line:
                try:
                    # Extract the time (could be in seconds or ms)
                    time_part = line.split("took")[1].strip()
                    if "ms" in time_part or "us" in time_part:
                        time_str = time_part.replace("ms", "").replace("us", "").strip()
                        # Convert to ms
                        metrics["recursive_verify_ms"] = float(time_str)
                    else:
                        metrics["recursive_verify_ms"] = float(time_part.replace("s", "")) * 1000
                except:
                    pass
            
            elif "CompressedSNARK::prove:" in line and "took" in line:
                try:
                    time_str = line.split("took")[1].strip().replace("s", "")
                    metrics["compressed_prove_s"] = float(time_str)
                except:
                    pass
            
            elif "CompressedSNARK::verify:" in line and "took" in line:
                try:
                    time_part = line.split("took")[1].strip()
                    if "ms" in time_part or "us" in time_part:
                        time_str = time_part.replace("ms", "").replace("us", "").strip()
                        metrics["compressed_verify_ms"] = float(time_str)
                    else:
                        metrics["compressed_verify_ms"] = float(time_part.replace("s", "")) * 1000
                except:
                    pass
            
            elif "Number of constraints per step (primary circuit):" in line:
                try:
                    metrics["primary_constraints"] = int(line.split(":")[1].strip())
                except:
                    pass
            
            elif "Number of variables per step (primary circuit):" in line:
                try:
                    metrics["primary_variables"] = int(line.split(":")[1].strip())
                except:
                    pass
            
            elif "Maximum resident set size (kbytes):" in line:
                try:
                    # Extract the memory value (format: "Maximum resident set size (kbytes): 123456")
                    memory_str = line.split(":")[1].strip()
                    metrics["peak_memory_kb"] = int(memory_str)
                    # Also calculate MB
                    metrics["peak_memory_mb"] = round(metrics["peak_memory_kb"] / 1024.0, 2)
                except:
                    pass
    
    except Exception as e:
        print(f"Error reading {log_file}: {e}")
    
    return metrics


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_metrics_to_csv.py <log_directory> [output_csv]")
        print("Example: python3 extract_metrics_to_csv.py resize/proofs/ results.csv")
        sys.exit(1)
    
    log_dir = Path(sys.argv[1])
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "metrics_results.csv"
    
    # Find all log files
    log_files = list(log_dir.glob("*_output.log"))
    
    if not log_files:
        print(f"No log files found in {log_dir}")
        sys.exit(1)
    
    print(f"Found {len(log_files)} log file(s)")
    
    # Extract metrics from each log
    all_metrics = []
    for log_file in sorted(log_files):
        metrics = extract_metrics_from_log(log_file)
        all_metrics.append(metrics)
    
    # Write to CSV
    fieldnames = [
        "file",
        "key_generation_s",
        "recursive_creation_s",
        "recursive_verify_ms",
        "compressed_prove_s",
        "compressed_verify_ms",
        "primary_constraints",
        "primary_variables",
        "peak_memory_kb",
        "peak_memory_mb",
    ]
    
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for metrics in all_metrics:
            writer.writerow(metrics)
    
    print(f"✓ Metrics saved to: {output_csv}")
    
    # Print summary
    if all_metrics:
        print("\nSummary:")
        print("-" * 60)
        key_gen_times = [m["key_generation_s"] for m in all_metrics if m["key_generation_s"] is not None]
        recursive_times = [m["recursive_creation_s"] for m in all_metrics if m["recursive_creation_s"] is not None]
        
        if key_gen_times:
            print(f"Key Generation: avg={sum(key_gen_times)/len(key_gen_times):.2f}s")
        if recursive_times:
            print(f"Recursive Creation: avg={sum(recursive_times)/len(recursive_times):.2f}s")


if __name__ == '__main__':
    main()

