import tensorflow as tf
import os

def parse_mnist_fn(example_proto):
    feature_description = {
        'image': tf.io.FixedLenFeature([], tf.string),
        'label': tf.io.FixedLenFeature([], tf.int64),
    }
    features = tf.io.parse_single_example(example_proto, feature_description)
    
    # 🕵️ SAFE DECODE STRATEGY
    # If decode_raw failed with 313, it's likely a compressed format (PNG/JPG)
    try:
        # Try decoding as an image (PNG/JPG) first
        image = tf.io.decode_image(features['image'], channels=1)
    except:
        # Fallback to raw bytes if it's not a standard image format
        image = tf.io.decode_raw(features['image'], tf.uint8)

    # Use a dynamic reshape or set shape to avoid the 313 vs 784 crash
    image = tf.cast(image, tf.float32) / 255.0
    image = tf.ensure_shape(image, [28, 28, 1]) 
    
    return image, features['label']

def get_mnist_dataset(tfrecord_path, batch_size=32, shuffle_buffer=10000):
    """
    Creates a high-performance data pipeline using tf.data.
    """
    if not os.path.exists(tfrecord_path):
        raise FileNotFoundError(f"Could not find TFRecord at {tfrecord_path}")

    dataset = tf.data.TFRecordDataset(tfrecord_path)
    
    # FIX: Removed 'parse_fn=' and passed it as a positional argument.
    # TensorFlow expects the function as the first argument (map_func).
    dataset = dataset.map(parse_mnist_fn, num_parallel_calls=tf.data.AUTOTUNE)
    
    dataset = dataset.shuffle(shuffle_buffer)
    dataset = dataset.batch(batch_size)
    dataset = dataset.prefetch(buffer_size=tf.data.AUTOTUNE)
    
    return dataset

if __name__ == "__main__":
    # Test the loader locally
    path = "data/tfrecords/mnist_standard.tfrecord"
    try:
        ds = get_mnist_dataset(path)
        for img_batch, label_batch in ds.take(1):
            print(f"✅ MNIST Loader Test Success!")
            print(f"📦 Batch Shape: {img_batch.shape}")  # Should be (32, 28, 28, 1)
            print(f"🏷️ Labels in Batch: {label_batch.numpy()[:5]}")
    except Exception as e:
        print(f"❌ Loader Test Failed: {e}")