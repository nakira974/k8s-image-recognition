import pandas as pd
import glob
from PIL import Image

from tensorflow.lite.python.conversion_metadata_schema_py_generated import np

import tensorflow as tf
from keras.applications.inception_v3 import preprocess_input
from keras import Model
from keras.layers import Input, Flatten, Dense, Dropout


def create_embedding_model():
    input_shape = (299, 299, 3)
    embedding_dim = 128

    # Define the input layer
    input_layer = Input(shape=input_shape)

    # Add the pre-trained Inception v3 model
    base_model = tf.keras.applications.InceptionV3(
        include_top=False,
        weights='imagenet',
        input_shape=input_shape
    )
    x = base_model(input_layer)

    # Flatten the output from the pre-trained model
    x = Flatten()(x)

    # Add a dense layer with dropout
    x = Dense(512, activation='relu')(x)
    x = Dropout(0.5)(x)

    # Add another dense layer with dropout
    x = Dense(embedding_dim, activation='relu')(x)
    x = Dropout(0.5)(x)

    # Define the output layer
    output_layer = x

    # Create the model
    result_embedding_model = Model(inputs=[input_layer], outputs=[output_layer])

    return result_embedding_model


def create_embeddings(dataset, p_embedding_model):
    photo_ids = dataset['colors']['photo_id']
    color_hex_codes = dataset['colors']['hex']
    batch_size = 32
    result_embeddings = []


    for i in range(0, len(photo_ids), batch_size):
        # Load a batch of images
        batch_ids = photo_ids[i:i + batch_size]
        batch_hex_codes = color_hex_codes[i:i + batch_size]
        batch_images = []
        for hex_code in batch_hex_codes:
            # Convert hex code to RGB values
            r, g, b = tuple(int(hex_code[i:i + 2], 16) for i in (0, 2, 4))
            # Create an image with the given RGB values
            img = Image.new('RGB', (299, 299), (r, g, b))
            print("{} {} {}".format(r, g, b), end=" has been generated\n")
            batch_images.append(img)
        batch_images = np.array([preprocess_input(np.array(img)) for img in batch_images])

        # Extract embeddings for the batch of images
        batch_embeddings = p_embedding_model.predict(batch_images)
        result_embeddings.extend(batch_embeddings)

    return result_embeddings


path = './unsplash_datasets/'
documents = ['photos', 'keywords', 'collections', 'conversions', 'colors']
datasets = {}

for doc in documents:
    files = glob.glob(path + doc + ".tsv*")

    subsets = []
    for filename in files:
        df = pd.read_csv(filename, sep='\t', header=0)
        subsets.append(df)

    datasets[doc] = pd.concat(subsets, axis=0, ignore_index=True)

print(datasets)
embedding_model = create_embedding_model()
embeddings = create_embeddings(datasets, embedding_model)
print(embeddings)
