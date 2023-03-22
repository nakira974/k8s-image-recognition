import pandas as pd
import glob
from PIL import Image
from google.auth.transport import requests

from tensorflow.lite.python.conversion_metadata_schema_py_generated import np

import tensorflow as tf
from keras.applications.inception_v3 import preprocess_input
from keras import Model
from keras.layers import Input, Flatten, Dense, Dropout, LSTM, RepeatVector, TimeDistributed
from huggingface_hub import login
from transformers import AutoTokenizer, AutoModel, AutoConfig


def create_text_generation_model():
    embedding_dim = 128
    num_decoder_tokens = 28
    latent_dim = 256

    # Define the input layer for the decoder
    input_decoder_layer = Input(shape=(None, num_decoder_tokens))

    # Define the LSTM decoder
    decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True)
    decoder_outputs, _, _ = decoder_lstm(input_decoder_layer)

    # Add a dense layer
    decoder_dense = Dense(num_decoder_tokens, activation='softmax')
    decoder_outputs = decoder_dense(decoder_outputs)

    # Define the output layer for the decoder
    output_decoder_layer = decoder_outputs

    # Create the model
    result_text_generation_model = Model(inputs=[input_decoder_layer], outputs=[output_decoder_layer])

    return result_text_generation_model


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

    # Define the model and tokenizer
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


def prepare_data_for_text_generation(embedding_matrix, dataframe):
    photo_ids = dataframe.photo_id
    descriptions = []
    for i in range(len(photo_ids)):
        description = "<start> " + dataframe.iloc[i]['description'] + " <end>"
        descriptions.append(description)

    # Tokenize the textual descriptions
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    sequences = tokenizer(descriptions, padding='max_length', truncation=True, max_length=64, return_tensors='tf')

    # Create input and output sequences for training
    encoder_input_data = embedding_matrix
    decoder_input_data = sequences.input_ids
    decoder_output_data = sequences.attention_mask

    return encoder_input_data, decoder_input_data, decoder_output_data


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

text_generation_model = create_text_generation_model()
encoder_input_data, decoder_input_data, decoder_target_data = prepare_data_for_text_generation(embeddings,
                                                                                               datasets['photos'])
text_generation_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

text_generation_model.fit([decoder_input_data], [decoder_target_data], epochs=10, batch_size=32)
output = text_generation_model.predict([encoder_input_data])

login(token="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")
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)
print(decoded_output)

text_generation_model.save('wickr-bot.keras')

print(end="END\n")
