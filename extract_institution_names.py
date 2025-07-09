#!/usr/bin/env python3
"""
Script to extract institution names from DICOM files.
This script walks through all directories, finds .dcm files, and extracts the institution name from each.
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import pydicom
except ImportError:
    print("Error: pydicom library is required. Install it with: pip install pydicom")
    sys.exit(1)


def extract_institution_name(dcm_file_path):
    """
    Extract institution name from a DICOM file.

    Args:
        dcm_file_path (str): Path to the DICOM file

    Returns:
        tuple: (institution_name, study_instance_uid, error_message)
    """
    try:
        # Read the DICOM file
        ds = pydicom.dcmread(dcm_file_path, force=True)
        # Try to get institution name (tag 0008,0080)
        institution_name = None
        study_instance_uid = None
        if hasattr(ds, 'InstitutionName') and ds.InstitutionName:
            institution_name = str(ds.InstitutionName).strip()
        elif (0x0008, 0x0080) in ds:
            institution_name = str(ds[0x0008, 0x0080].value).strip()
        if hasattr(ds, 'StudyInstanceUID') and ds.StudyInstanceUID:
            study_instance_uid = str(ds.StudyInstanceUID).strip()
        # (0020, 000D)
        elif (0x0020, 0x000D) in ds:
            study_instance_uid = str(ds[0x0020, 0x000D].value).strip()

        return institution_name, study_instance_uid, None

    except Exception as e:
        return None, None, str(e)


def find_dcm_files(root_directory):
    """
    Find all .dcm files in the directory tree.

    Args:
        root_directory (str): Root directory to search

    Yields:
        str: Path to each DICOM file found
    """
    root_path = Path(root_directory)

    for dcm_file in root_path.rglob("*.dcm"):
        yield str(dcm_file)


def main():
    """Main function to process all DICOM files and extract institution names."""

    print("Please choose mode: ")
    print("1. Use a single file")
    print("2. Use a directory")

    while True:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")

    if choice == '1':
        # Single file mode
        while True:
            file_path = input("Enter the path to the DICOM file: ").strip()
            if os.path.exists(file_path):
                if file_path.lower().endswith('.dcm'):
                    break
                else:
                    print("Error: File must have .dcm extension")
            else:
                print("Error: File not found. Please enter a valid file path.")

        print("Starting DICOM institution name extraction...")
        print(f"Processing single file: {os.path.abspath(file_path)}")
        print("-" * 60)

        # Process single file
        results = []
        processed_count = 1

        print(f"Processing: {file_path}")
        institution_name, study_instance_uid, error = extract_institution_name(
            file_path)

        if error:
            print(f"  ERROR: {error}")
            results.append({
                'id': study_instance_uid,
                'institution_name': 'ERROR',
                'error': error
            })
            error_count = 1
        else:
            institution_display = institution_name if institution_name else 'NOT FOUND'
            print(f"  Institution: {institution_display}")
            results.append({
                'id': study_instance_uid,
                'institution_name': institution_name if institution_name else '',
                'error': ''
            })
            error_count = 0

    else:
        # Directory mode
        while True:
            root_dir = input(
                "Enter the directory path (or press Enter for current directory): ").strip()
            if not root_dir:
                root_dir = "."

            if os.path.exists(root_dir) and os.path.isdir(root_dir):
                break
            else:
                print("Error: Directory not found. Please enter a valid directory path.")

        print("Starting DICOM institution name extraction...")
        print(f"Searching for .dcm files in: {os.path.abspath(root_dir)}")
        print("-" * 60)

        # Results storage
        results = []
        error_count = 0
        processed_count = 0

        # Find and process all DICOM files
        for dcm_file_path in find_dcm_files(root_dir):
            processed_count += 1
            print(f"Processing ({processed_count}): {dcm_file_path}")

            institution_name, study_instance_uid, error = extract_institution_name(
                dcm_file_path,
            )

            if error:
                print(f"  ERROR: {error}")
                error_count += 1
                results.append({
                    'id': study_instance_uid,
                    'institution_name': 'ERROR',
                    'error': error
                })
            else:
                institution_display = institution_name if institution_name else 'NOT FOUND'
                print(f"  Institution: {institution_display}")
                results.append({
                    'id': study_instance_uid,
                    'institution_name': institution_name if institution_name else '',
                    'error': ''
                })

    print("-" * 60)
    print(f"Processing complete!")
    print(f"Total files processed: {processed_count}")
    print(f"Files with errors: {error_count}")
    print(
        f"Files with institution names: {len([r for r in results if r['institution_name'] and r['institution_name'] != 'ERROR'])}")

    # Save results to CSV
    output_file = f"institution_names_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'institution_name', 'error']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in results:
                writer.writerow(result)

        print(f"\nResults saved to: {output_file}")

    except Exception as e:
        print(f"Error saving CSV file: {e}")

    # Display summary of unique institutions
    unique_institutions = set()
    for result in results:
        if result['institution_name'] and result['institution_name'] != 'ERROR':
            unique_institutions.add(result['institution_name'])

    if unique_institutions:
        print(f"\nUnique institutions found ({len(unique_institutions)}):")
        for institution in sorted(unique_institutions):
            count = len(
                [r for r in results if r['institution_name'] == institution])
            print(f"  - {institution} ({count} files)")
    else:
        print("\nNo institution names found in any DICOM files.")


if __name__ == "__main__":
    main()
