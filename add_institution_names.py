#!/usr/bin/env python3
"""
Script to add or modify institution names in DICOM files.
This script can process single files or entire directories and update the InstitutionName tag.
"""

import os
import random
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import pydicom
    from pydicom.uid import generate_uid
except ImportError:
    print("Error: pydicom library is required. Install it with: pip install pydicom")
    sys.exit(1)


def backup_file(file_path):
    """
    Create a backup of the original file.

    Args:
        file_path (str): Path to the file to backup

    Returns:
        str: Path to the backup file
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path


def generate_patient_id():
    """
    Generate a random patient ID.

    Returns:
        str: Random patient ID
    """
    return f"PAT{random.randint(100000, 999999)}"


def generate_accession_number():
    """
    Generate a random accession number.

    Returns:
        str: Random accession number
    """
    return f"ACC{random.randint(100000, 999999)}"


def add_institution_name(dcm_file_path, institution_name, create_backup=True, patient_mapping=None, study_mapping=None, base_output_dir=None):
    """
    Add or modify institution name in a DICOM file.

    Args:
        dcm_file_path (str): Path to the DICOM file
        institution_name (str): Institution name to set
        create_backup (bool): Whether to create a backup before modifying
        patient_mapping (dict): Dictionary to map original PatientIDs to new ones
        study_mapping (dict): Dictionary to map original StudyInstanceUIDs to new ones
        base_output_dir (str): Base directory for reorganized files

    Returns:
        tuple: (success, original_institution, error_message, backup_path, new_file_path)
    """
    if patient_mapping is None:
        patient_mapping = {}
    if study_mapping is None:
        study_mapping = {}
    try:
        # Read the DICOM file
        ds = pydicom.dcmread(dcm_file_path, force=True)

        # Get original institution name if it exists
        original_institution = None
        if hasattr(ds, 'InstitutionName') and ds.InstitutionName:
            original_institution = str(ds.InstitutionName).strip()
        elif (0x0008, 0x0080) in ds:
            original_institution = str(ds[0x0008, 0x0080].value).strip()

        # Create backup if requested
        backup_path = None
        if create_backup:
            backup_path = backup_file(dcm_file_path)

            # Generate proper DICOM UIDs (numeric only, dot-separated)
        # Map original PatientID to new consistent PatientID
        original_patient_id = str(ds.PatientID) if hasattr(
            ds, 'PatientID') and ds.PatientID else 'UNKNOWN_PATIENT'
        if original_patient_id not in patient_mapping:
            patient_mapping[original_patient_id] = generate_patient_id()
            # Generate patient name for new patient
            patient_suffix = random.randint(1000, 9999)
            patient_mapping[f"{original_patient_id}_name"] = f"Testing Patient {patient_suffix}"

        ds.PatientID = patient_mapping[original_patient_id]
        ds.PatientName = patient_mapping[f"{original_patient_id}_name"]

        # Map original StudyInstanceUID to new consistent StudyInstanceUID
        original_study_uid = str(ds.StudyInstanceUID) if hasattr(
            ds, 'StudyInstanceUID') and ds.StudyInstanceUID else 'UNKNOWN_STUDY'
        if original_study_uid not in study_mapping:
            study_mapping[original_study_uid] = generate_uid()

        # Set the date and time to current date and time
        ds.StudyDate = datetime.now().strftime('%Y%m%d')
        ds.StudyTime = datetime.now().strftime('%H%M%S')

        ds.StudyInstanceUID = study_mapping[original_study_uid]

        ds.SeriesInstanceUID = generate_uid()
        ds.SOPInstanceUID = generate_uid()
        ds.AccessionNumber = generate_accession_number()

        # Set the new institution name
        ds.InstitutionName = institution_name

        # Preserve original transfer syntax and encoding
        original_transfer_syntax = ds.file_meta.TransferSyntaxUID if hasattr(
            ds, 'file_meta') and hasattr(ds.file_meta, 'TransferSyntaxUID') else None

        # Determine new file path if base_output_dir is provided
        new_file_path = dcm_file_path
        if base_output_dir:
            # Create new directory structure based on new StudyInstanceUID
            new_study_dir = os.path.join(base_output_dir, ds.StudyInstanceUID)
            os.makedirs(new_study_dir, exist_ok=True)

            # Generate new filename based on new IDs
            original_filename = os.path.basename(dcm_file_path)
            if original_filename.lower().endswith('.dcm'):
                # Create filename with patient and series info
                new_filename = f"{ds.PatientID}_{ds.SeriesInstanceUID}_{ds.SOPInstanceUID}.dcm"
            else:
                new_filename = original_filename

            new_file_path = os.path.join(new_study_dir, new_filename)

        # Save the modified file while preserving structure
        if original_transfer_syntax:
            ds.save_as(new_file_path, write_like_original=True)
        else:
            # Fallback if no transfer syntax found
            ds.save_as(new_file_path, write_like_original=False)

        return True, original_institution, None, backup_path, new_file_path

    except Exception as e:
        return False, None, str(e), None, None


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
    """Main function to add institution names to DICOM files."""

    print("DICOM Institution Name Modifier")
    print("=" * 40)
    print("This script will ADD or MODIFY institution names in DICOM files.")
    print("WARNING: This will permanently modify your DICOM files!")
    print("=" * 40)

    # Get institution name to set
    institution_name = input("Enter the institution name to set: ").strip()

    print(f"\nInstitution name to set: '{institution_name}'")

    # Choose processing mode
    print("\nPlease choose mode:")
    print("1. Process a single file")
    print("2. Process all files in a directory")

    while True:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")

    # Choose backup option
    print("\nBackup options:")
    print("1. Create backups of original files (recommended)")
    print("2. No backups (modify files directly)")

    while True:
        backup_choice = input("Enter your choice (1 or 2): ").strip()
        if backup_choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")

    create_backup = backup_choice == '1'

    # Choose file organization option
    print("\nFile organization options:")
    print("1. Modify files in place (keep original structure)")
    print("2. Create new organized structure (recommended)")

    while True:
        org_choice = input("Enter your choice (1 or 2): ").strip()
        if org_choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")

    reorganize_files = org_choice == '2'
    base_output_dir = None

    if reorganize_files:
        while True:
            output_dir = input(
                "Enter output directory for reorganized files (or press Enter for 'reorganized'): ").strip()
            if not output_dir:
                output_dir = "reorganized"

            # Create the output directory if it doesn't exist
            try:
                os.makedirs(output_dir, exist_ok=True)
                base_output_dir = output_dir
                break
            except Exception as e:
                print(f"Error creating directory '{output_dir}': {e}")

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

        files_to_process = [file_path]

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

        print(f"\nSearching for .dcm files in: {os.path.abspath(root_dir)}")
        files_to_process = list(find_dcm_files(root_dir))

        if not files_to_process:
            print("No DICOM files found in the specified directory.")
            return

        print(f"Found {len(files_to_process)} DICOM files.")

    # Final confirmation
    print(f"\n" + "=" * 60)
    print(f"READY TO PROCESS:")
    print(f"- Files to modify: {len(files_to_process)}")
    print(f"- Institution name: '{institution_name}'")
    print(f"- Create backups: {'Yes' if create_backup else 'No'}")
    print(f"- Reorganize files: {'Yes' if reorganize_files else 'No'}")
    if reorganize_files:
        print(f"- Output directory: {base_output_dir}")
    print(f"=" * 60)

    confirm = input(
        "Are you sure you want to proceed? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Operation cancelled.")
        return

    # Process files
    print(f"\nStarting processing...")
    print("-" * 60)

    results = []
    success_count = 0
    error_count = 0

    # Create mapping dictionaries to ensure consistency across files
    patient_mapping = {}  # Maps original PatientID -> new PatientID
    study_mapping = {}    # Maps original StudyInstanceUID -> new StudyInstanceUID

    for i, dcm_file_path in enumerate(files_to_process, 1):
        print(f"Processing ({i}/{len(files_to_process)}): {dcm_file_path}")

        success, original_institution, error, backup_path, new_file_path = add_institution_name(
            dcm_file_path, institution_name, create_backup, patient_mapping, study_mapping, base_output_dir
        )

        if success:
            success_count += 1
            original_display = original_institution if original_institution else "NOT SET"
            print(f"  ✓ SUCCESS: '{original_display}' → '{institution_name}'")
            if backup_path:
                print(f"    Backup: {backup_path}")
            if new_file_path != dcm_file_path:
                print(f"    New location: {new_file_path}")

            results.append({
                'original_file_path': dcm_file_path,
                'new_file_path': new_file_path,
                'status': 'SUCCESS',
                'original_institution': original_institution or '',
                'new_institution': institution_name,
                'backup_path': backup_path or '',
                'error': ''
            })
        else:
            error_count += 1
            print(f"  ✗ ERROR: {error}")

            results.append({
                'original_file_path': dcm_file_path,
                'new_file_path': '',
                'status': 'ERROR',
                'original_institution': '',
                'new_institution': '',
                'backup_path': '',
                'error': error
            })

    print("-" * 60)
    print(f"Processing complete!")
    print(f"Successfully modified: {success_count} files")
    print(f"Errors: {error_count} files")

    # Count unique patients and studies that were mapped
    unique_patients = len(
        [k for k in patient_mapping.keys() if not k.endswith('_name')])
    unique_studies = len(study_mapping)
    print(f"Unique patients processed: {unique_patients}")
    print(f"Unique studies processed: {unique_studies}")

    # Save results log
    log_file = f"institution_modification_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    try:
        import csv
        with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['original_file_path', 'new_file_path', 'status', 'original_institution',
                          'new_institution', 'backup_path', 'error']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in results:
                writer.writerow(result)

        print(f"\nModification log saved to: {log_file}")

    except Exception as e:
        print(f"Error saving log file: {e}")

    if create_backup and success_count > 0:
        print(f"\n📁 Backup files created for successful modifications.")
        print(f"   To restore originals, rename .backup_* files back to .dcm")

    if reorganize_files and success_count > 0:
        print(f"\n📂 Files have been reorganized in: {base_output_dir}")
        print(
            f"   Directory structure: {base_output_dir}/[StudyInstanceUID]/[PatientID]_[SeriesUID]_[SOPUID].dcm")

    print(
        f"\n✅ Institution name '{institution_name}' has been set in {success_count} files.")


if __name__ == "__main__":
    main()
