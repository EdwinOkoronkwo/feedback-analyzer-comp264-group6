import os
import tensorflow as tf
from PIL import Image
import numpy as np

import os
import tensorflow as tf

def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

def process_nist_to_tfrecord(source_dir, output_path, limit=1000):
    """
    Recursively crawls the NIST by_class tree:
    by_class/ -> [hex_folders] -> [train_folders] -> [images].png
    """
    count = 0
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with tf.io.TFRecordWriter(output_path) as writer:
        # os.walk is key here - it visits every single subfolder
        for root, dirs, files in os.walk(source_dir):
            for filename in files:
                if filename.lower().endswith('.png'):
                    if count >= limit:
                        break
                    
                    filepath = os.path.join(root, filename)
                    
                    # Extract label from the parent folder (e.g., '4a' for 'J')
                    # We look for the part of the path that is the 2-char hex code
                    path_parts = root.split(os.sep)
                    label_hex = "00"
                    for part in path_parts:
                        if len(part) == 2 and all(c in '0123456789abcdef' for c in part.lower()):
                            label_hex = part
                            break
                    
                    label = int(label_hex, 16)

                    with open(filepath, 'rb') as f:
                        image_bytes = f.read()

                    feature = {
                        'image': _bytes_feature(image_bytes),
                        'label': _int64_feature(label),
                        'filename': _bytes_feature(filename.encode('utf-8'))
                    }
                    
                    example = tf.train.Example(features=tf.train.Features(feature=feature))
                    writer.write(example.SerializeToString())
                    count += 1

            if count >= limit:
                break

    return count