import tensorflow as tf

def bake_mnist_to_tfrecord(output_file):
    print(f"🚀 Baking MNIST into {output_file}...")
    
    # Load the standard MNIST from Keras
    (x_train, y_train), _ = tf.keras.datasets.mnist.load_data()
    
    with tf.io.TFRecordWriter(output_file) as writer:
        for i in range(len(x_train)):
            # MNIST is already pixels, so we just convert to bytes
            image_raw = x_train[i].tobytes()
            
            example = tf.train.Example(features=tf.train.Features(feature={
                'image': tf.train.Feature(bytes_list=tf.train.BytesList(value=[image_raw])),
                'label': tf.train.Feature(int64_list=tf.train.Int64List(value=[y_train[i]]))
            }))
            writer.write(example.SerializeToString())
            
            if i % 10000 == 0:
                print(f"✅ Baked {i} samples...")

    print(f"✨ Success! Baked {len(x_train)} MNIST samples.")

if __name__ == "__main__":
    out_path = "data/tfrecords/mnist_standard.tfrecord"
    bake_mnist_to_tfrecord(out_path)