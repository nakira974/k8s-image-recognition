use image::imageops::FilterType;
use image::load;
use rust_bert::Config;
use tch::nn::Linear;
use tensorflow::Tensor;
use rust_bert::gpt2::{Gpt2Config, GPT2Generator, Gpt2Model};
use rust_bert::pipelines::common::ModelType;
use rust_bert::pipelines::generation_utils::{GenerateConfig, LanguageGenerator};
use std::path::Path;
use tch::{nn, Device};

fn main() {
    use image::{self, GenericImageView};
    use tch::{Tensor, nn::{Module, Conv2D}};

// Load pre-trained ResNet50 model
    let mut resnet = tch::CModule::load("resnet50.pt").unwrap();
    resnet.set_eval();

// Load image and preprocess it
    let img = image::open("rsc/IMG_20220604_132820.jpg").unwrap();
    let resized_img = img.resize_exact(224, 224, FilterType::Nearest);
    let tensor_img = Tensor::of_slice(resized_img.to_bytes().as_slice())
        .view([1, 3, 224, 224])
        .to_kind(tch::Kind::Float);

// Calculate features using ResNet50 model
    let features = resnet.forward_ts(&[&tensor_img]);

// Perform adaptive average pooling
    let embedding_size = 2048;
    let pooled_features = features.unwrap().get(0)
        .adaptive_avg_pool2d(&[1, 1])
        .view([-1, embedding_size]);


    // Load GPT-2 configuration from checkpoint file
    let config = Gpt2Config::from_file("gpt2_config.json");

    // Declare a generation configuration
    let generate_config = GenerateConfig {
        max_length: 20,
        do_sample: true,
        top_k: 50,
        temperature: 0.7,
        ..Default::default()
    };


    let config_path = Path::new("path/to/config.json");
    let device = Device::Cpu;
    let p = nn::VarStore::new(device);
    let config = Gpt2Config::from_file(config_path);
    let model: Gpt2Model = Gpt2Model::new(&p.root() / "gpt2", &config);

    // Instantiate GPT2 generator
    let mut generator = GPT2Generator::new(generate_config);

    // Generate text from embeddings using GPT2 generator
    let prompt = LanguageGenerator::generate_prompt_from_embeddings(&[&pooled_features], None);
    let output = generator.generate(Some(vec![&prompt]), generate_config)?;
    for generated_text in output {
        println!("Description: {}", generated_text.text);
    }
}
