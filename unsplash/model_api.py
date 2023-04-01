from typing import Any, Dict
import io
from PIL import Image
import torch
from fastapi import FastAPI, HTTPException
from fastapi.param_functions import Body
from transformers import Pix2StructForConditionalGeneration, Pix2StructProcessor
from decouple import config
from huggingface_hub import login

app = FastAPI()
API_KEY = config('HUGGING_FACE_TOKEN')
login(API_KEY)
google_model = Pix2StructForConditionalGeneration.from_pretrained("Aloblock/descrivizio")
processor = Pix2StructProcessor.from_pretrained("Aloblock/descrivizio")


class ImagePredictionController:
    def __init__(self, model: Pix2StructForConditionalGeneration, processor: Pix2StructProcessor) -> None:
        self.model = model
        self.processor = processor

    async def predict(self, image_bytes: bytes) -> Dict[str, Any]:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            inputs = self.processor(images=image, return_tensors="pt")
            predictions = self.model.generate(**inputs)
            prediction_text = self.processor.decode(predictions[0], skip_special_tokens=True)
            return {"prediction": prediction_text}
        except:
            raise HTTPException(status_code=400, detail="Error processing image")


controller = ImagePredictionController(google_model, processor)


@app.get('/model/descrivizio-001')
async def predict_image(image_bytes: bytes = Body(...)):
    return await controller.predict(image_bytes)
