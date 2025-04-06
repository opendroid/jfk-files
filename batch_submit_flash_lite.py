# Author: Gemini Advanced 2.5 Pro (experimental)
# Date: 2025-04-06
# Description: This script is used to submit a batch prediction job to
# the Gemini 1.5 Flash model. It lists all PNG image files from a
# specified GCS bucket and prefix, creates a JSON Lines file
# formatted for the Gemini batch prediction API, and submits the
# job to Vertex AI.

import json
from google.cloud import storage
import vertexai
from vertexai.batch_prediction import BatchPredictionJob
from datetime import datetime

# --- Configuration ---
PROJECT_ID = "jfk-assassination-records"  # Your Google Cloud Project ID
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.0-flash-lite-001"

# --- Input PNG Files location ---
INPUT_BUCKET_NAME = "jfk-assassination-records"
IMAGES_DIR = "images/"

# --- Output Configuration ---
# Bucket where output will be stored
OUTPUT_BUCKET_NAME = "jfk-assassination-records//text/gemini-flash-lite/"
# Batch Prediction output goes into a FOLDER named by the job ID/name.
# This specifies the PARENT directory for those job output folders.
BATCH_JOB_OUTPUT_PARENT_URI = f"gs://{OUTPUT_BUCKET_NAME}"

# --- Temporary Input File Configuration ---
# Creates a unique name for the input file based on the current timestamp
suffix = datetime.now().strftime('%Y%m%d_%H%M')
JSONL_REQUESTS_FILENAME = f"gemini-flash-lite_{suffix}.jsonl"
jsonl_requests_uri = f"gs://{INPUT_BUCKET_NAME}/batch_job_temp/"
jsonl_requests_uri += JSONL_REQUESTS_FILENAME
JSONL_REQUESTS_GCS_URI = jsonl_requests_uri

# --- Helper Functions ---


def gcs_png_files_uris(bucket_name, prefix):
    """
    Lists all .png file URIs in a specified GCS bucket and prefix.

    Args:
        bucket_name (str): The name of the GCS bucket.
        prefix (str): The prefix (folder path) within the bucket to search.

    Returns:
        list: A list of strings, where each string is a GCS URI (gs://...)
              pointing to a .png file. Returns an empty list if no files are
              found.
    """
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    png_files = []
    print(f"Listing PNG files in gs://{bucket_name}/{prefix}...")
    count = 0
    for blob in blobs:
        # Check if the blob name ends with .png (case-insensitive)
        # and ensure it's not just the directory placeholder object itself.
        if blob.name.lower().endswith(".png") and blob.name != prefix:
            png_files.append(f"gs://{bucket_name}/{blob.name}")
            count += 1
            # Provide progress update every 1000 files found
            if count % 10000 == 0:
                print(f"  Found {count} PNG files so far...")
    print(f"Found a total of {len(png_files)} PNG files.")
    return png_files


def get_request_jsonl_name(base_uri, idx):
    """
    Generates a JSONL filename with an index suffix.

    Args:
        base_uri (str): The original GCS URI for the JSONL file
        idx (int): The index to append to the filename

    Returns:
        str: The modified GCS URI with the index in the filename
    """
    if base_uri.endswith('.jsonl'):
        # Split the URI into path and filename
        path_parts = base_uri.rsplit('/', 1)
        if len(path_parts) > 1:
            path = path_parts[0]
            filename = path_parts[1]
            # Split filename into name and extension
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) > 1:
                name = name_parts[0]
                ext = name_parts[1]
                # Create new filename with index
                new_filename = f"{name}_{idx:03d}.{ext}"
                return f"{path}/{new_filename}"
    return base_uri


def create_and_upload_input_file(image_uris, prompt, gcs_requests_uri):
    """
    Creates a JSON Lines file formatted for Gemini multimodal batch prediction
    and uploads it to Google Cloud Storage. Each line contains the prompt and
    a reference to one image.

    Args:
        image_uris (list): A list of GCS URIs (gs://...) to the images.
        prompt (str): The text prompt to include in each prediction request.
        gcs_requests_uri (str): The GCS URI (gs://...) where the generated JSONL
                              file should be uploaded.

    Raises:
        ValueError: If the gcs_requests_uri is not a valid GCS path.
        Exception: If any error occurs during GCS upload.
    """
    print("Generating input file content according to Gemini batch schema...")
    lines = []
    # Define the structure for a single prediction instance, matching the
    # format expected by the Vertex AI Gemini batch prediction API.
    for uri in image_uris:
        instance = {
            "request": {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {"fileData": {"mime_type": "image/png",
                                          "file_uri": uri}}
                        ]
                    }
                ]
            }
        }
        # Python dictionary to a JSON string for the JSON Lines file.
        lines.append(json.dumps(instance))

    # Join all JSON strings with newline characters to form the JSON Lines.
    # Save JSON Lines to a GCS in 1000 lines chunks
    chunks = [lines[i:i+1000] for i in range(0, len(lines), 1000)]
    for idx, chunk in enumerate(chunks):
        jsonl_content = "\n".join(chunk)

        # Get the chunk-specific URI with index
        chunk_uri = get_request_jsonl_name(gcs_requests_uri, idx)
        print(f"Uploading: {idx+1}/{len(chunks)} to {chunk_uri}")
        # Parse the GCS URI to get bucket name and blob name for upload.
        try:
            if not chunk_uri.startswith("gs://"):
                raise ValueError("Output URI must start with gs://")
            # Simple split assuming bucket name doesn't contain '/'
            bucket_name, blob_name = chunk_uri.replace(
                "gs://", "").split("/", 1)
        except ValueError as e:
            print(f"Error parsing GCS URI '{chunk_uri}': {e}")
            raise  # Re-raise the error to stop execution if URI is invalid

        # Get the target bucket and blob objects from GCS client.
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # Upload the generated JSON Lines content to the specified GCS.
        # Set the content type to 'application/jsonl' for clarity.
        blob.upload_from_string(
            jsonl_content, content_type="application/jsonl")


