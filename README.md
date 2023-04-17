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

![k8s-load-balanced.drawio.png](doc%2Frsc%2Fimg%2Fk8s-load-balanced.drawio.png)