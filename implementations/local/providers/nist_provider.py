import tensorflow as tf

from chalicelib.interfaces.dataset import IDatasetProvider


class NistDatasetUtility(IDatasetProvider):
    @staticmethod
    def get_tfrecord_dataset(record_path, batch_size=32):
        """
        Utility method to stream and parse a TFRecord.
        Returns a high-performance tf.data.Dataset object.
        """
        # Define how to decode the binary data we wrote in handler.py
        feature_description = {
            'image': tf.io.FixedLenFeature([], tf.string),
            'label': tf.io.FixedLenFeature([], tf.int64),
            'filename': tf.io.FixedLenFeature([], tf.string),
        }

        def _parse_function(example_proto):
            return tf.io.parse_single_example(example_proto, feature_description)

        # Build the pipeline
        dataset = tf.data.TFRecordDataset(record_path)
        dataset = dataset.map(_parse_function)
        return dataset.batch(batch_size)