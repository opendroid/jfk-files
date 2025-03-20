from bs4 import BeautifulSoup
import os
import glob


def extract_filenames(file_path):
    """Extract the last part of the path as filenames from the .file_path

    Args:
        file_path (str): Path to the file containing the failed links

    Returns:
        list: List of filenames
    """
    # Extract complete links from the ../data/webdata.html that end with .pdf
    with open(file_path, "r") as file:
        webpage = file.read()

    soup = BeautifulSoup(webpage, "html.parser")
    # Sample links:
    # https://www.archives.gov/files/research/jfk/releases/2025/0318/104-10003-10041.pdf
    # https://www.archives.gov/files/research/jfk/releases/2025/0318/104-10004-10143%20(C06932208).pdf
    # Replace spaces with %20 in the link
    # Find all links that end with .pdf and use only the last part of the link
    links = []
    base_url = "https://www.archives.gov"
    for link in soup.find_all('a'):
        href = link.get('href')
        # Keep only the last part of the link
        if href:
            if href and href.endswith('.pdf'):
                # Add domain to relative URLs and encode spaces
                full_url = base_url + href.replace(' ', '%20')
                links.append(full_url)

    # Print the links that has spaces or newlines in the name with a counter
    for i, link in enumerate(links):
        if " " in link or "\n" in link:
            print(f"{i}: {link}")
    return list(set(links))


def compare_links_and_filenames(links, filenames):
    # Compare the links and filenames
    for link in links:
        if link.split('/')[-1] not in filenames:
            print(f"{link} not in filenames")


if __name__ == "__main__":
    links = extract_filenames("./data/jfk_files_20250318.html")
    saved_pdf_path = "../../data/jfk/pdf-20250318"
    print(f"Found {len(links)} links")
    count = range(1, 11)
    # Extract the filesnames last part of path in ../data/jfk/*.pdf

    filenames = [f.split('/')[-1]
                 for f in glob.glob(os.path.join(saved_pdf_path, "*.pdf"))]
    compare_links_and_filenames(links, filenames)
    two_links = [f'{i:2}: {link}' for i, link in zip(count, links[:2])]
    print(f"PDF Links: {count} links:\n{'\n'.join(two_links)}")
    print(f"PDF Files: {len(filenames)} filenames: {filenames[:2]}")
