use actix_web::{
    post, get, patch, web, App, Error, HttpResponse, HttpRequest, HttpServer, Result,
    client::{Client, ClientResponse, HttpClientError}
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use futures::stream::StreamExt;
use std::convert::TryFrom;
use std::io::Cursor;

#[derive(Debug, Serialize, Deserialize)]
pub struct ApplicationPhoto {
    // fields for application photo
}

/// Send a POST request to the Descrivizio model for image analysis
#[post("/nakira974/model/descrivizio-001/process")]
async fn descrivizio_analyze(
    app_photo: web::Json<ApplicationPhoto>,
    req: HttpRequest,
    client: web::Data<Client>
) -> Result<HttpResponse, Error> {
    let uri = format!("http://{}{}/model/descrivizio-001", req.uri().host().unwrap(), req.uri().path());
    let response = client.post(uri)
        .header("Content-Type", "application/json")
        .send_json(&app_photo)
        .await?;

    let mut result = HttpResponse::build(response.status());
    for (header_name, header_value) in response.headers() {
        result.header(header_name.clone(), header_value.clone());
    }

    let bytes = response.body().await?;
    Ok(result.body(bytes))
}

/// Send a PATCH request to the Descrivizio model for image analysis
#[patch("/nakira974/model/descrivizio-001/process")]
async fn descrivizio_analyze_from_header(
    req: HttpRequest,
    client: web::Data<Client>
) -> Result<HttpResponse, Error> {
    let uri = format!("http://{}{}/model/descrivizio-001", req.uri().host().unwrap(), req.uri().path());
    let image_url = req.headers().get("Image-Url").unwrap().to_str().unwrap();

    let response = client.post(uri)
        .header("Content-Type", "image/*")
        .body(get_image_blob(image_url).await.unwrap())
        .send()
        .await?;

    let mut result = HttpResponse::build(response.status());
    for (header_name, header_value) in response.headers() {
        result.header(header_name.clone(), header_value.clone());
    }

    let bytes = response.body().await?;
    Ok(result.body(bytes))
}

/// Send a GET request to download user images
#[get("/nakira974/model/image/download")]
async fn get_user_image(
    req: HttpRequest,
    client: web::Data<Client>
) -> Result<HttpResponse, Error> {
    let uri = format!("http://{}{}", req.uri().host().unwrap(), req.uri().path());
    let image_url = req.headers().get("Image-Url").unwrap().to_str().unwrap();

    let response = client.get(image_url)
        .send()
        .await?;

    let mut result = HttpResponse::build(response.status());
    for (header_name, header_value) in response.headers() {
        result.header(header_name.clone(), header_value.clone());
    }

    let mut response_bytes = vec![];
    let mut stream = response.bytes_stream();
    while let Some(Ok(chunk)) = stream.next().await {
        response_bytes.extend_from_slice(&chunk);
    }
    let bytes = Bytes::from(response_bytes);

    Ok(result.body(bytes))
}

async fn get_image_blob(image_url: &str) -> Result<Vec<u8>, HttpClientError> {
    let mut response: ClientResponse = Client::default().get(image_url)
        .send()
        .await?;

    let mut blob = vec![];
    while let Some(item) = response.body_mut().next().await {
        let bytes = item?;
        blob.extend(bytes);
    }
    Ok(blob)
}

#[actix_rt::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        let client = Client::new();

        App::new()
            .data(client)
            .service(descrivizio_analyze)
            .service(descrivizio_analyze_from_header)
            .service(get_user_image)})
        .bind(("127.0.0.1", 7777))?
        .run()
        .await
}