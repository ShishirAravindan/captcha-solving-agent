#!python3

import base64
import requests
import logging
import logging.config
import utils
from PIL import Image
import io

config = {
    "model": "llava",
    "prompt": "Respond with 1 if image has a {target}, else 0.",
    "server_url": "http://localhost:11434/api/generate",
    "api_timeout": 200
}

def decaptcha(target: str, image_path: str, grid_size: int) -> list[bool]:
    """
    Process a list of images using the vLLM API for classification.
    Args:
        - `target`: The classification target (e.g. Select all squares with "traffic lights").
        - `image_path`: Path of image containing the 9 sub-images.
    Returns:
        list contains 9 predictions (boolean) for each sub image:
            0 1 2
            3 4 5
            6 7 8
    """
    logging.info(f"Enter decaptcha: {target}, {image_path}")

    images = _split_and_encode_image(image_path, grid_size)
    logging.debug(f"Images split and encoded: {target}, {image_path}")

    preds = _process_images(target, images)
    logging.info(f"Exit decaptcha: {target}, {image_path}, {preds}")
    return preds


def _split_and_encode_image(image_path: str, grid_size: int) -> list[str]:
    """
    Split the image into 9 equal parts and return base64 
    encoded strings for each part.
    """
    with Image.open(image_path) as img:
        width, height = img.size
        square_size = min(width, height) // grid_size
        
        # List to store base64 encoded image parts
        encoded_parts = []
        
        for i in range(grid_size):
            for j in range(grid_size):
                # Coordinates for cropping
                left = j * square_size
                top = i * square_size
                right = left + square_size
                bottom = top + square_size
                
                square = img.crop((left, top, right, bottom))
                
                buffer = io.BytesIO()
                square.save(buffer, format="PNG")
                base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                encoded_parts.append(base64_image)
    return encoded_parts
    

def _process_images(target: str, images: list[str]) -> list[bool]:
    """
    Process a list of images using the vLLM API for classification.

    Returns:
        list: A list of integer results (0 or 1) corresponding to each image's classification.

    Note:
        - The return value is None which means it could not identify some blocks and retry
          button on the captcha page has to be pressed
    """
    results = []

    for image in images:
        classification = _make_vLLM_API_call(target, image)
        if classification == '0':
            results.append(False)
        elif classification == '1':
            results.append(True)
        else:
            logging.error(f'Model returned non-regular prediction: {classification}')
            return None
    return results

def _make_vLLM_API_call(target:str, image: str) -> str:
    """Make an API call to the vLLM server for image classification.

    Args:
        - `prompt` (str): The classification prompt to send to the server.
        - `image` (str): The base64-encoded image data.

    Returns:
        - str: The stripped response from the server if the call is successful.
        None: If the API call fails.

    Raises: `requests.exceptions.RequestException`: If there's an error in 
    making the HTTP request.

    Note: This function logs the API call status and any errors that occur.
    """
    json_data = {
        "model": config["model"],
        "prompt": config["prompt"].format(target=target),
        "stream": False,
        "images": [image]
    }
    response = requests.post(config["server_url"], json=json_data, timeout=config["api_timeout"])
    if response.status_code == 200:
        prediction = response.json()['response'].strip()
        logging.debug(f"_make_vLLM_API_call success: {target}, {prediction}")
        return prediction
    logging.error(f"_make_vLLM_API_call failed: {target}, {response.status_code}, {response.text}")
    return "-1"


#--------------------------------------------------------------------------------
# Test code
def test_main():
    logging.config.fileConfig("test_log.ini")
    ret = decaptcha("bus", "../vLLM-demo/bus.jpg")
    utils.assert_equal("bus", ret, [None, False, False, True, True, True, False, True, None])

    # TODO: All other test case
        
    
if __name__ == "__main__":
    test_main()
