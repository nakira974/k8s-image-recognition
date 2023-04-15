
# Base image
FROM python:3.9-slim-buster

# Set working directory
WORKDIR /app

# Copy over the necessary files
COPY requirements.txt .
COPY ImagePredictionController.py .
COPY ApplicationImage.py .
COPY main.py .
COPY log.ini .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 7777 for the application to run on
EXPOSE 7777

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7777", "--log-config=log.ini"]