#!/usr/bin/env python3
"""
Script to create a completely new DICOM study with new IDs while preserving structure.
This script updates Institution Name, Patient Name, and generates new IDs for Study, Series, and Instances,
while maintaining proper hierarchical relationships and descriptions.
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    import pydicom
    from pydicom.uid import generate_uid
except ImportError:
    print("Error: pydicom library is required. Install it with: pip install pydicom")
    sys.exit(1)





def generate_patient_id():
    """
    Generate a unique patient ID based on timestamp and counter.

    Returns:
        str: Unique patient ID
    """
    import random
    return f"PAT{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"


def create_new_study(dcm_file_path, institution_name, patient_name, 
                     mappings=None, base_output_dir=None):
    """
    Create a new study from DICOM file with new IDs while preserving structure.

    Args:
        dcm_file_path (str): Path to the DICOM file
        institution_name (str): New institution name to set
        patient_name (str): New patient name to set
        mappings (dict): Dictionary containing ID mappings to maintain consistency
        base_output_dir (str): Base directory for reorganized files

    Returns:
        tuple: (success, error_message, new_file_path, mappings)
    """
    if mappings is None:
        mappings = {
            'patient_id': None,
            'study_uid': None,
            'series_map': {},      # original_series_uid -> (new_series_uid, series_description)
            'instance_map': {}     # original_instance_uid -> new_instance_uid
        }

    try:
        # Read the DICOM file
        ds = pydicom.dcmread(dcm_file_path, force=True)

        # Create backup if requested
        # (Backup functionality removed)


        # ===== PATIENT ID MAPPING =====
        # Generate new PatientID once for all files
        if mappings['patient_id'] is None:
            mappings['patient_id'] = generate_patient_id()
        
        ds.PatientID = mappings['patient_id']
        ds.PatientName = patient_name

        # ===== STUDY UID MAPPING =====
        # Generate new StudyInstanceUID once for all files
        original_study_uid = str(ds.StudyInstanceUID) if hasattr(
            ds, 'StudyInstanceUID') and ds.StudyInstanceUID else None
        
        if mappings['study_uid'] is None:
            mappings['study_uid'] = generate_uid()
        
        ds.StudyInstanceUID = mappings['study_uid']

        # ===== SERIES UID MAPPING =====
        # Map original SeriesInstanceUID to new one (consistent across files in same series)
        original_series_uid = str(ds.SeriesInstanceUID) if hasattr(
            ds, 'SeriesInstanceUID') and ds.SeriesInstanceUID else None
        
        if original_series_uid and original_series_uid not in mappings['series_map']:
            # Generate generic series description and protocol name
            series_count = len(mappings['series_map']) + 1
            series_description = f"Series {series_count}"
            protocol_name = f"Protocol {series_count}"
            series_number = ds.SeriesNumber if hasattr(ds, 'SeriesNumber') else None
            
            # Create new series UID
            new_series_uid = generate_uid()
            mappings['series_map'][original_series_uid] = {
                'new_uid': new_series_uid,
                'description': series_description,
                'protocol_name': protocol_name,
                'number': series_number
            }
        
        if original_series_uid and original_series_uid in mappings['series_map']:
            series_info = mappings['series_map'][original_series_uid]
            ds.SeriesInstanceUID = series_info['new_uid']
            
            # Set anonymized series description
            ds.SeriesDescription = series_info['description']
            
            # Set anonymized protocol name
            ds.ProtocolName = series_info['protocol_name']

        # ===== INSTANCE UID MAPPING =====
        # Map original SOPInstanceUID to new one (unique for each instance)
        original_instance_uid = str(ds.SOPInstanceUID) if hasattr(
            ds, 'SOPInstanceUID') and ds.SOPInstanceUID else None
        
        if original_instance_uid and original_instance_uid not in mappings['instance_map']:
            mappings['instance_map'][original_instance_uid] = generate_uid()
        
        if original_instance_uid and original_instance_uid in mappings['instance_map']:
            ds.SOPInstanceUID = mappings['instance_map'][original_instance_uid]

        # ===== UPDATE OTHER IDENTIFIERS =====
        # Set institution name
        ds.InstitutionName = institution_name

        # Update study ID if present
        if hasattr(ds, 'StudyID'):
            ds.StudyID = f"STU{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Update accession number if present
        if hasattr(ds, 'AccessionNumber'):
            import random
            ds.AccessionNumber = f"ACC{random.randint(100000, 999999)}"

        # Update dates to current date
        current_date = datetime.now().strftime('%Y%m%d')
        current_time = datetime.now().strftime('%H%M%S')
        
        if hasattr(ds, 'StudyDate'):
            ds.StudyDate = current_date
        if hasattr(ds, 'StudyTime'):
            ds.StudyTime = current_time
        if hasattr(ds, 'SeriesDate'):
            ds.SeriesDate = current_date
        if hasattr(ds, 'SeriesTime'):
            ds.SeriesTime = current_time

        # Preserve original transfer syntax and encoding
        original_transfer_syntax = ds.file_meta.TransferSyntaxUID if hasattr(
            ds, 'file_meta') and hasattr(ds.file_meta, 'TransferSyntaxUID') else None

        # Determine new file path
        new_file_path = dcm_file_path
        if base_output_dir:
            # Create new directory structure: output_dir/StudyUID/SeriesUID/
            series_uid = ds.SeriesInstanceUID if hasattr(ds, 'SeriesInstanceUID') else "UNKNOWN_SERIES"
            new_series_dir = os.path.join(base_output_dir, ds.StudyInstanceUID, series_uid)
            os.makedirs(new_series_dir, exist_ok=True)

            # Generate new filename
            original_filename = os.path.basename(dcm_file_path)
            instance_number = ds.InstanceNumber if hasattr(ds, 'InstanceNumber') else "0"
            
            if original_filename.lower().endswith('.dcm'):
                new_filename = f"IMG{str(instance_number).zfill(5)}.dcm"
            else:
                new_filename = original_filename

            new_file_path = os.path.join(new_series_dir, new_filename)

        # Save the modified file while preserving structure
        if original_transfer_syntax:
            ds.save_as(new_file_path, write_like_original=True)
        else:
            ds.save_as(new_file_path, write_like_original=False)

        return True, None, new_file_path, mappings

    except Exception as e:
        return False, str(e), None, mappings


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
    """Main function to create a new DICOM study."""

    print("=" * 70)
    print("DICOM Study Creator - Create New Study with Preserved Structure")
    print("=" * 70)
    print("This script will create a completely new study with:")
    print("  • New Institution Name")
    print("  • New Patient Name and ID")
    print("  • New Study, Series, and Instance UIDs")
    print("  • Preserved series and instance relationships")
    print("  • Preserved series descriptions and metadata")
    print("=" * 70)

    # Get institution name
    institution_input = input("\nEnter the new institution name (press Enter to auto-generate): ").strip()
    if institution_input:
        institution_name = institution_input
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        institution_name = f"AutoInst_{timestamp}"

    # Get patient name
    patient_input = input("Enter the new patient name (press Enter to auto-generate): ").strip()
    if patient_input:
        patient_name = patient_input
    else:
        import random
        patient_name = f"AutoPatient_{datetime.now().strftime('%Y%m%d')}_{random.randint(1000, 9999)}"

    print(f"\n✓ Institution Name: '{institution_name}'")
    print(f"✓ Patient Name: '{patient_name}'")

    # Choose processing mode
    print("\nPlease choose processing mode:")
    print("1. Process a single file")
    print("2. Process all files in a directory (recommended for complete studies)")

    while True:
        choice = input("Enter your choice (1 or 2) [default: 2]: ").strip()
        if not choice:
            choice = '2'
            print("Using default: 2")
        if choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")

    # Choose output directory
    print("\nOutput options:")
    print("1. Create new organized directory structure (recommended)")
    print("2. Modify files in place")

    while True:
        org_choice = input("Enter your choice (1 or 2) [default: 1]: ").strip()
        if not org_choice:
            org_choice = '1'
            print("Using default: 1")
        if org_choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")

    reorganize_files = org_choice == '1'
    base_output_dir = None

    if reorganize_files:
        while True:
            output_dir = input(
                "Enter output directory (or press Enter for 'new_study'): ").strip().strip('\'"')
            if not output_dir:
                output_dir = "new_study"

            # Create the output directory if it doesn't exist
            try:
                os.makedirs(output_dir, exist_ok=True)
                base_output_dir = output_dir
                break
            except Exception as e:
                print(f"Error creating directory '{output_dir}': {e}")

    # Get input files
    if choice == '1':
        # Single file mode
        while True:
            file_path = input("\nEnter the path to the DICOM file: ").strip().strip('\'"')
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
                "\nEnter the directory path (or press Enter for current directory): ").strip().strip('\'"')
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
    print(f"\n" + "=" * 70)
    print(f"READY TO PROCESS:")
    print(f"  • Files to process: {len(files_to_process)}")
    print(f"  • Institution name: '{institution_name}'")
    print(f"  • Patient name: '{patient_name}'")
    print(f"  • Create organized structure: {'Yes' if reorganize_files else 'No'}")
    if reorganize_files:
        print(f"  • Output directory: {base_output_dir}")
    print(f"=" * 70)

    confirm = input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Operation cancelled.")
        return

    # Process files
    print(f"\nStarting processing...")
    print("-" * 70)

    results = []
    success_count = 0
    error_count = 0

    # Create mapping dictionary to ensure consistency across files
    mappings = {
        'patient_id': None,
        'study_uid': None,
        'series_map': {},
        'instance_map': {}
    }

    for i, dcm_file_path in enumerate(files_to_process, 1):
        print(f"\nProcessing ({i}/{len(files_to_process)}): {dcm_file_path}")

        success, error, new_file_path, mappings = create_new_study(
            dcm_file_path, institution_name, patient_name, 
            mappings, base_output_dir
        )

        if success:
            success_count += 1
            print(f"  ✓ SUCCESS")
            results.append({
                'original_file_path': dcm_file_path,
                'new_file_path': new_file_path,
                'status': 'SUCCESS',
                'error': ''
            })
        else:
            error_count += 1
            print(f"  ✗ ERROR: {error}")

            results.append({
                'original_file_path': dcm_file_path,
                'new_file_path': '',
                'status': 'ERROR',
                'error': error
            })

    print("\n" + "=" * 70)
    print(f"PROCESSING COMPLETE!")
    print("=" * 70)
    print(f"Successfully processed: {success_count} files")
    print(f"Errors: {error_count} files")
    print(f"\nNew Study Details:")
    print(f"  • Patient ID: {mappings['patient_id']}")
    print(f"  • Patient Name: {patient_name}")
    print(f"  • Study UID: {mappings['study_uid']}")
    print(f"  • Number of Series: {len(mappings['series_map'])}")
    print(f"  • Number of Instances: {len(mappings['instance_map'])}")

    # Display series information
    if mappings['series_map']:
        print(f"\n  Series Information:")
        for idx, (orig_uid, series_info) in enumerate(mappings['series_map'].items(), 1):
            desc = series_info['description'] if series_info['description'] else "No description"
            print(f"    {idx}. {desc}")
            print(f"       New UID: {series_info['new_uid']}")

    # Save results log
    log_file = f"new_study_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    try:
        import csv
        with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['original_file_path', 'new_file_path', 'status', 'error']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in results:
                writer.writerow(result)

        print(f"\n📄 Processing log saved to: {log_file}")

    except Exception as e:
        print(f"Error saving log file: {e}")

    # Save mapping information
    mapping_file = f"uid_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(mapping_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("DICOM UID Mapping Information\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Patient Information:\n")
            f.write(f"  New Patient ID: {mappings['patient_id']}\n")
            f.write(f"  New Patient Name: {patient_name}\n\n")
            f.write(f"Study Information:\n")
            f.write(f"  New Study UID: {mappings['study_uid']}\n\n")
            f.write(f"Series Mappings ({len(mappings['series_map'])} series):\n")
            f.write("-" * 70 + "\n")
            for orig_uid, series_info in mappings['series_map'].items():
                f.write(f"  Original Series UID: {orig_uid}\n")
                f.write(f"  New Series UID: {series_info['new_uid']}\n")
                f.write(f"  Description: {series_info['description']}\n")
                if series_info['number'] is not None:
                    f.write(f"  Series Number: {series_info['number']}\n")
                f.write("\n")
            
            f.write(f"\nInstance Mappings ({len(mappings['instance_map'])} instances):\n")
            f.write("-" * 70 + "\n")
            for orig_uid, new_uid in mappings['instance_map'].items():
                f.write(f"  Original: {orig_uid}\n")
                f.write(f"  New:      {new_uid}\n\n")

        print(f"📄 UID mapping saved to: {mapping_file}")

    except Exception as e:
        print(f"Error saving mapping file: {e}")



    if reorganize_files and success_count > 0:
        print(f"\n📂 Files have been reorganized in: {base_output_dir}")
        print(f"   Directory structure: {base_output_dir}/[StudyUID]/[SeriesUID]/IMG#####.dcm")

    print(f"\n✅ Successfully created new study with {success_count} files!")
    print(f"   Institution: '{institution_name}'")
    print(f"   Patient: '{patient_name}'")


if __name__ == "__main__":
    main()


