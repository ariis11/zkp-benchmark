#!/usr/bin/env python3
"""
Extract metrics from VIMz proof generation log files and output to CSV.

Usage:
    python3 extract_vimz_metrics.py <proofs_directory> [output_csv]

Example:
    python3 extract_vimz_metrics.py vimz/image_converter/blur/proofs_laptop_hd
    python3 extract_vimz_metrics.py vimz/image_converter/blur/proofs_laptop_hd results.csv
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


def parse_vimz_log(log_file: Path) -> Dict[str, Optional[float]]:
    """
    Parse a VIMz output log file and extract metrics.
    
    Returns a dictionary with the following keys:
    - key_generation_time_s
    - recursive_snark_creation_time_s
    - recursive_snark_verify_time_s
    - recursive_snark_verify_time_ms
    - compressed_snark_prove_time_s
    - compressed_snark_verify_time_s
    - compressed_snark_verify_time_ms
    - constraints_primary
    - variables_primary
    - constraints_secondary
    - variables_secondary
    - peak_memory_kb
    - peak_memory_mb
    - peak_memory_gb
    """
    metrics = {
        'key_generation_time_s': None,
        'recursive_snark_creation_time_s': None,
        'recursive_snark_verify_time_s': None,
        'recursive_snark_verify_time_ms': None,
        'compressed_snark_prove_time_s': None,
        'compressed_snark_verify_time_s': None,
        'compressed_snark_verify_time_ms': None,
        'constraints_primary': None,
        'variables_primary': None,
        'constraints_secondary': None,
        'variables_secondary': None,
        'peak_memory_kb': None,
        'peak_memory_mb': None,
        'peak_memory_gb': None,
    }
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        for line in lines:
            # Key generation time: "Creating keys from R1CS took 28.576486843s"
            if 'Creating keys from R1CS took' in line:
                value = extract_metric(line, r'Creating keys from R1CS took\s+([0-9.]+)s')
                if value is not None:
                    metrics['key_generation_time_s'] = value
            
            # RecursiveSNARK creation time: "RecursiveSNARK creation took 1190.833422077s"
            elif 'RecursiveSNARK creation took' in line:
                value = extract_metric(line, r'RecursiveSNARK creation took\s+([0-9.]+)s')
                if value is not None:
                    metrics['recursive_snark_creation_time_s'] = value
            
            # RecursiveSNARK verify time: "RecursiveSNARK::verify: ... took 1.596634548s"
            elif 'RecursiveSNARK::verify' in line and 'took' in line:
                # Try to extract time in seconds
                value = extract_metric(line, r'took\s+([0-9.]+)s')
                if value is None:
                    # Sometimes it's in milliseconds
                    value = extract_metric(line, r'took\s+([0-9.]+)ms')
                    if value is not None:
                        metrics['recursive_snark_verify_time_ms'] = value
                        metrics['recursive_snark_verify_time_s'] = value / 1000.0
                else:
                    metrics['recursive_snark_verify_time_s'] = value
                    metrics['recursive_snark_verify_time_ms'] = value * 1000.0
            
            # CompressedSNARK prove time: "CompressedSNARK::prove: true, took 53.14977675s"
            elif 'CompressedSNARK::prove' in line and 'took' in line:
                value = extract_metric(line, r'took\s+([0-9.]+)s')
                if value is not None:
                    metrics['compressed_snark_prove_time_s'] = value
            
            # CompressedSNARK verify time: "CompressedSNARK::verify: true, took 2.106095646s"
            elif 'CompressedSNARK::verify' in line and 'took' in line:
                # Try seconds first
                value = extract_metric(line, r'took\s+([0-9.]+)s')
                if value is None:
                    # Sometimes it's in milliseconds
                    value = extract_metric(line, r'took\s+([0-9.]+)ms')
                    if value is not None:
                        metrics['compressed_snark_verify_time_ms'] = value
                        metrics['compressed_snark_verify_time_s'] = value / 1000.0
                else:
                    metrics['compressed_snark_verify_time_s'] = value
                    metrics['compressed_snark_verify_time_ms'] = value * 1000.0
            
            # Primary circuit constraints: "Number of constraints per step (primary circuit): 559724"
            elif 'Number of constraints per step (primary circuit):' in line:
                value = extract_metric(line, r'Number of constraints per step \(primary circuit\):\s*([0-9]+)')
                if value is not None:
                    metrics['constraints_primary'] = int(value)
            
            # Primary circuit variables: "Number of variables per step (primary circuit): 544360"
            elif 'Number of variables per step (primary circuit):' in line:
                value = extract_metric(line, r'Number of variables per step \(primary circuit\):\s*([0-9]+)')
                if value is not None:
                    metrics['variables_primary'] = int(value)
            
            # Secondary circuit constraints: "Number of constraints per step (secondary circuit): 10347"
            elif 'Number of constraints per step (secondary circuit):' in line:
                value = extract_metric(line, r'Number of constraints per step \(secondary circuit\):\s*([0-9]+)')
                if value is not None:
                    metrics['constraints_secondary'] = int(value)
            
            # Secondary circuit variables: "Number of variables per step (secondary circuit): 10329"
            elif 'Number of variables per step (secondary circuit):' in line:
                value = extract_metric(line, r'Number of variables per step \(secondary circuit\):\s*([0-9]+)')
                if value is not None:
                    metrics['variables_secondary'] = int(value)
            
            # Peak memory: "Maximum resident set size (kbytes): 2650280"
            elif 'Maximum resident set size (kbytes):' in line:
                value = extract_metric(line, r'Maximum resident set size \(kbytes\):\s*([0-9]+)')
                if value is not None:
                    metrics['peak_memory_kb'] = int(value)
                    metrics['peak_memory_mb'] = round(value / 1024.0, 2)
                    metrics['peak_memory_gb'] = round(value / (1024.0 * 1024.0), 3)
    
    except Exception as e:
        print(f"Warning: Error reading {log_file}: {e}", file=sys.stderr)
        # Return empty metrics but still include the row
    
    return metrics


def find_log_files(directory: Path) -> list:
    """Find all passport_xxxx_output.log files in the directory."""
    log_files = sorted(directory.glob('passport_*_output.log'))
    return log_files


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_vimz_metrics.py <proofs_directory> [output_csv]")
        print("\nExample:")
        print("  python3 extract_vimz_metrics.py vimz/image_converter/blur/proofs_laptop_hd")
        print("  python3 extract_vimz_metrics.py vimz/image_converter/blur/proofs_laptop_hd results.csv")
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
        
        metrics = parse_vimz_log(log_file)
        metrics['file'] = log_file.name
        metrics['passport_id'] = passport_num
        
        # Always include the row, even if no metrics were extracted
        all_metrics.append(metrics)
        
        # Check if we got any metrics at all
        has_any_metrics = any(v is not None for k, v in metrics.items() if k not in ['file', 'passport_id'])
        if not has_any_metrics:
            failed_files.append(log_file.name)
    
    if failed_files:
        print(f"Warning: Could not extract any metrics from {len(failed_files)} files (rows included with empty values):", file=sys.stderr)
        for f in failed_files[:5]:  # Show first 5
            print(f"  - {f}", file=sys.stderr)
        if len(failed_files) > 5:
            print(f"  ... and {len(failed_files) - 5} more", file=sys.stderr)
    
    # Write to CSV
    fieldnames = [
        'passport_id',
        'file',
        'key_generation_time_s',
        'recursive_snark_creation_time_s',
        'recursive_snark_verify_time_s',
        'recursive_snark_verify_time_ms',
        'compressed_snark_prove_time_s',
        'compressed_snark_verify_time_s',
        'compressed_snark_verify_time_ms',
        'constraints_primary',
        'variables_primary',
        'constraints_secondary',
        'variables_secondary',
        'peak_memory_kb',
        'peak_memory_mb',
        'peak_memory_gb',
    ]
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for metrics in all_metrics:
            # Only include defined fieldnames, use empty string for None values
            row = {k: (metrics.get(k) if metrics.get(k) is not None else '') for k in fieldnames}
            writer.writerow(row)
    
    print(f"\n✓ Processed {len(all_metrics)} files (all rows included)")
    print(f"✓ CSV written to: {output_file}")
    
    # Print summary statistics (only for files with metrics)
    print("\nSummary Statistics (files with extracted metrics):")
    print("-" * 70)
    
    numeric_fields = [
        'key_generation_time_s',
        'recursive_snark_creation_time_s',
        'recursive_snark_verify_time_ms',
        'compressed_snark_prove_time_s',
        'compressed_snark_verify_time_ms',
        'constraints_primary',
        'variables_primary',
        'constraints_secondary',
        'variables_secondary',
        'peak_memory_mb',
    ]
    
    for field in numeric_fields:
        values = [m[field] for m in all_metrics if m.get(field) is not None]
        if values:
            mean_val = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            print(f"{field:35s}: mean={mean_val:12.3f}, min={min_val:12.3f}, max={max_val:12.3f} ({len(values)} values)")


if __name__ == '__main__':
    main()

