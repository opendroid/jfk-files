# Read the JSONL file from GCS and print the results in a
# human readable format. The JSONL file is the output of the
# A sample JSONL file is available at ./data/flash_predictions.jsonl

import json
from google.cloud import storage
from rich.console import Console
from rich.markdown import Markdown


def read_jsonl_file(storage_client, bucket_name, blob_name):
    # Use the storage_client passed from the caller
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Read the JSONL file
    jsonl_content = blob.download_as_string(
        client=storage_client).decode('utf-8')
    # Parse the JSONL file
    predictions = []
    not_parsed_count = 0
    for line in jsonl_content.splitlines():
        try:
            prediction = json.loads(line)
            predictions.append(prediction)
        except Exception as e:
            not_parsed_count += 1
            print(f"Error parsing line: {e}:")
            print(line)
            continue
    if not_parsed_count > 0:
        print(f"Not parsed count: {not_parsed_count}")
    return predictions


def print_prediction(prediction, console):
    print(json.dumps(prediction, indent=2))
    # Parse the prediction
    content = prediction['response']['candidates'][0]['content']
    text = content['parts'][0]['text']
    # Use Markdown to print the prediction
    markdown = Markdown(text)
    console.print(markdown)


def find_key_in_nested_json(json_object, key):
    # Write a find key in a nested JSON object
    # some of the keys are arrays
    for k, v in json_object.items():
        if k == key:
            return v
        elif isinstance(v, list):
            for el in v:
                if isinstance(el, dict):
                    result = find_key_in_nested_json(el, key)
                    if result is not None:
                        return result
        elif isinstance(v, dict):
            result = find_key_in_nested_json(v, key)
            if result is not None:
                return result
    return None


def process_all_predictions(storage_client, bucket_name,
                            prediction_file_names):
    """Input is a list of prediction files.
    The function will print the predictions in a human readable format.

    Args:
        predictions (_type_): _description_
    """
    summaries, count = [], 0
    no_transcription_count = 0
    for file_name in prediction_file_names:
        # Fetch the prediction file from GCS
        predictions = read_jsonl_file(
            storage_client, bucket_name, file_name)
        # Print the prediction
        row_count = 0
        for prediction in predictions:
            row_count += 1
            # print_prediction(prediction, console)
            # Get the image name from the prediction file name
            try:
                content = prediction["request"]["contents"][0]
                image_name = find_key_in_nested_json(content, "file_uri")
                if image_name is None:
                    image_name = find_key_in_nested_json(content, "fileUri")
                    if image_name is None:
                        print(json.dumps(prediction, indent=2))
                        exit()
                response = prediction["response"]
                model_version = response["modelVersion"]
                usage_metadata = response["usageMetadata"]
                if "candidatesTokenCount" in usage_metadata:
                    response_tokens = usage_metadata["candidatesTokenCount"]
                else:
                    response_tokens = 0
                prompt_tokens = usage_metadata["promptTokensDetails"]
                prompt_text_tokens = prompt_tokens[0]["tokenCount"]
                prompt_image_tokens = prompt_tokens[1]["tokenCount"]
                total_tokens = usage_metadata["totalTokenCount"]
                content = response["candidates"][0]["content"]
                transcription_text = find_key_in_nested_json(response, "text")
                if transcription_text is None:
                    no_transcription_count += 1
                    transcription_text = "No transcription done."
                    print(f"{no_transcription_count}: {image_name}")

                # transcription_text = content["parts"][0]["text"]
                summary = {
                    "image_name": image_name,
                    "model_version": model_version,
                    "response_tokens": response_tokens,
                    "prompt_text_tokens": prompt_text_tokens,
                    "prompt_image_tokens": prompt_image_tokens,
                    "total_tokens": total_tokens,
                    "transcription_text": transcription_text
                }
                summaries.append(summary)
            except Exception as e:
                count += 1
                print(f"JSON Error: {count}: {e}")
                print(json.dumps(prediction, indent=2))
                continue
    # Sort the summaries by the image_name
    summaries.sort(key=lambda x: x["image_name"])
    print(f"No transcription found for {no_transcription_count} images.")
    return summaries


def print_summary(summary):
    console = Console()
    console.print(f"Image name: {summary['image_name']}")
    console.print(f"Model version: {summary['model_version']}")
    console.print.print(f"Response tokens: {summary['response_tokens']}")
    console.print(f"Prompt text tokens: {summary['prompt_text_tokens']}")
    console.print(f"Prompt image tokens: {summary['prompt_image_tokens']}")
    markdown = Markdown(summary["transcription_text"])
    console.print(markdown)


def fetch_prediction_files(storage_client, bucket_name, blob_name):
    """The files are stred in as:
    gs://jfk-assassination-records/text/gemini-flash-lite/**/predictions.jsonl
    The function will return a list of the prediction files.

    Args:
        bucket_name (_type_): _description_
        blob_name (_type_): _description_
    """

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Get a list of all the predictions.jsonl files in all subfolders
    prediction_file_names = []
    for blob in bucket.list_blobs(prefix=blob_name):
        if blob.name.endswith('predictions.jsonl'):
            prediction_file_names.append(blob.name)
    return prediction_file_names


def save_summaries_jsonl(summaries, output_file_name):
    with open(output_file_name, 'w') as f:
        for summary in summaries:
            f.write(json.dumps(summary) + '\n')


def print_all_summaries(summaries):
    console = Console()
    response_tokens, total_tokens = 0, 0
    prompt_text_tokens, prompt_image_tokens = 0, 0
    for summary in summaries:
        response_tokens += summary["response_tokens"]
        total_tokens += summary["total_tokens"]
        prompt_text_tokens += summary["prompt_text_tokens"]
        prompt_image_tokens += summary["prompt_image_tokens"]
    console.print(f"Total prompt text tokens: {prompt_text_tokens}")
    console.print(f"Total prompt image tokens: {prompt_image_tokens}")
    console.print(f"Total response tokens: {response_tokens}")
    console.print(f"Total tokens: {total_tokens}")
    return


def main():
    # Initialize the GCS client
    storage_client = storage.Client()

    # Get a list of all the prediction files names, Get all
    # the **/predictions.jsonl files
    bucket_name = "jfk-assassination-records"
    blob_name = "text/gemini-flash-lite/"
    prediction_file_names = fetch_prediction_files(storage_client,
                                                   bucket_name, blob_name)

    print(f"Found {len(prediction_file_names)} prediction files.")

    # Create summary of all the transcriptions done.
    # Each prediction file contains predictions as a JSONL.
    # Each line is transcription of one image.
    summaries = process_all_predictions(
        storage_client, bucket_name, prediction_file_names)

    dest_dir = "/whatever/"
    output_file_name = dest_dir + "/gemini_predictions.jsonl"
    save_summaries_jsonl(summaries, output_file_name)

    print_all_summaries(summaries)


if __name__ == "__main__":
    main()
