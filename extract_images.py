import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
import json
from tqdm import tqdm


def extract_images_from_pdf(pdf_path, output_dir):
    """Extract images from a PDF file. For each page, we extract all images
    and save them to the output directory. The images are saved with the
    naming convention:
      <pdf_name>_page<page_number>_img<image_number>.<extension>

    Args:
        pdf_path (str): Path to the PDF file.
        output_dir (str): Path to the directory to save the images.
    """
    n_images = 0
    try:
        # Open PDF
        doc = fitz.open(pdf_path)

        # Get PDF filename without extension
        pdf_name = Path(pdf_path).stem

        # Extract images from each page
        for page_num, page in enumerate(doc):
            image_list = page.get_images()

            # Create a directory for the page
            page_dir = f"{output_dir}/{pdf_name}"
            Path(page_dir).mkdir(parents=True, exist_ok=True)

            # Save each image
            for img_idx, img in enumerate(image_list):
                xref = img[0]  # image reference number
                base_img = doc.extract_image(xref)
                image_bytes = base_img["image"]

                # Create unique filename
                image_suffix = f"img_{img_idx+1:02d}.{base_img['ext']}"
                page_suffix = f"page_{page_num+1:03d}"
                image_filename = f"{pdf_name}_{page_suffix}_{image_suffix}"
                image_path = f"{output_dir}/{pdf_name}/{image_filename}"
                n_images += 1
                # Save image
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
        print(f": {n_images} {pdf_path}")
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
    finally:
        if 'doc' in locals():
            doc.close()
    return n_images


def extract_image_metadata(png_path):
    """Extract metadata from a PNG image. Assume that the image is a page of
    a corresponding PDF. For example,
     PDF Name:"198-10009-10099.pdf",
     Saved images are:
      "198-10009-10099_page1_img1.png", "198-10009-10099_page1_img2.png",
      "198-10009-10099_page2_img1.png", "198-10009-10099_page2_img2.png", etc.
      We use the naming convention to extract the PDF name and the page number.
      Also there was only one image per page in the original PDF.

    Args:
        png_path (str): Path to the PNG image.

    Returns:
        dict: Metadata of the image as a dictionary.
    """
    image = Image.open(png_path)
    # Get image size
    image_size = len(image.tobytes())
    # Get image resolution
    image_resolution = image.info.get("dpi", (96, 96))
    # Get image dimensions
    image_dimensions = image.size
    # Get image format
    image_format = image.format
    # Get PDF name:
    try:
        index = png_path.split("/")[-1].find("_page")
        pdf_name = png_path.split("/")[-1][:index] + ".pdf"
        # Get page number
        index_img = png_path.split("/")[-1].find("_img")
        page_number = png_path.split("/")[-1][index+6:index_img]
        return {
            "size": image_size,
            "resolution": image_resolution,
            "dimensions": image_dimensions,
            "format": image_format,
            "name": png_path.split("/")[-1],
            "pdf_name": pdf_name,
            "page_number": page_number
        }
    except Exception as e:
        print(f"Error extracting metadata from {png_path}: {str(e)}")
        return None


def extract_images_from_all_pdf(pdf_dir, output_dir):
    """Extract images from all PDFs in the given directory.

    Args:
        pdf_dir (str): Path to the directory containing the PDFs.
        output_dir (str): Path to the directory to save the images.
    """
    # Setup paths
    pdf_dir = Path(pdf_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process all PDFs
    count = 0
    for i, pdf_path in enumerate(pdf_dir.glob("*.pdf")):
        print(f"{i+1:05d}", end=" ")
        count += extract_images_from_pdf(pdf_path, output_dir)
    print(f"Total images extracted: {count}")


def extract_image_metadata_from_all_png(png_dir, metadata_file):
    """Extract metadata from all PNG images in the given directory.

    Args:
        png_dir (str): Path to the directory containing the PNG images.
        metadata_file (str): Path to the file to save the metadata.
    """
    # Setup paths
    png_dir = Path(png_dir)
    # Get all the png files in the directory recursively, sorted by name
    png_glob = sorted(png_dir.glob("**/*.png"))

    results = []
    # Add progress bar using tqdm
    images_count = len(list(png_glob))
    progress_bar = tqdm(desc="Images processed",
                        total=images_count, colour="#00FFFF", unit=" images")
    # Reset glob iterator
    for i, png_path in enumerate(png_glob):
        r = extract_image_metadata(png_path.as_posix())
        if r is not None:
            results.append(r)
        else:
            print(f"{i+1:05d}: Error extracting metadata from {png_path}")
            break
        progress_bar.update(1)
    progress_bar.close()
    # Save results to JSON file
    with open(metadata_file, "w") as f:
        json.dump(results, f, indent=4)


def main():
    # Extract images from all PDFs
    pdf_dir = "../../data/jfk/docs/pdf/20250318"
    output_dir = "../../data/jfk/images/images/20250318"
    extract_images_from_all_pdf(pdf_dir, output_dir)

    # Extract image metadata
    png_dir = "../../data/jfk/images/images/20250318"
    metadata_file = "../../data/jfk/images/images/20250318-metadata.json"
    extract_image_metadata_from_all_png(png_dir, metadata_file)


if __name__ == "__main__":
    main()
