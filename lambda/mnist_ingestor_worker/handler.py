import json
import os
import boto3
import tensorflow as tf

# --- HELPERS (From your NIST logic, adapted for MNIST) ---

def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

def process_mnist_to_tfrecord(output_path, limit=1000):
    """Bakes MNIST from Keras into a TFRecord."""
    (x_train, y_train), _ = tf.keras.datasets.mnist.load_data()
    count = 0
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with tf.io.TFRecordWriter(output_path) as writer:
        for i in range(min(len(x_train), limit)):
            image_np = x_train[i]
            label = int(y_train[i])
            image_bytes = tf.io.encode_png(image_np[..., tf.newaxis]).numpy()
            filename = f"mnist_sample_{i}.png".encode('utf-8')

            feature = {
                'image': _bytes_feature(image_bytes),
                'label': _int64_feature(label),
                'filename': _bytes_feature(filename)
            }
            example = tf.train.Example(features=tf.train.Features(feature=feature))
            writer.write(example.SerializeToString())
            count += 1
    return count

# --- LAMBDA HANDLER ---

def lambda_handler(event, context):
    """
    MNIST Ingestor: Uses the local TF function to create the baseline.
    """
    # 🎯 Set local paths
    output_path = "/home/edwin/projects/feedback_analyzer/data/tfrecords/mnist_standard.tfrecord"
    limit = event.get('limit', 10) # Default to 10 for your test
    fid = "mnist_baseline_test"

    try:
        print(f"📦 MNIST Worker: Processing {limit} samples...")
        
        # 🚀 Execute the TF logic
        actual_count = process_mnist_to_tfrecord(output_path, limit=limit)

        print(f"✅ Created: {output_path} with {actual_count} samples.")

        return {
            "status": "success",
            "feedback_id": fid,
            "count": actual_count,
            "path": output_path
        }

    except Exception as e:
        print(f"❌ MNIST Worker Error: {str(e)}")
        return {"status": "error", "message": str(e)}