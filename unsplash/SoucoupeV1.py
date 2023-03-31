import json
import os
from typing import Union, Tuple

from tensorflow.lite.python.conversion_metadata_schema_py_generated import np
import pandas as pd
import glob
from PIL import Image
import tensorflow as tf
from keras.applications.inception_v3 import preprocess_input
from keras import Model
from keras.layers import Input, Flatten, Dense, Dropout, LSTM, TimeDistributed, Embedding
from huggingface_hub import login
from torch import nn
from torch._inductor.codecache import cache_dir
from transformers import PreTrainedModel, BertTokenizer, AutoConfig, BertConfig
import matplotlib
class Soucoupe(PreTrainedModel):
    def prepare_inputs_for_generation(self, input_ids, **kwargs):
        # Get the photo embeddings from the input_ids
        photo_embeddings = input_ids[:, :128]

        # Set the max length of the decoder input
        kwargs["max_length"] = 64

        # Return the photo embeddings as input and the rest of the kwargs as is
        return {"image_embeddings": photo_embeddings}, kwargs

    def _reorder_cache(self, past_key_values, beam_idx):
        pass

    def resize_position_embeddings(self, new_num_position_embeddings: int):
        pass

    def get_position_embeddings(self) -> Union[nn.Embedding, Tuple[nn.Embedding]]:
        pass

    def __init__(self, saved_model, tokenizer, *inputs, **kwargs):
        super(Soucoupe, self).__init__(*inputs, **kwargs)

        self.saved_model = saved_model
        self.tokenizer = tokenizer

    def generate_description(self, image_embeddings):
        # Get the output from the SavedModel
        output = self.saved_model(image_embeddings)

        # Convert the output to a description string
        decoded_output = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return decoded_output

    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path, dtype=tf.float32, *model_args, **kwargs):
        if pretrained_model_name_or_path == "local":
            main()
            saved_model = tf.saved_model.load("Aloblock/descrivizio")
            tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
            return cls(saved_model, tokenizer)

        config = AutoConfig.from_pretrained(pretrained_model_name_or_path, *model_args, cache_dir=cache_dir,
                                            **kwargs)
        config.dtype = dtype

    def forward(self, image_embeddings):
        return self.generate_description(image_embeddings)

    @staticmethod
    def prepare_data_for_text_generation(embedding_matrix, dataframe):
        photo_ids = dataframe.photo_id
        descriptions = []
        for i in range(len(photo_ids)):
            description = "<start> " + str(dataframe.iloc[i]['photo_description']) + " <end>"
            descriptions.append(description)

        # Tokenize the textual descriptions
        max_seq_length = 128
        google_bert_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        sequences = google_bert_tokenizer(descriptions, padding='max_length',
                                          truncation=True,
                                          max_length=max_seq_length,
                                          return_tensors='tf')

        # Create input and output sequences for training
        encoder_input_matrix = embedding_matrix
        decoder_input_data = sequences.input_ids[:, :-1]
        decoder_output_data = Soucoupe.to_one_hot(sequences.input_ids[:, 1:], num_classes=28)

        # Convert decoder_input_data to a Numpy array to avoid 'tuple' object error
        decoder_input_data = np.array(decoder_input_data)

        return encoder_input_matrix, decoder_input_data, decoder_output_data, google_bert_tokenizer

    @staticmethod
    def create_embeddings(dataset, p_embedding_model):
        photo_ids = dataset['colors']['photo_id']
        color_hex_codes = dataset['colors']['hex']
        batch_size = 128
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

    @staticmethod
    def create_embedding_model():
        input_shape = (299, 299, 3)
        embedding_dim = 128

        # Define the input layer
        input_layer = Input(shape=input_shape)

        # Add the pre-trained Inception v3 model
        base_model = tf.keras.applications.InceptionV3(
            include_top=False,
            weights='imagenet',
            input_tensor=input_layer
        )

        # Set all layers in the base model to non-trainable
        for layer in base_model.layers:
            layer.trainable = False

        # Flatten the output from the pre-trained model
        x = Flatten()(base_model.output)

        # Add a dense layer with dropout
        x = Dense(512, activation='relu')(x)
        x = Dropout(0.5)(x)

        # Add another dense layer with dropout
        x = Dense(embedding_dim, activation='relu')(x)
        x = Dropout(0.5)(x)

        # Add an output layer to produce the embeddings
        output_layer = Dense(embedding_dim)(x)

        # Create the model
        model = Model(inputs=[input_layer], outputs=[output_layer])

        return model

    @staticmethod
    def create_text_generation_model(vocab_size):
        embedding_dim = 128
        num_decoder_tokens = 28
        latent_dim = 256

        # Define the input layer for the decoder
        input_decoder_layer = Input(shape=(None,))

        # Add a masking layer to mask out any inputs with value -1
        masking_layer = tf.keras.layers.Masking(mask_value=-1)
        embedded_layer = Embedding(input_dim=vocab_size, output_dim=embedding_dim)
        embedded_output = embedded_layer(input_decoder_layer)
        embedded_output = masking_layer(embedded_output)

        # Define the LSTM decoder
        decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True)
        decoder_outputs, _, _ = decoder_lstm(embedded_output)

        # Add a dense layer
        decoder_dense = Dense(num_decoder_tokens, activation='softmax')
        decoder_outputs = decoder_dense(decoder_outputs)

        # Add a TimeDistributed layer to apply the dense layer to each time step
        # ensure that the output shape of the model matches the expected shape of the target data
        time_distributed_layer = TimeDistributed(Dense(num_decoder_tokens, activation='softmax'))
        decoder_outputs = time_distributed_layer(decoder_outputs)

        # Define the output layer for the decoder
        output_decoder_layer = decoder_outputs

        # Create the model
        result_text_generation_model = Model(inputs=[input_decoder_layer], outputs=[output_decoder_layer])

        return result_text_generation_model

    @staticmethod
    def to_one_hot(data, num_classes):
        # Truncate values less than 0 or greater than num_classes-2
        data = np.clip(data, 0, num_classes - 2)

        # Create an empty one-hot array with shape (batch_size, timesteps, num_classes)
        batch_size, timesteps = data.shape
        result = np.zeros((batch_size, timesteps, num_classes))

        # Convert data to one-hot encoding
        for i in range(batch_size):
            for j in range(timesteps):
                result[i, j, data[i, j]] = 1

        return result

    def prepare_inputs_for_generation(self, input_ids, **kwargs):
        # Get the photo embeddings from the input_ids
        photo_embeddings = input_ids[:, :128]

        # Add an additional "batch" dimension to the photo embeddings tensor
        photo_embeddings = tf.expand_dims(photo_embeddings, axis=0)

        # Set the max length of the decoder input
        kwargs["max_length"] = 64

        # Return the photo embeddings as input and the rest of the kwargs as is
        return {"image_embeddings": photo_embeddings}, kwargs

    def generate_description(self, image_embeddings):
        # Get the output from the SavedModel
        output = self.saved_model(image_embeddings)

        # Convert the output to a description string
        decoded_output = self.tokenizer.decode(tf.squeeze(output).numpy().tolist(),
                                               skip_special_tokens=True)
        return decoded_output


