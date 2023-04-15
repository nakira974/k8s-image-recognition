from typing import Any, Dict
import io
from PIL import Image
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.param_functions import Body
from transformers import Pix2StructForConditionalGeneration, Pix2StructProcessor
from decouple import config
from huggingface_hub import login
from pydantic import BaseModel
from ImagePredictionController import ImagePredictionController
from ApplicationImage import ApplicationImage
import uvicorn
import base64

app = FastAPI()
API_KEY = config('HUGGING_FACE_TOKEN')
login(API_KEY)
google_model = Pix2StructForConditionalGeneration.from_pretrained("Aloblock/descrivizio")
processor = Pix2StructProcessor.from_pretrained("Aloblock/descrivizio")
controller = ImagePredictionController(google_model, processor)


@app.post('/model/descrivizio-001')
async def predict_image(request: Request):
    return await controller.predict(request)


uvicorn.run(app, host="0.0.0.0", port=7777, log_config=f"./log.ini")

