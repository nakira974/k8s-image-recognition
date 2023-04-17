# k8s-image-recognition


A simple Image recognition model exposed on uvicorn, exposed by an Actix reverse proxy,
that runs in a k8s cluster hosted on aws
### Linux/MacOS
```shell
echo "HUGGING_FACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_TO_YOUR_MODEL" > ./descrivizio001/.env
```
### Windows
```shell
New-Item -ItemType File -Path ".\descrivizio001\.env" -Value "HUGGING_FACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_TO_YOUR_MODEL"
```

![Application-Architecture](..%2F..%2F..%2FDownloads%2Fk8s-load-balanced.drawio.png)