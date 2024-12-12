import logging
import os
from azure.storage.blob import BlobServiceClient
import azure.functions as func
import requests

# The main function entry point, triggered by a new blob upload
def main(myblob: func.InputStream, blob: func.Out[func.InputStream]):
    logging.info(f"Processing blob: {myblob.name}, Size: {myblob.length} bytes")

    # Determine file type based on blob name
    if myblob.name.endswith(".jpg") or myblob.name.endswith(".png"):
        process_image(myblob.name)
    elif myblob.name.endswith(".txt"):
        process_text(myblob.name)
    else:
        logging.warning(f"Unsupported file type for blob: {myblob.name}")

# Function to process image files using the Computer Vision API
def process_image(blob_name):
    """Process image files using Computer Vision API"""
    endpoint = os.getenv("COMPUTER_VISION_ENDPOINT").rstrip("/")  # Ensure no trailing slash
    key = os.getenv("COMPUTER_VISION_KEY")
    image_url = f"https://dtmluitstorage.blob.core.windows.net/luit-container/{blob_name}"
    
    # Log the endpoint and image URL for debugging
    logging.info(f"Computer Vision Endpoint: {endpoint}")
    logging.info(f"Image URL: {image_url}")

    # Prepare API request
    analyze_url = f"{endpoint}/vision/v3.2/analyze"
    headers = {"Ocp-Apim-Subscription-Key": key}
    params = {"visualFeatures": "Categories,Description,Tags"}
    data = {"url": image_url}
    
    try:
        response = requests.post(analyze_url, headers=headers, params=params, json=data)
        response.raise_for_status()  # Raise an error for bad requests
        analysis = response.json()
        logging.info(f"Image analysis result: {analysis}")
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error occurred while processing image: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")

# Function to process text files using the Text Analytics API
def process_text(blob_name):
    """Process text files using Text Analytics API"""
    endpoint = os.getenv("TEXT_ANALYTICS_ENDPOINT").rstrip("/")  # Ensure no trailing slash
    key = os.getenv("TEXT_ANALYTICS_KEY")
    
    # Download the blob content
    blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AzureWebJobsStorage"))
    blob_client = blob_service_client.get_blob_client(container="luit-container", blob=blob_name)
    blob_content = blob_client.download_blob().readall().decode("utf-8")
    
    # Log the endpoint and blob content for debugging
    logging.info(f"Text Analytics Endpoint: {endpoint}")
    logging.info(f"Blob content: {blob_content}")

    # Prepare API request for sentiment analysis
    analyze_url = f"{endpoint}/text/analytics/v3.1/sentiment"
    headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"}
    data = {"documents": [{"id": "1", "language": "en", "text": blob_content}]}
    
    try:
        response = requests.post(analyze_url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for bad requests
        analysis = response.json()
        logging.info(f"Text analysis result: {analysis}")
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error occurred while processing text: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
