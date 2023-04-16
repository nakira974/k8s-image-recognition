# k8s-image-recognition
A simple Image recognition model exposed on uvicorn, exposed by an Actix reverse proxy

### Linux/MacOS
```shell
echo "HUGGING_FACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_TO_YOUR_MODEL" > ./descrivizio001/.env
```
### Windows
```shell
New-Item -ItemType File -Path "C:\path\to\descrivizio001\.env" -Value "HUGGING_FACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_TO_YOUR_MODEL"
```