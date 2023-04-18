# k8s-image-recognition

This repository was made for my final project for my Engineer degree at Unilasalle Amiens, thank you to the staff of the school as well as to the teachers for these 3 years which complete my 6 years of studies in the field of software and system/network engineering.
It concists in a simple automated k8s cluster build on AWS deploying an actix_web reverse proxy API to call an inference of google/pix2struct model that i trained for french road signs, stored in Huggingface.co 

## How to Use :
```shell
kompose convert -f .\docker-compose.yml
kubectl --kubeconfig=<Path to your configuration> apply -f .
kubectl get pod
kubectl get service
kubectl get deployment
```
### Linux/MacOS Image build requierments
```shell
echo "HUGGING_FACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_TO_YOUR_MODEL" > ./descrivizio001/.env
```
### Windows build requierments
```shell
New-Item -ItemType File -Path ".\descrivizio001\.env" -Value "HUGGING_FACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_TO_YOUR_MODEL"
```

![k8s-load-balanced.drawio.png](doc%2Frsc%2Fimg%2Fk8s-load-balanced.drawio.png)
