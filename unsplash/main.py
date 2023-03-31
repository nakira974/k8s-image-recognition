import os

from unsplash.SoucoupeV1 import Soucoupe
from huggingface_hub import login
from transformers import Pix2StructForConditionalGeneration, Pix2StructProcessor
import requests
from PIL import Image
from decouple import config
import torch

print("CUDA DEVICE :"+torch.__version__)
print("IS CUDA AVAILABLE : ", end=torch.cuda.is_available().__str__()+"\n")

API_KEY = config('HUGGING_FACE_TOKEN')

login(API_KEY)

google_model = Pix2StructForConditionalGeneration.from_pretrained("Aloblock/descrivizio")
processor = Pix2StructProcessor.from_pretrained("Aloblock/descrivizio")

url = "https://www.ilankelman.org/stopsigns/australia.jpg"
image = Image.open(requests.get(url, stream=True).raw)
inputs = processor(images=image, return_tensors="pt")
predictions = google_model.generate(**inputs)
print(processor.decode(predictions[0], skip_special_tokens=True))