def main():
    path = './unsplash_datasets/'
    documents = ['photos', 'colors']
    datasets = {}

    for doc in documents:
        files = glob.glob(path + doc + ".tsv*")

        subsets = []
        for filename in files:
            df = pd.read_csv(filename, sep='\t', header=0)
            subsets.append(df)

        datasets[doc] = pd.concat(subsets, axis=0, ignore_index=True)

    print(datasets)
    embedding_model = Soucoupe.create_embedding_model()
    embeddings = Soucoupe.create_embeddings(datasets, embedding_model)
    print(embeddings)
    encoder_input_data, \
        decoder_input_data, \
        decoder_target_data, tokenizer = Soucoupe.prepare_data_for_text_generation(embeddings,
                                                                        datasets['photos'])
    decoder_input_data[decoder_input_data < 0] = 0

    text_generation_model = Soucoupe.create_text_generation_model(decoder_input_data.max())

    text_generation_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    # Train the model using decoder_input_one_hot
    print('Decoder input data min:', decoder_input_data.min())
    print('Decoder input data max:', decoder_input_data.max())
    print('Decoder target data min:', decoder_target_data.min())
    print('Decoder target data max:', decoder_target_data.max())
    decoder_input_data = np.clip(decoder_input_data, 0, text_generation_model.layers[1].input_dim - 2)
    history = text_generation_model.fit(decoder_input_data, decoder_target_data, epochs=6, batch_size=128)

    history_frame = pd.DataFrame(history.history)
    history_frame.loc[:, ['loss', 'loss']].plot()
    history_frame.loc[:, ['accuracy', 'accuracy']].plot()
    encoder_input_data = np.array(embeddings)
    encoder_input_data[encoder_input_data < 0] = 0
    print(encoder_input_data.shape)

    output = text_generation_model.predict(encoder_input_data, verbose=True)
    print(output.shape)
    # My decoder =(
    char_set = "abcdefghijklmnopqrstuvwxyz0123456789-,;.!?:'\"/\\|_@#$%^&*~`+-=<>()[]{} "
    # Create a lookup table to map one-hot encoded indices to characters
    idx_to_char = {i: c for i, c in enumerate(char_set)}
    # Find the index of the maximum value in each row of the output array
    decoded_indices = np.argmax(output, axis=2)
    # Map the indices back to their corresponding characters using the lookup table
    decoded_strings = []
    for indices in decoded_indices:
        decoded_string = ""
        for index in indices:
            if index == 0:
                break
            decoded_string += idx_to_char[index]
        decoded_strings.append(decoded_string)
    print(decoded_strings)

    tf.keras.models.save_model(text_generation_model, 'Aloblock/descrivizio')


if __name__ == '__main__':
    main()