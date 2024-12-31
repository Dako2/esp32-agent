import os
import base64
import openai
import tempfile
from PIL import Image
from io import BytesIO


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

class OpenAIImageAnalyzer:
    """
    A class to encode images and send them to OpenAI's API for analysis.
    """

    def __init__(self, api_key: str = "", model_name: str = "gpt-4-vision"):
        
        """
        Initializes the OpenAIImageAnalyzer with the given API key and model name.

        Args:
            api_key (str): Your OpenAI API key.
            model_name (str): The name of the OpenAI model to use.
        """
        if not api_key:
            # Load OpenAI API Key from environment variable
            OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
            if not OPENAI_API_KEY:
                raise ValueError("Please set the OPENAI_API_KEY environment variable.")
        
        self.api_key = api_key
        self.model_name = model_name
        openai.api_key = self.api_key
        
        self.client = openai.OpenAI()
 
    def analyze_image(self, image_path: str) -> str:
        """
        Sends the image to OpenAI's API for analysis and returns the response.

        Args:
            image_path (str): The file path to the image.

        Returns:
            str: The analysis result from OpenAI.

        Raises:
            Exception: If the API request fails or the response is invalid.
        """
        try:
            # Getting the base64 string
            base64_image = encode_image(image_path)

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "What is in this image?",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
            )

            print(response.choices[0].content.message)
            
            return response.choices[0].content.message
        
        except openai.error.OpenAIError as e:
            print(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error during image analysis: {e}")
            raise

    def display_image(self, image_path: str):
        """
        Opens the image using the default image viewer.

        Args:
            image_path (str): The file path to the image.

        Raises:
            Exception: If opening the image fails.
        """
        try:
            img = Image.open(image_path)
            img.show()  # This will open the image using the default image viewer
            print(f"Image '{image_path}' opened for verification.")
        except Exception as e:
            print(f"Error opening image '{image_path}': {e}")
            raise

# Example Usage
if __name__ == "__main__":

    # Initialize the analyzer
    analyzer = OpenAIImageAnalyzer(api_key="", model_name="gpt-4-vision")  # Update model name as needed

    # Path to your image
    image_path = "captured_image.jpg"  # Replace with your actual image path

    try:
        # Step 1: Analyze the image
        analysis_result = analyzer.analyze_image(image_path)
        print("Analysis from OpenAI:")
        print(analysis_result)
    except Exception as e:
        print(f"Failed to analyze image: {e}")
