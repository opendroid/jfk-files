# download_jfk_files.py
#
# This script downloads the files from the JFK website.
# URL: https://www.archives.gov/research/jfk/release-2025
# The files are stored in the data/jfk directory.
#
# The plan:
# 1. Download the webpage from URL.
# 2. Parse the webpage for inks that end in .PDF
# 3. Download the files to the {target} directory.
#    - Replace %20 with '' in the filename.

import requests
from tqdm import tqdm
import os
from extract_filenames import extract_filenames


def download_files(links, destination_dir):
    """Download the files from the links to the destination directory.

    Args:
        links (list): List of links to download.
        destination_dir (str): Directory to save the files.

    Returns:
        list: List of links that failed to download.
    """
    failed_links = []
    existing_files = []
    # Show progress with tqdm
    pbar = tqdm(total=len(links), desc="Documents downloaded",
                colour="#00FFFF", unit=" pdf(s)")
    for link in links:
        filename = link.split('/')[-1].replace("%20", "")
        filepath = f"{destination_dir}/{filename}"
        if os.path.exists(f"{filepath}"):
            existing_files.append(link)
            pbar.update(1)
            continue
        response = requests.get(link)
        if response.status_code != 200:
            failed_links.append(link)
            pbar.update(1)
            continue

        with open(f"{filepath}", "wb") as file:
            file.write(response.content)
        pbar.update(1)
    pbar.close()

    # Print the number of failed links
    if len(failed_links) > 0:
        print(f"Failed to download: {len(failed_links)} links")
        # Save the failed links to a file
        with open("../data/jfk_failed_links.txt", "w") as file:
            for link in failed_links:
                file.write(link + "\n")

    if len(existing_files) > 0:
        print(f"Existing files: {len(existing_files)} files")

    downloaded_files = len(links) - len(failed_links) - len(existing_files)
    if downloaded_files > 0:
        print(f"Downloaded: {downloaded_files} files")

    return failed_links


if __name__ == "__main__":
    links1 = extract_filenames("./data/jfk_files_20250320.html")
    links2 = extract_filenames("./data/jfk_files_20250318.html")
    links = set(links1) - set(links2)
    print(f"Downloading {len(links)} files")
    download_files(links, "../../data/jfk/docs/pdf/20250320")
