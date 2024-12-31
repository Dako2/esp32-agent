import requests
import openai
import os
from io import BytesIO
from PIL import Image
from image_analyzer import OpenAIImageAnalyzer

# ----------------------------
# Configuration
# ----------------------------

# ESP32 Camera Server URL
ESP32_CAMERA_URL = 'http://192.168.86.245/capture'  # Replace with your ESP32 IP and endpoint
#ESP32_CAMERA_URL = 'http://192.168.86.245:81/stream"  # Replace with your ESP32 IP and endpoint

# OpenAI API Key
OPENAI_API_KEY = 'your_openai_api_key_here'  # Replace with your actual OpenAI API key

# OpenAI API Endpoint (Assuming GPT-4 with vision capabilities)
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

# ----------------------------
# Functions
# ----------------------------

def fetch_image(url):
    """
    Fetches an image from the specified URL.

    Args:
        url (str): The URL to fetch the image from.

    Returns:
        bytes: The image data in bytes.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from ESP32: {e}")
        return None

def send_image_to_openai(image_bytes):
    """
    Sends the image to OpenAI's API for processing.

    Args:
        image_bytes (bytes): The image data in bytes.

    Returns:
        dict: The response from OpenAI's API.
    """
    
    # Initialize the analyzer
    analyzer = OpenAIImageAnalyzer(api_key="", model_name="gpt-4-vision")  # Update model name as needed

    # Path to your image
    image_path = "captured_image.jpg"  # Replace with your actual image path

    try:
        # Step 1: Analyze the image
        analysis_result = analyzer.analyze_image(image_path)
        print("Analysis from OpenAI:")
        print(analysis_result)
        return analysis_result
    except Exception as e:
        print(f"Failed to analyze image: {e}")

# Step 1: Fetch the image from ESP32
image_data = fetch_image(ESP32_CAMERA_URL)
if not image_data:
    print("Failed to retrieve image. Exiting.")
    
# Optional: Save the image locally for verification
with open('captured_image.jpg', 'wb') as f:
    f.write(image_data)
print("Image fetched and saved as 'captured_image.jpg'.")

# Step 2: Send the image to OpenAI
openai_response = send_image_to_openai(image_data)
if not openai_response:
    print("Failed to get response from OpenAI.")
    

# Step 3: Process and display the response
print("Response from OpenAI:")
print(openai_response)
