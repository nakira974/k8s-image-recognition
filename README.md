# k8s-image-recognition

This repository was made for a study project.

It concists in a simple automated k8s cluster build on AWS deploying an actix_web reverse proxy API to call an inference of google/pix2struct model that i trained for french road signs, stored in Huggingface.co.

CI\CD are building docker images resulting from the main branch's content.

## How to Use :
```shell
kompose convert -f .\kube-docker-compose.yml
kubectl --kubeconfig=<Path to your configuration> apply -f <desirated-deployments>
...
kubectl expose deployment descrivizio001-web --type="NodePort" --port 80 --name=desrivizio001-web
kubectl expose deployment descrivizio001-api --type="NodePort" --port 8085 --name=descrivizio001-api
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
