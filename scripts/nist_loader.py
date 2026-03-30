import tensorflow as tf
import numpy as np

def parse_fn(example_proto):
    feature_description = {
        'image': tf.io.FixedLenFeature([], tf.string),
        'label': tf.io.FixedLenFeature([], tf.int64),
    }
    features = tf.io.parse_single_example(example_proto, feature_description)
    image_raw = tf.io.decode_raw(features['image'], tf.uint8)

    # 1. Unpack all 16384 bits into a flat 1D array first
    shift_amounts = tf.cast(tf.range(8), tf.uint8)
    bits = tf.bitwise.right_shift(tf.expand_dims(image_raw, 1), shift_amounts)
    bits = tf.math.mod(bits, 2)
    flat_bits = tf.reshape(bits, [-1]) # [16384]

    # 2. Reshape as Column-Major (Fortran-style)
    # If standard [128, 128] looks like noise, we 'Transpose' the logic
    image = tf.reshape(flat_bits, [128, 128])
    image = tf.transpose(image) 
    
    # 3. Invert if needed (NIST is often 1=Black, 0=White)
    # If the image is 'Ghostly', remove the subtraction
    image = 1.0 - tf.cast(image, tf.float32)
    
    return image, features['label']

def get_nist_dataset(tfrecord_path, batch_size=32):
    dataset = tf.data.TFRecordDataset(tfrecord_path)
    dataset = dataset.map(parse_fn)
    dataset = dataset.shuffle(1000).batch(batch_size)
    return dataset

if __name__ == "__main__":
    # Quick Test: Let's pull one batch and check shapes
    path = "/home/edwin/projects/feedback_analyzer/data/tfrecords/nist_authentic.tfrecord"
    ds = get_nist_dataset(path)
    
    for images, labels in ds.take(1):
        print(f"✅ Batch Shape: {images.shape}")
        print(f"✅ Label Sample: {labels[0].numpy()} (ASCII: {chr(labels[0].numpy())})")