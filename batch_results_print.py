# Read the JSONL file from GCS and print the results in a
# human readable format. The JSONL file is the output of the
# A sample JSONL file is available at ./data/flash_predictions.jsonl

import json
from google.cloud import storage
from rich.console import Console
from rich.markdown import Markdown


def read_jsonl_file(bucket_name, blob_name):
    # Initialize the GCS client
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Read the JSONL file
    jsonl_content = blob.download_as_string(
        client=storage_client).decode('utf-8')
    # Parse the JSONL file
    predictions = [json.loads(line) for line in jsonl_content.splitlines()]
    return predictions


def print_prediction(prediction, console):
    # Parse the prediction
    prediction = prediction['response']['candidates'][0]['content']['parts'][0]['text']
    # Use Markdown to print the prediction
    markdown = Markdown(prediction)
    console.print(markdown)


def main():
    # Read the JSONL file from GCS
    bucket_name = "jfk-assassination-records"
    blob_name = "text/gemini-flash-lite/prediction-model-2025-04-06T05:15:27.793955Z/predictions.jsonl"
    # Read the JSONL file
    predictions = read_jsonl_file(bucket_name, blob_name)
    # Print the results in a human readable format
    console = Console()
    for prediction in predictions:
        console.print(f"Prediction {prediction['id']}")
        print_prediction(prediction, console)


if __name__ == "__main__":
    main()
