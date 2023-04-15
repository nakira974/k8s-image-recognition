pub mod model_processing {
    use std::collections::HashMap;
    use std::io::Write;
    use std::time::{Duration, Instant};

    use actix_web::{App, Error, get, HttpResponse, HttpResponseBuilder, HttpServer, patch, post, web};
    use actix_web::{dev::ServiceRequest, middleware::Logger};
    use actix_web::HttpRequest;
    use actix_web::web::BufMut;
    use env_logger::fmt::{Color, Formatter};
    use log::{info, LevelFilter};
    use reqwest::Client;

    use crate::models::model_processing::ApplicationImage;

    #[post("/nakira974/model/descrivizio-001/process")]
    pub async fn descrivizio_analyze(
        app_photo: web::Json<ApplicationImage>,
        client: web::Data<Client>,
    ) -> Result<HttpResponse, Error> {
        let uri = format!("http://{}{}", "localhost:7777", "/model/descrivizio-001");

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
                return Err(error.into());
            }
        };

        let status_code = response.status();
        let headers = response.headers().clone();
        let bytes = response.bytes().await.map_err(|err| actix_web::error::ErrorBadRequest(err))?;

        let mut result_builder = HttpResponse::build(status_code);
        for (name, value) in headers {
            result_builder.header(name.unwrap(), value.to_str().unwrap_or_default());
        }

        Ok(result_builder.body(bytes))
    }

    #[patch("/nakira974/model/descrivizio-001/process")]
    pub async fn descrivizio_analyze_from_header(
        client: web::Data<Client>,
        req: HttpRequest,
    ) -> Result<HttpResponse, Error> {
        let uri = format!("http://{}{}", "localhost:7777", "/model/descrivizio-001");

        // Extract image_url from request headers
        let image_url = match req.headers()
            .get("Image-Url")
            .map(|value| value.to_str().ok())
            .flatten() {
            Some(url) => url.to_owned(),
            None => return Err(actix_web::error::ErrorBadRequest("Invalid header value").into()),
        };

        // Get image bytes
        let mut image_bytes_response = client.get(&image_url).send().await.map_err(|err| actix_web::error::ErrorBadRequest(err.to_string()))?;
        let mut image_bytes = Vec::new();
        while let Some(chunk) = image_bytes_response.chunk().await.map_err(|err| actix_web::error::ErrorInternalServerError(err))? {
            image_bytes.extend_from_slice(&chunk);
        }

        // Send POST request to remote server with binary payload
        let response = client.post(&uri)
            .header("Content-Type", "image/*")
            .body(image_bytes)
            .send()
            .await.map_err(|err| actix_web::error::ErrorBadRequest(err.to_string()))?;

        // Read response body into memory as bytes
        let status = response.status();
        let resp_body = response.bytes().await.map_err(|err| actix_web::error::ErrorBadRequest(err))?;
        let mut http_resp_builder = HttpResponseBuilder::new(status);

        Ok(http_resp_builder.body(resp_body))
    }

    #[get("/nakira974/model/image/download")]
    pub async fn get_user_image(
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

        let response = client.get(image_url).send().await.map_err(|err| actix_web::error::ErrorBadRequest(err.to_string()))?;
        let headers = response.headers().clone();

        let body = match response.bytes().await {
            Ok(bytes) => bytes,
            Err(err) => return Err(actix_web::error::ErrorBadRequest(err).into()),
        };

        let mut result_builder = HttpResponse::Ok();
        for (name, value) in headers.iter() {
            result_builder.header(name.clone(), value.to_str().unwrap_or_default());
        }

        Ok(result_builder.body(body))
    }
}