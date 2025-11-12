import os
import pathlib
import zipfile
import requests
from typing import List

# Define the web URLs that contain the files to be downloaded

BG_BASE_URL = “https://www2.census.gov/geo/tiger/TIGER2025/BG/”
TRACT_BASE_URL = “https://www2.census.gov/geo/tiger/TIGER2025/TRACT/”

# Define the local directory where files will be downloaded to

project_root = pathlib.Path.cwd()
download_dir = project_root / “Census_BlockGroup_ZipFiles”
download_dir.mkdir(exist_ok=True)

# Define the list of block group file names to download

bg_file_names = [
“tl_2025_01_bg.zip”,
“tl_2025_02_bg.zip”,
“tl_2025_04_bg.zip”,
“tl_2025_05_bg.zip”,
“tl_2025_06_bg.zip”,
“tl_2025_08_bg.zip”,
“tl_2025_09_bg.zip”,
“tl_2025_10_bg.zip”,
“tl_2025_11_bg.zip”,
“tl_2025_12_bg.zip”,
“tl_2025_13_bg.zip”,
“tl_2025_15_bg.zip”,
“tl_2025_16_bg.zip”,
“tl_2025_17_bg.zip”,
“tl_2025_18_bg.zip”,
“tl_2025_19_bg.zip”,
“tl_2025_20_bg.zip”,
“tl_2025_21_bg.zip”,
“tl_2025_22_bg.zip”,
“tl_2025_23_bg.zip”,
“tl_2025_24_bg.zip”,
“tl_2025_25_bg.zip”,
“tl_2025_26_bg.zip”,
“tl_2025_27_bg.zip”,
“tl_2025_28_bg.zip”,
“tl_2025_29_bg.zip”,
“tl_2025_30_bg.zip”,
“tl_2025_31_bg.zip”,
“tl_2025_32_bg.zip”,
“tl_2025_33_bg.zip”,
“tl_2025_34_bg.zip”,
“tl_2025_35_bg.zip”,
“tl_2025_36_bg.zip”,
“tl_2025_37_bg.zip”,
“tl_2025_38_bg.zip”,
“tl_2025_39_bg.zip”,
“tl_2025_40_bg.zip”,
“tl_2025_41_bg.zip”,
“tl_2025_42_bg.zip”,
“tl_2025_44_bg.zip”,
“tl_2025_45_bg.zip”,
“tl_2025_46_bg.zip”,
“tl_2025_47_bg.zip”,
“tl_2025_48_bg.zip”,
“tl_2025_49_bg.zip”,
“tl_2025_50_bg.zip”,
“tl_2025_51_bg.zip”,
“tl_2025_53_bg.zip”,
“tl_2025_54_bg.zip”,
“tl_2025_55_bg.zip”,
“tl_2025_56_bg.zip”,
“tl_2025_60_bg.zip”,
“tl_2025_66_bg.zip”,
“tl_2025_69_bg.zip”,
“tl_2025_72_bg.zip”,
“tl_2025_78_bg.zip”,
]

# Define the list of tract file names to download

tract_file_names = [
“tl_2025_01_tract.zip”,
“tl_2025_02_tract.zip”,
“tl_2025_04_tract.zip”,
“tl_2025_05_tract.zip”,
“tl_2025_06_tract.zip”,
“tl_2025_08_tract.zip”,
“tl_2025_09_tract.zip”,
“tl_2025_10_tract.zip”,
“tl_2025_11_tract.zip”,
“tl_2025_12_tract.zip”,
“tl_2025_13_tract.zip”,
“tl_2025_15_tract.zip”,
“tl_2025_16_tract.zip”,
“tl_2025_17_tract.zip”,
“tl_2025_18_tract.zip”,
“tl_2025_19_tract.zip”,
“tl_2025_20_tract.zip”,
“tl_2025_21_tract.zip”,
“tl_2025_22_tract.zip”,
“tl_2025_23_tract.zip”,
“tl_2025_24_tract.zip”,
“tl_2025_25_tract.zip”,
“tl_2025_26_tract.zip”,
“tl_2025_27_tract.zip”,
“tl_2025_28_tract.zip”,
“tl_2025_29_tract.zip”,
“tl_2025_30_tract.zip”,
“tl_2025_31_tract.zip”,
“tl_2025_32_tract.zip”,
“tl_2025_33_tract.zip”,
“tl_2025_34_tract.zip”,
“tl_2025_35_tract.zip”,
“tl_2025_36_tract.zip”,
“tl_2025_37_tract.zip”,
“tl_2025_38_tract.zip”,
“tl_2025_39_tract.zip”,
“tl_2025_40_tract.zip”,
“tl_2025_41_tract.zip”,
“tl_2025_42_tract.zip”,
“tl_2025_44_tract.zip”,
“tl_2025_45_tract.zip”,
“tl_2025_46_tract.zip”,
“tl_2025_47_tract.zip”,
“tl_2025_48_tract.zip”,
“tl_2025_49_tract.zip”,
“tl_2025_50_tract.zip”,
“tl_2025_51_tract.zip”,
“tl_2025_53_tract.zip”,
“tl_2025_54_tract.zip”,
“tl_2025_55_tract.zip”,
“tl_2025_56_tract.zip”,
“tl_2025_60_tract.zip”,
“tl_2025_66_tract.zip”,
“tl_2025_69_tract.zip”,
“tl_2025_72_tract.zip”,
“tl_2025_78_tract.zip”,
]

