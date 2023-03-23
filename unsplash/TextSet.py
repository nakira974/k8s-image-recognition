import numpy
import tensorflow as tf
from tensorflow._api.v2 import math


class TextDataset(tf.keras.utils.Sequence):
    def __init__(self, encoder_input_data, decoder_input_data, decoder_target_data, batch_size):
        self.encoder_input_data = encoder_input_data
        self.decoder_input_data = decoder_input_data
        self.decoder_target_data = decoder_target_data
        self.batch_size = int(float(batch_size))

    def __len__(self):
        return math.ceil(len(self.encoder_input_data) / self.batch_size)

    def __getitem__(self, idx):
        start_idx = idx * self.batch_size
        end_idx = min(start_idx + self.batch_size, len(self.encoder_input_data))

        # Reshape the decoder input data to have shape (batch_size, timesteps, 1)
        seq_length = self.decoder_input_data.shape[-1]
        # Convert decoder input data to integer data type
        decoder_input_data_int = self.decoder_input_data[start_idx:end_idx].astype(numpy.int32)

        return ([self.encoder_input_data[start_idx:end_idx]],
                decoder_input_data_int), \
            self.decoder_target_data[start_idx:end_idx]
