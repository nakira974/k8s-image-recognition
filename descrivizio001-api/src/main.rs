use actix_web::{get, patch, post, web, App, Error, HttpResponse, HttpServer};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use actix_web::HttpRequest;

#[derive(Debug, Serialize, Deserialize)]
pub struct ApplicationPhoto {
    // fields for application photo
}

#[post("/nakira974/model/descrivizio-001/process")]
async fn descrivizio_analyze(
    app_photo: web::Json<ApplicationPhoto>,
    client: web::Data<Client>,
) -> Result<HttpResponse, Error> {
    let uri = format!("http://{}{}", "localhost:8000", "/model/descrivizio-001");

    let response = client
        .post(&uri)
        .header("Content-Type", "application/json")
        .json(&app_photo)
        .send()
        .await?;

    let body = response.bytes().await?;
    let mut result_builder = HttpResponse::build(response.status());
    for (name, value) in response.headers() {
        result_builder.header(name, value.to_str()?);
    }

    Ok(result_builder.body(body))
}

#[patch("/nakira974/model/descrivizio-001/process")]
async fn descrivizio_analyze_from_header(
    client: web::Data<Client>,
    req: HttpRequest,
) -> Result<HttpResponse, Error> {
    let uri = format!("http://{}{}", "localhost:8000", "/model/descrivizio-001");
    let image_url = req
        .headers()
        .get("Image-Url")
        .ok_or_else(|| HttpResponse::BadRequest().finish())?
        .to_str()
        .map_err(|_| HttpResponse::BadRequest().finish())?;

    let image_bytes = client.get(image_url).send().await?.bytes().await?;

    let response = client
        .post(&uri)
        .header("Content-Type", "image/*")
        .body(image_bytes)
        .send()
        .await?;

    let body = response.bytes().await?;
    let mut result_builder = HttpResponse::build(response.status());
    for (name, value) in response.headers() {
        result_builder.header(name, value.to_str()?);
    }

    Ok(result_builder.body(body))
}

#[get("/nakira974/model/image/download")]
async fn get_user_image(
    client: web::Data<Client>,
    req: HttpRequest,
) -> Result<HttpResponse, Error> {
    let image_url = req
        .headers()
        .get("Image-Url")
        .ok_or_else(|| HttpResponse::BadRequest().finish())?
        .to_str()
        .map_err(|_| HttpResponse::BadRequest().finish())?;

    let image_bytes = client.get(image_url).send().await?.bytes().await?;

    let mut result_builder = HttpResponse::Ok();
    result_builder.body(image_bytes)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        let client = Client::new();

        App::new()
            .data(client)
            .service(descrivizio_analyze)
            .service(descrivizio_analyze_from_header)
            .service(get_user_image)
    })
        .bind(("127.0.0.1", 7777))?
        .run()
        .await
}