def download_file(url: str, destination: pathlib.Path) -> bool:
“”“Download a file from a URL to a destination path.

```
Args:
    url: The URL to download from
    destination: The local path to save the file
    
Returns:
    True if successful, False otherwise
"""
try:
    print(f"Downloading {url}...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()  # Raise an error for bad status codes
    
    with open(destination, "wb") as f:
        f.write(response.content)
    
    print(f"  ✓ Successfully downloaded to {destination}")
    return True
except requests.exceptions.RequestException as e:
    print(f"  ✗ Error downloading {url}: {e}")
    return False
```

def extract_zip(zip_path: pathlib.Path, extract_dir: pathlib.Path) -> bool:
“”“Extract a zip file to a directory.

```
Args:
    zip_path: Path to the zip file
    extract_dir: Directory to extract to
    
Returns:
    True if successful, False otherwise
"""
try:
    # Verify the file is actually a valid zip
    if not zipfile.is_zipfile(zip_path):
        print(f"  ✗ {zip_path} is not a valid zip file")
        return False
    
    print(f"Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Extract to a subdirectory named after the zip file (without extension)
        zip_name = zip_path.stem
        target_dir = extract_dir / zip_name
        zip_ref.extractall(target_dir)
    
    print(f"  ✓ Extracted to {target_dir}")
    return True
except zipfile.BadZipFile as e:
    print(f"  ✗ Bad zip file {zip_path}: {e}")
    return False
except Exception as e:
    print(f"  ✗ Error extracting {zip_path}: {e}")
    return False
```

def process_files(base_url: str, file_names: List[str], file_type: str):
“”“Download and extract a list of files.

```
Args:
    base_url: The base URL for downloading
    file_names: List of file names to download
    file_type: Type of files (for naming directories)
"""
# Create directories
zip_dir = project_root / f"Census_{file_type}_ZipFiles"
extract_dir = project_root / f"Census_{file_type}"

zip_dir.mkdir(exist_ok=True)
extract_dir.mkdir(exist_ok=True)

print(f"\n{'='*60}")
print(f"Processing {file_type} files")
print(f"{'='*60}\n")

successful_downloads = 0
failed_downloads = 0
successful_extractions = 0
failed_extractions = 0

# Download all files
for file_name in file_names:
    file_url = base_url + file_name
    zip_path = zip_dir / file_name
    
    if download_file(file_url, zip_path):
        successful_downloads += 1
    else:
        failed_downloads += 1

print(f"\nDownload Summary: {successful_downloads} successful, {failed_downloads} failed")

# Extract all successfully downloaded files
print(f"\n{'='*60}")
print(f"Extracting {file_type} files")
print(f"{'='*60}\n")

for zip_file in zip_dir.glob("*.zip"):
    if extract_zip(zip_file, extract_dir):
        successful_extractions += 1
    else:
        failed_extractions += 1

print(f"\nExtraction Summary: {successful_extractions} successful, {failed_extractions} failed")
print(f"{'='*60}\n")
```

def main():
“”“Main function to download and extract all Census files.”””
print(“Starting Census data download and extraction process…\n”)

```
# Process block group files
process_files(BG_BASE_URL, bg_file_names, "BlockGroup")

# Process tract files
process_files(TRACT_BASE_URL, tract_file_names, "Tract")

print("\n" + "="*60)
print("All processing complete!")
print("="*60)
```

if **name** == “**main**”:
main()