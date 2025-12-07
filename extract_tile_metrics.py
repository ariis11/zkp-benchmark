#!/usr/bin/env python3
"""
Extract metrics from Tile-Based proof generation log files and output to CSV.

Usage:
    python3 extract_tile_metrics.py <proofs_directory> [output_csv]

Example:
    python3 extract_tile_metrics.py tile-based/benchmark/grayscale/proofs_laptop_hd
    python3 extract_tile_metrics.py tile-based/benchmark/grayscale/proofs_laptop_hd results.csv
"""

import re
import sys
import csv
from pathlib import Path
from typing import Dict, Optional


def extract_metric(line: str, pattern: str, default: Optional[float] = None) -> Optional[float]:
    """Extract a numeric value from a line using a regex pattern."""
    match = re.search(pattern, line)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            return default
    return default


def parse_tile_log(log_file: Path) -> Dict[str, Optional[float]]:
    """
    Parse a Tile-Based output log file and extract metrics.
    
    Returns a dictionary with the following keys:
    - circuit_build_time_s
    - total_proof_generation_time_s
    - average_proof_time_per_tile_s
    - total_verification_time_ms
    - average_verification_time_per_tile_ms
    - num_tiles
    - constraints
    - variables_per_tile
    - peak_memory_kb
    - peak_memory_mb
    """
    metrics = {
        'circuit_build_time_s': None,
        'total_proof_generation_time_s': None,
        'average_proof_time_per_tile_s': None,
        'total_verification_time_ms': None,
        'average_verification_time_per_tile_ms': None,
        'num_tiles': None,
        'constraints': None,
        'variables_per_tile': None,
        'peak_memory_kb': None,
        'peak_memory_mb': None,
    }
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        for line in lines:
            # Circuit build time: "Circuit build took: 3.8s"
            if 'Circuit build took:' in line:
                value = extract_metric(line, r'Circuit build took:\s*([0-9.]+)s')
                if value is not None:
                    metrics['circuit_build_time_s'] = value
            
            # Total proof generation time: "Total proof generation time: 95.4s"
            elif 'Total proof generation time:' in line:
                value = extract_metric(line, r'Total proof generation time:\s*([0-9.]+)s')
                if value is not None:
                    metrics['total_proof_generation_time_s'] = value
            
            # Average proof time per tile: "Average proof time per tile: 7.95s"
            elif 'Average proof time per tile:' in line:
                value = extract_metric(line, r'Average proof time per tile:\s*([0-9.]+)s')
                if value is not None:
                    metrics['average_proof_time_per_tile_s'] = value
            
            # Total verification time: "Total verification time: 12.5ms"
            elif 'Total verification time:' in line:
                value = extract_metric(line, r'Total verification time:\s*([0-9.]+)ms')
                if value is not None:
                    metrics['total_verification_time_ms'] = value
            
            # Average verification time per tile: "Average verification time per tile: 1.04ms"
            elif 'Average verification time per tile:' in line:
                value = extract_metric(line, r'Average verification time per tile:\s*([0-9.]+)ms')
                if value is not None:
                    metrics['average_verification_time_per_tile_ms'] = value
            
            # Number of tiles: "Total tiles processed: 12"
            elif 'Total tiles processed:' in line:
                value = extract_metric(line, r'Total tiles processed:\s*([0-9]+)')
                if value is not None:
                    metrics['num_tiles'] = int(value)
            
            # Number of constraints: "Number of constraints: 245760"
            elif 'Number of constraints:' in line:
                value = extract_metric(line, r'Number of constraints:\s*([0-9]+)')
                if value is not None:
                    metrics['constraints'] = int(value)
            
            # Variables per tile: "Variables per tile: 245760"
            elif 'Variables per tile:' in line:
                value = extract_metric(line, r'Variables per tile:\s*([0-9]+)')
                if value is not None:
                    metrics['variables_per_tile'] = int(value)
            
            # Peak memory: "Maximum resident set size (kbytes): 4400296"
            elif 'Maximum resident set size (kbytes):' in line:
                value = extract_metric(line, r'Maximum resident set size \(kbytes\):\s*([0-9]+)')
                if value is not None:
                    metrics['peak_memory_kb'] = int(value)
                    metrics['peak_memory_mb'] = round(value / 1024.0, 2)
                    metrics['peak_memory_gb'] = round(value / (1024.0 * 1024.0), 3)
    
    except Exception as e:
        print(f"Error reading {log_file}: {e}", file=sys.stderr)
    
    return metrics


