FROM rust:1.68.2-buster as builder

WORKDIR /app

# Copy source code to container
COPY . .

# Build the application
RUN cargo build --release

# Start a new stage and copy over the binary
FROM debian:stretch-slim

COPY --from=builder /app/target/release/descrivizio001-api /usr/local/bin/descrivizio001-api

# Expose port 8085
EXPOSE 8085

# Start the service
CMD ["descrivizio001-api"]