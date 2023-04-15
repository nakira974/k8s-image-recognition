import io
from typing import Any, Dict
import requests
from PIL import Image
from fastapi import HTTPException, Request
from transformers import Pix2StructForConditionalGeneration, Pix2StructProcessor

from ApplicationImage import ApplicationImage


class ImagePredictionController:
    def __init__(self, model: Pix2StructForConditionalGeneration, processor: Pix2StructProcessor) -> None:
        self.model = model
        self.processor = processor

    async def predict(self, request: Request) -> Dict[str, Any]:
        try:
            application_image = await request.body()
            print("Processing image...")
            image = Image.open(io.BytesIO(application_image))
            inputs = self.processor(images=image, return_tensors="pt")
            predictions = self.model.generate(**inputs)
            prediction_text = self.processor.decode(predictions[0], skip_special_tokens=True)
            print("Image process ended...")
            return {"prediction": prediction_text}
        except:
            raise HTTPException(status_code=400, detail="Error processing image")