# --- Step1: Get all image URIs of PNG files in the input bucket ---
def step1_get_all_image_uris():
    """
    Lists all PNG image URIs in the specified GCS bucket and prefix.

    Returns:
        list: A list of strings, where each string is a GCS URI (gs://...)
              pointing to a .png file. Returns an empty list if no files are found.
    """
    # 1. Get all PNG image files from the configured GCS input path.
    images_gcs_uris = gcs_png_files_uris(INPUT_BUCKET_NAME, IMAGES_DIR)
    # Save the list of image URIs to a file
    with open('./data/png_uris.txt', 'w') as f:
        for uri in images_gcs_uris:
            f.write(uri + '\n')
    # Exit if no image files were found to process.
    if not images_gcs_uris:
        print("No PNG files found in the specified input location. Exiting.")
        return None
    return images_gcs_uris


def step2_generate_and_save_jsonl_file(images_gcs_uris):
    """
    Generates a JSON Lines file formatted for Gemini multimodal batch prediction
    and uploads it to Google Cloud Storage. Each line contains the prompt and
    a reference to one image.
    """
    # 2. Generate the JSON Lines input file required by the batch job
    #    and upload it to a temporary location in GCS.
    try:
        # The prompt is passed here and packaged
        # inside the function to build each line of the JSONL file.
        prompt = open('data/transcription_prompt.txt', 'r').read()
        create_and_upload_input_file(
            images_gcs_uris, prompt, JSONL_REQUESTS_GCS_URI)
    except Exception as e:
        # If input file creation/upload fails, print error and exit.
        print(f"Failed to create or upload input file: {e}")
        return


def step3_submit_batch_job(requests_json_nl, output_jsonl_uri):
    """
    Submits the Vertex AI Batch Prediction Job.
    """
    # 3. Configure and submit the Vertex AI Batch Prediction Job.
    # Create a unique display name for the job using a timestamp.
    suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
    job_display_name = f"gemini-flash-lite-image-transcription_{suffix}"
    print(f"\nSubmitting Batch Prediction Job: {job_display_name}")

    try:
        # Create and run the Batch Prediction Job using the Vertex AI SDK.
        job = BatchPredictionJob.submit(
            source_model=MODEL_NAME,
            input_dataset=requests_json_nl,
            output_uri_prefix=output_jsonl_uri,
        )

        # Print confirmation and job details upon successful submission.
        print("\nBatch Prediction Job submitted successfully!")
        print(f"  Job Display Name: {job.display_name}")
        print("  Job Resource Name (use for checking status):", end="")
        print(job.resource_name)
        print(f"  Job State: {job.state}")
        print("Monitor progress in the Google Cloud Console", end=" ")
        print("(Vertex AI > Batch Predictions)")
        print("Or use the 'check_job_status.py' ", end=" ")
        print("script with the resource name above. ", end=" ")
        print("Transcription output will be saved in:")
        print(f"{output_jsonl_uri}")
    except Exception as e:
        # Print error details if job submission fails.
        print(f"\nError submitting Batch Prediction Job: {e}")
        print("Check SDK setup, permissions, quotas, and configuration.")
        print(f"The requests JSONL file remains at {requests_json_nl}")


# --- Main Submission Logic ---
def main():
    """
    Main function to orchestrate the batch prediction job submission.
    1. Lists input image files from GCS.
    2. Creates and uploads the formatted JSON Lines input file to GCS.
    3. Configures and submits the Vertex AI Batch Prediction Job.
    """
    # png_uris = step1_get_all_image_uris()
    # if png_uris is None:
    #     return
    # step2_generate_and_save_jsonl_file(png_uris)

    requests_json_nl = "gs://jfk-assassination-records/text-prompt.jsonl"
    output_jsonl_uri = BATCH_JOB_OUTPUT_PARENT_URI
    step3_submit_batch_job(requests_json_nl, output_jsonl_uri)


# Standard Python entry point check.
if __name__ == "__main__":
    # --- Initialization ---
    proj_location = f"{PROJECT_ID}-{LOCATION}"
    print(f"Initializing Vertex AI SDK for project {proj_location}...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    print("Initializing Google Cloud Storage client...")
    storage_client = storage.Client(project=PROJECT_ID)
    main()
