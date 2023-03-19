use std::fs::File;
use std::io::Read;
use image::{GenericImageView, ImageBuffer, Luma, RgbImage};
use tensorflow::{Graph, ImportGraphDefOptions, Operation, Session, SessionOptions, Tensor};

///  Preprocess the dataset:
/// Use the `image` crate to preprocess the images.
/// Resize all the images to a fixed size and convert them to grayscale.
fn preprocess_image(image_path: &str, size: (u32, u32)) -> Option<Vec<f32>> {
    let img = image::open(image_path).ok()?.resize_exact(size.0, size.1, image::imageops::FilterType::Nearest);
    let img = img.to_luma8();
    let img = ImageBuffer::from_fn(size.0, size.1, |x, y| Luma([img.get_pixel(x, y)[0]]));
    Some(img.to_vec().iter().map(|x| *x as f32 / 255.).collect())
}



fn main() {
    let images = vec!["image1.jpg", "image2.jpg", "image3.jpg"];
    let graph = {
        let mut graph = tensorflow::Graph::new();
        let mut proto = Vec::new();
        File::open("model/inception_v3_2016_08_28_frozen.pb")?
            .read_to_end(&mut proto)?;

        graph.import_graph_def(&*proto, {&ImportGraphDefOptions})?;
        graph
    };
    let session = tensorflow::Session::new(&tensorflow::SessionOptions::new(), &graph)?;
    let input_operation = graph.operation_by_name_required("input")?;
    let output_operation = graph.operation_by_name_required("InceptionV3/Predictions/Reshape_1")?;

    let entries = images.iter().map(|i| Node::from(preprocess_image(i, (299, 299)).unwrap())).collect::<Vec<_>>();
    let input_tensor = Tensor::from(entries.as_slice());

    let results = session.run(&mut [(input_operation, input_tensor), &[output_operation]])?;
    let embeddings_tensor = results[0].clone();
    let embeddings = embeddings_tensor.into::<Vec<f32>>();

}