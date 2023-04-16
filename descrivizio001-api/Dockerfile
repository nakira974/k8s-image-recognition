FROM rust:1.68.2-slim-bullseye AS builder
WORKDIR /code

# Install openssl and pkg-config dependencies
RUN apt-get update && \
    apt-get -y install libssl-dev pkg-config curl ca-certificates&& \
    rm -rf /var/lib/apt/lists/* \

# Install Rust and Cargo
RUN curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain stable -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Download crates-io index and fetch dependency code.
# This step avoids needing to spend time on every build downloading the index
# which can take a long time within the docker context. Docker will cache it.
RUN USER=root cargo init
COPY Cargo.toml Cargo.toml
RUN cargo fetch

# copy app files
COPY src src

# compile app
RUN cargo build --release

###############
## run stage ##
###############
FROM debian:bullseye-slim
WORKDIR /app

# Copy SSL libraries from builder stage image.
COPY --from=builder /usr/lib/x86_64-linux-gnu/libssl.so* /usr/lib/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libcrypto.so* /usr/lib/
# Copy Rust and Cargo binaries from builder stage image.
COPY --from=builder /usr/local/cargo/bin/cargo /usr/local/cargo/bin/cargo
# copy server binary from build stage
COPY --from=builder /code/target/release/descrivizio001-api descrivizio001-api

# indicate what port the server is running on
EXPOSE 8085

# run server
CMD [ "/app/descrivizio001-api" ]