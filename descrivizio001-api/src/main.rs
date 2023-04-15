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

    let response = match client
        .post(&uri)
        .header("Content-Type", "application/json")
        .json(&app_photo)
        .send()
        .await {
        Ok(res) => res,
        Err(e) => {
            let error_message = format!("Reqwest error: {}", e.to_string());
            let error = actix_web::error::ErrorBadRequest(error_message);
            return Err(error.into())
        }
    };

    let body = response
        .bytes()
        .await
        .map_err(|err| actix_web::error::ErrorBadRequest(err))?;
    let mut result_builder = HttpResponse::build(response.status());

    for (name, value) in response.headers() {
        result_builder.header(name, value.to_str().unwrap_or_default());
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
        .ok_or_else(|| actix_web::error::ErrorBadRequest("Image-Url header is missing"))?
        .to_str()
        .map_err(|_| actix_web::error::ErrorBadRequest("Invalid header value"))?;

    let image_bytes = client
        .get(image_url)
        .send()
        .await
        .map_err(|err| actix_web::error::ErrorBadRequest(err.to_string()))?
        .bytes()
        .await
        .map_err(|err| actix_web::error::ErrorBadRequest(err))?;

    let response = client
        .post(&uri)
        .header("Content-Type", "image/*")
        .body(image_bytes)
        .send()
        .await
        .map_err(|err| actix_web::error::ErrorBadRequest(err.to_string()))?;

    let body = response.bytes()
        .await
        .map_err(|err| actix_web::error::ErrorBadRequest(err))?;

    let mut result_builder = HttpResponse::build(response.status());
    for (name, value) in response.headers() {
        result_builder.header(name, value.to_str().unwrap_or_default());
    }

    Ok(result_builder.body(body))
}

#[get("/nakira974/model/image/download")]
async fn get_user_image(
    client: web::Data<Client>,
    req: HttpRequest,
) -> Result<HttpResponse, Error> {
    let image_url = match req.headers()
        .get("Image-Url")
        .ok_or_else(|| HttpResponse::BadRequest().finish())
    {
        Ok(header) => header.to_str().map_err(|_| {
            actix_web::error::ErrorBadRequest("Invalid header value")
        })?,
        Err(response) => {
            let error_message = format!("Invalid header value: {:?}", response);
            return Err(actix_web::error::ErrorBadRequest(error_message).into());
        }
    };

    let response = match client.get(image_url).send().await {
        Ok(res) => res,
        Err(e) => return Err(actix_web::error::ErrorBadRequest(format!("Reqwest error: {}", e.to_string())).into()),
    };

    let body = match response.bytes().await {
        Ok(bytes) => bytes,
        Err(err) => return Err(actix_web::error::ErrorBadRequest(err).into()),
    };

    let mut result_builder = HttpResponse::Ok();
    for (name, value) in response.headers() {
        result_builder.header(name, value.to_str().unwrap_or_default());
    }

    Ok(result_builder.body(body))
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