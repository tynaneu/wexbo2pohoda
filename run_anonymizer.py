#!/usr/bin/env python3
"""Script to run the XML anonymizer on invoice files."""

import sys
import os
from pathlib import Path
from src.wexbo2pohoda.anonymizer import XMLAnonymizer


def main():
    """Run anonymizer on specified input file and save to data folder."""
    input_file = "/home/kristyna/Downloads/db_invoice_2026_03_28_10_37.xml"
    output_dir = "/home/kristyna/Documents/wexbo2pohoda/data"
    
    # Verify input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    output_filename = "anonymized_invoice_2026_03_28.xml"
    output_file = os.path.join(output_dir, output_filename)
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print()
    
    try:
        # Run anonymizer with seed for reproducibility
        anonymizer = XMLAnonymizer(seed=42)
        result = anonymizer.anonymize_file(input_file, output_file)
        
        print(f"✓ Successfully anonymized file")
        print(f"✓ Output saved to: {result}")
        print()
        
        # Print summary statistics
        import xml.etree.ElementTree as ET
        tree = ET.parse(result)
        root = tree.getroot()
        items = root.findall('item')
        print(f"Summary:")
        print(f"  Total items processed: {len(items)}")
        
    except Exception as e:
        print(f"Error: Failed to anonymize file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
