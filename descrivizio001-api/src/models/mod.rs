pub mod model_processing {
    use serde::{Deserialize, Serialize};

    #[derive(Debug, Serialize, Deserialize)]
    pub struct ApplicationImage {
        content: Vec<u8>,
    }

    impl ApplicationImage {
        pub fn new(content: Vec<u8>) -> Self {
            Self { content }
        }

        pub fn into_bytes(self) -> Vec<u8> {
            self.content
        }
    }
}

