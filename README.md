# JFK Files

The JFK files were launched on Mar 18, 2025. The files were posted on
[JFK Assassination Records - 2025 Documents Release](https://www.archives.gov/research/jfk/release-2025).
The project details are on [JFK Assassination Records Analysis](https://docs.google.com/document/d/1zvEYoMBZEyy1ABDUnuSLDPGfOWRKW0euB-CbaC4uUXA/edit?usp=sharing)

The purpose of this directory is to:
1. Download all 2,182 files.
	- download all 2,182 files and save them to huggingface hub.
2. Extract images:
	- extract the images from the files.
	- Save images to the huggingface hub.
4. Save metadata:
	- save the metadata to the huggingface hub.
5. OCR:
	- Do a OCR on the images .
	- Check teh OCR results again LLM.
	- If the OCR results are not good enough, use LLM to correct the OCR results.

## Tools
The coding was assisted by the:
1. __cursor__ code editor using __Claude-3.5-Sonnet__.
2. Grok for difficult problems where sonnet failed.
3. ChatGPT for general coding assistance.

## Plan

1. Download the files from the web page.
2. Process the images using OCR
3. Improce the OCR using LLMs
4. Check the results using LLMs
5. Save the results

### Download the files
The `data_prep` contains utilities to extract the filenames from webspage and download the files.

1. Manually download the webpage from [URL](https://www.archives.gov/research/jfk/release-2025). Make sure to select "All" entries in the dropdown.
2. Saved the webpage as `./data/jfk_files_20250318.html`.
3. `extract_filenames.py`: parses the webpage to find the links to the files.
    - The files are in href tags with names that end in `.pdf`.
4. `download_files.py`: downloads the files from the links. The files are saved in the temp directory.
5. `extract_images.py`: extracts the images from the files. The images are saved in the temp directory.


#### Downlaoded Data

The downloaded data is saved on the:
- [huggingface](https://huggingface.co/datasets/opendriod/jfk-assassination-records)
- [Google Storage Bucket](https://storage.googleapis.com/jfk-assassination-records)

The data folder structure is as follows:

```
jfk-assassination-records/
    - pdf/
        - 20250318/
            - 104-10001-10002.pdf
            - 104-10003-10041.pdf
            - ...
        - 20250320/
            - 104-10302-10024.pdf
            - 124-10167-10498.pdf
            - ...
		- ...
    - images/
        - 20250318/
            - 104-10003-10041/
                - 104-10003-10041_page_001_img_01.png
                - 104-10003-10041_page_001_img_02.png
                - ...
        - 20250320/
            - 104-10302-10024/
                - 104-10302-10024_page_001_img_01.png
                - 104-10302-10024_page_002_img_01.png
                - ...
```

### OCR
The OCTR
