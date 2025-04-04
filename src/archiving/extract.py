import os
import sys
import shutil
import subprocess

__parent_dir__ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(__parent_dir__)

from find_files_by_name import find_files_by_name as find_files
from file_extention_helper import append_file_extension as append_file_extension


def remove_7z_extension(file_path):
    """
    Removes the .7z or .7z.001 extension from a file path.

    Args:
        file_path (str): The file path.

    Returns:
        str: The file path without the .7z or .7z.001 extension, or the original path if no match.
    """
    if file_path.lower().endswith(".7z"):
        return file_path[:-3]  # Remove the last 3 characters (.7z)
    elif file_path.lower().endswith(".7z.001"):
        return file_path[:-7] # Remove the last 7 characters (.7z.001)
    else:
        return file_path  # Return the original path if no match
    

def extract_7z(archive_path, extract_path):
    """
    Extracts a 7z archive.
    """
    if not os.path.exists(archive_path):
        print(f"Error: 7z archive not found: {archive_path}")
        return False

    command = [
        "7z",
        "x",
        archive_path,
        f"-o{extract_path}",
        "-y",
        "-spe",
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Successfully extracted {archive_path} to {extract_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error extracting {archive_path}: {e}")
        return False
    except FileNotFoundError:
        print("Error: 7z command not found. Make sure it is installed and in your PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def verify_and_repair_par2(par2_file_path, repair=True):
    """
    Verifies and optionally repairs files using a PAR2 file.
    """
    if not os.path.exists(par2_file_path):
        print(f"Error: PAR2 file not found: {par2_file_path}")
        return False

    par2_dir = os.path.dirname(par2_file_path)
    try:
        verify_process = subprocess.run(
            ["par2j64", "v", par2_file_path],
            cwd=par2_dir,
            capture_output=True,
            text=True,
        )

        if "All Files Complete" in verify_process.stdout:
            print(f"Verification successful: All files are correct for {par2_file_path}")
            return True
        elif "Ready to repair" in verify_process.stdout:
            print(f"Verification failed: Some files are missing or damaged for {par2_file_path}")
            if repair:
                print(f"Attempting repair for {par2_file_path}...")
                repair_process = subprocess.run(
                    ["par2j64", "r", par2_file_path],
                    cwd=par2_dir,
                    capture_output=True,
                    text=True,
                )
                if "Repaired successfully" in repair_process.stdout:
                    print(f"Repair successful for {par2_file_path}.")
                    return True
                else:
                    print(f"Repair failed for {par2_file_path}.")
                    print(repair_process.stdout)
                    print(repair_process.stderr)
                    return False
            else:
                return False
        else:
            print(f"Unknown PAR2 output during verification for {par2_file_path}:")
            print(verify_process.stdout)
            print(verify_process.stderr)
            return False

    except FileNotFoundError:
        print("Error: par2j64 command not found. Make sure it is installed and in your PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def verify_and_extract_archives(folder_path):
    if not os.path.isabs(folder_path):
        folder_path = os.path.abspath(folder_path)

    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return
    
    _7z_files =  find_files(folder_path, ends_with = '.7z', search_subdir = True)
    _7z_volume_files = find_files(folder_path, ends_with = '.7z.001', search_subdir = True)
    archive_files = _7z_files | _7z_volume_files
    
    if not archive_files:
        return print(f"No archives found in directory: {folder_path}")

    for file_path in archive_files:
        file_path_name = remove_7z_extension(file_path)
        directory, _ = os.path.split(file_path)
        parent_folder_name = os.path.basename(directory)

        if verify_and_repair_par2(append_file_extension(file_path_name, '.7z.par2')):
            extract_7z(file_path, remove_7z_extension(file_path))
        elif verify_and_repair_par2(append_file_extension(file_path_name, '.7z.001.par2')):
            extract_7z(file_path, remove_7z_extension(file_path))
        
        try:
            items_in_dir = os.listdir(directory)
            if parent_folder_name in items_in_dir:
                children_dir_path = os.path.join(directory, parent_folder_name)
                for child in os.listdir(children_dir_path):
                    child_path = os.path.join(children_dir_path, child)
                    shutil.move(child_path, os.path.dirname(children_dir_path))
                os.rmdir(children_dir_path)
        except FileNotFoundError:
            print(f"Warning: Directory '{directory}' not found after extraction.")
        except Exception as e:
            print(f"An error occurred while moving folder: {e}")   


def main():
    folder_path = input("Enter the directory folder: ")  
    verify_and_extract_archives(folder_path)
    print("Done!")


if __name__ == "__main__":
    main()