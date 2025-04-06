from bs4 import BeautifulSoup
import os
import glob


def extract_pdf_urls(file_path):
    """Extract the pdf links from the html file located in {file_path}.

    Args:
        file_path (str): Path to the html file containing the links.

    Returns:
        list: List of PDF URLs
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


def get_links_not_downloaded(links, filenames):
    # Compare the links and filenames
    not_downloaded = []
    for link in links:
        # Sanitize the link, replace %20 with ''
        # This was done during download_files.py
        link = link.replace('%20', '')
        link = link.split('/')[-1]
        if link not in filenames:
            not_downloaded.append(link)

    return not_downloaded


if __name__ == "__main__":
    links = extract_pdf_urls("./data/jfk_files_20250318.html")
    saved_pdf_path = "../../data/jfk/docs/pdf/20250318"
    print(f"Found {len(links)} links")

    # Extract the filesnames last part of path
    filenames = [f.split('/')[-1]
                 for f in glob.glob(os.path.join(saved_pdf_path, "*.pdf"))]
    not_downloaded = get_links_not_downloaded(links, filenames)
    if len(not_downloaded) > 0:
        print(f"Found {len(not_downloaded)} links not in filenames")
        for link in not_downloaded:
            print(link)
    else:
        print("All links are in the filenames")