def find_log_files(directory: Path) -> list:
    """Find all passport_xxxx_output.log files in the directory."""
    log_files = sorted(directory.glob('passport_*_output.log'))
    return log_files


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_tile_metrics.py <proofs_directory> [output_csv]")
        print("\nExample:")
        print("  python3 extract_tile_metrics.py tile-based/benchmark/grayscale/proofs_laptop_hd")
        print("  python3 extract_tile_metrics.py tile-based/benchmark/grayscale/proofs_laptop_hd results.csv")
        sys.exit(1)
    
    proofs_dir = Path(sys.argv[1])
    if not proofs_dir.exists():
        print(f"Error: Directory not found: {proofs_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Determine output file
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        # Default: use directory name + _metrics.csv
        output_file = proofs_dir.parent / f"{proofs_dir.name}_metrics.csv"
    
    # Find all log files
    log_files = find_log_files(proofs_dir)
    
    if not log_files:
        print(f"Error: No passport_*_output.log files found in {proofs_dir}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(log_files)} log files in {proofs_dir}")
    print(f"Output will be written to: {output_file}")
    
    # Extract metrics from all log files
    all_metrics = []
    failed_files = []
    
    for log_file in log_files:
        # Extract passport number from filename (e.g., passport_0000_output.log -> 0000)
        passport_match = re.search(r'passport_(\d+)_output\.log', log_file.name)
        if passport_match:
            passport_num = passport_match.group(1)
        else:
            passport_num = log_file.stem
        
        metrics = parse_tile_log(log_file)
        metrics['file'] = log_file.name
        metrics['passport_id'] = passport_num
        
        # Check if we got at least some metrics
        if any(v is not None for k, v in metrics.items() if k not in ['file', 'passport_id']):
            all_metrics.append(metrics)
        else:
            failed_files.append(log_file.name)
    
    if failed_files:
        print(f"Warning: Could not extract metrics from {len(failed_files)} files:", file=sys.stderr)
        for f in failed_files[:5]:  # Show first 5
            print(f"  - {f}", file=sys.stderr)
        if len(failed_files) > 5:
            print(f"  ... and {len(failed_files) - 5} more", file=sys.stderr)
    
    if not all_metrics:
        print("Error: No metrics extracted from any files", file=sys.stderr)
        sys.exit(1)
    
    # Write to CSV
    fieldnames = [
        'passport_id',
        'file',
        'num_tiles',
        'circuit_build_time_s',
        'total_proof_generation_time_s',
        'average_proof_time_per_tile_s',
        'total_verification_time_ms',
        'average_verification_time_per_tile_ms',
        'constraints',
        'variables_per_tile',
        'peak_memory_kb',
        'peak_memory_mb',
        'peak_memory_gb',
    ]
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for metrics in all_metrics:
            # Only include defined fieldnames
            row = {k: metrics.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    print(f"\n✓ Successfully extracted metrics from {len(all_metrics)} files")
    print(f"✓ CSV written to: {output_file}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("-" * 60)
    
    numeric_fields = [
        'num_tiles',
        'circuit_build_time_s',
        'total_proof_generation_time_s',
        'average_proof_time_per_tile_s',
        'total_verification_time_ms',
        'average_verification_time_per_tile_ms',
        'constraints',
        'variables_per_tile',
        'peak_memory_mb',
    ]
    
    for field in numeric_fields:
        values = [m[field] for m in all_metrics if m.get(field) is not None]
        if values:
            mean_val = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            print(f"{field:40s}: mean={mean_val:12.3f}, min={min_val:12.3f}, max={max_val:12.3f} ({len(values)} values)")


if __name__ == '__main__':
    main()

