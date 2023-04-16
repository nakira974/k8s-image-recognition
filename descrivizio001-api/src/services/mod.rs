pub mod logging_service {
    use std::collections::HashMap;
    use std::io::Write;

    use actix_rt::time::Instant;
    use actix_web::{dev::ServiceRequest, middleware::Logger};
    use env_logger::fmt::{Color, Formatter};
    use log::LevelFilter;

    fn format_log_message(
        formatter: &mut env_logger::fmt::Formatter,
        info: &ServiceRequest,
        start_time: &Instant,
    ) -> Result<(), std::io::Error> {
        let duration = start_time.elapsed().as_micros();

        let mut headers_map = HashMap::new();
        for (name, value) in info.headers() {
            headers_map.insert(
                name.as_str().to_owned(),
                value.to_str().unwrap_or_default().to_owned(),
            );
        }

        let uri_str = info.uri().to_string(); // Convert Uri to string
        let log_message = serde_json::json!({
           "request": {
               "method": info.method().as_str(),
               "uri": uri_str, // Use string version of Uri
               "headers": headers_map,
               "content_type": info.headers().get("Content-Type").map(|value| value.to_str().unwrap_or_default().to_owned()),
           },
           "response": {
               "http_version": format!("{:?}", info.version()),
               "headers": headers_map,
               // Response body is not logged in the example
           },
           "duration": duration,
        });

        // Write the log message using write_fmt instead of writeln
        formatter.write_fmt(format_args!("{}\n", log_message))?;

        Ok(())
    }

    pub fn init_logging() {
        let mut builder = env_logger::Builder::new();
        builder.filter(None, LevelFilter::Info);
        builder
            .format(|buf, record| {
                writeln!(
                    buf,
                    "{} [{}] - {}",
                    chrono::Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ"),
                    record.level(),
                    record.args()
                )
            })
            .filter(None, LevelFilter::Info);
        builder.init();
    }
}
