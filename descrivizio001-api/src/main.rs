use actix_web::{App, HttpServer};
use actix_web::middleware::Logger;
use reqwest::{Client, ClientBuilder};
use std::time::Duration;

use crate::controllers::model_processing::{descrivizio_analyze, descrivizio_analyze_from_header, get_user_image};
use crate::models::model_processing::ApplicationImage;
use crate::services::logging_service::init_logging;

mod models;
mod controllers;
mod services;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    init_logging();
    HttpServer::new(|| {
        let client = ClientBuilder::new()
            .connect_timeout(Duration::from_secs(10))
            .timeout(Duration::from_secs(30))
            .danger_accept_invalid_certs(true)
            .build()
            .unwrap();

        App::new()
            .data(client)
            .wrap(Logger::new("%a %{User-Agent}i %r %s %b \"%{Referer}i\" \"%{User-Agent}i\"\" %T"))
            .service(descrivizio_analyze)
            .service(descrivizio_analyze_from_header)
            .service(get_user_image)
    })
        .bind(("0.0.0.0", 8085))
        .expect("Unable to bind to port 8085")
        .run()
        .await
}
