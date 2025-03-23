# Leverage the Tesseract library to do OCR

import pytesseract
from PIL import Image
from pymupdf import fitz
import yaml
import io


def image_to_text(image_path: str) -> str:
    """
    Leverage the Tesseract library to do OCR
    """
    return pytesseract.image_to_string(image_path)


def pdf_to_text(pdf_path: str) -> list:
    """
    Renders each page of the PDF as an image and applies Tesseract OCR.
    Returns a list of dicts, each with 'page_number' and 'text' keys.
    """
    pages_text = []
    doc = fitz.open(pdf_path)

    for page_index, page in enumerate(doc):
        image_list = page.get_images()
        for image in image_list:
            base_image = doc.extract_image(image[0])
            image_bytes = Image.open(io.BytesIO(base_image["image"]))
            text = pytesseract.image_to_string(image_bytes)

            # Store results
            pages_text.append({
                "page_number": page_index,
                "text": text
            })

    doc.close()
    return pages_text


def main(options):
    """
    Main function to leverage the Tesseract library to do OCR
    """
    # image_path = f'{options["sample_image"]["page1"]}'
    # print(image_to_text(image_path))
    pdf_path = f"{options["sample_pdf"]["doc2"]}"
    ocr_results = pdf_to_text(pdf_path)
    for result in ocr_results:
        print(f"Page {result['page_number']}\n{result['text']}\n")


if __name__ == "__main__":
    with open("../config.yml", "r") as f:
        options = yaml.load(f, Loader=yaml.FullLoader)
        main(options)
