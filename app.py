# import base64
import json
import os
import time
from icecream import ic
import requests
import numpy as np
from PIL import Image
import io
import gradio as gr
import traceback

# Load the existing workflow from JSON in the global scope
with open('img_and_prompt_to_img.json', 'r') as file:
    api_data = json.load(file)
URL = "http://127.0.0.1:8188/api/prompt"
OUTPUT_DIR = "/home/user/workspace/ComfyUI/output"
IMAGE_UPLOAD_URL="http://127.0.0.1:8188/api/upload/image"

# Start queue for sending workflow
def start_queue(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode("utf-8")
    requests.post(url=URL, data=data)

def get_latest_image(folder):
    files = os.listdir(folder)
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    image_files.sort(key=lambda x: os.path.getmtime(os.path.join(folder, x)))
    latest_image = os.path.join(folder, image_files[-1]) if image_files else None
    return latest_image

def upload_image(file):
    try:
        image = Image.fromarray(file)
        # print(image,type(image))
        img_byte_arr = io.BytesIO()
        image_format = image.format if image.format else 'PNG'
        image.save(img_byte_arr, format=image_format)  # Change format to the desired one (JPEG, PNG, etc.)
        img_byte_arr = img_byte_arr.getvalue()

        files = [("image", (f"image.{image_format.lower()}", img_byte_arr, f"image/{image_format.lower()}"))]
        response = requests.post(IMAGE_UPLOAD_URL, files=files)
        # print(response.text)
        if response.status_code != 200:
            print("Error: The server returned an error.")
            return {}
        else:
            return response.json()
    except Exception as e:
        print(traceback.format_exc())

def generate_image(prompt,file):
    image_upolad_response = upload_image(file)
    # Updating the prompt in the existing workflow
    api_data['6']['inputs']['text'] = prompt
    api_data['13']['inputs']['image'] = image_upolad_response.get("name","")

    previous_image = get_latest_image (OUTPUT_DIR)
    # Start the pipeline
    start_queue(api_data)

    while True:
        latest_image=get_latest_image(OUTPUT_DIR)
        if latest_image != previous_image:
           return latest_image
        time.sleep(4)  

if __name__ == "__main__":
    demo = gr.Interface(fn=generate_image, inputs=["text","image"], outputs="image")
    demo.launch(allowed_paths=['/home/user/workspace/ComfyUI/output'])

