FROM python:3.9.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r ./requirements.txt

COPY . .

EXPOSE 80

CMD ["uvicorn", "main:app", "--reload", "--host=0.0.0.0", "--port=80"]

#docker build -t descrivizio001