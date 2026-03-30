import os
import numpy as np
import tensorflow as tf

def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

def bake_1st_edition(base_dir, output_file, limit_per_class=100):
    print(f"🚀 Starting Authentic 1st Ed Bake into {output_file}...")
    writer = tf.io.TFRecordWriter(output_file)
    total_baked = 0

    # The 1st Ed structure: .../data/by_class/[hex_folder]/
    by_class_path = os.path.join(base_dir, "data/by_class")
    
    for hex_folder in sorted(os.listdir(by_class_path)):
        class_path = os.path.join(by_class_path, hex_folder)
        if not os.path.isdir(class_path): continue
        
        label = int(hex_folder, 16)
        class_count = 0
        
        # Find all .mit files in this class folder
        mit_files = [f for f in os.listdir(class_path) if f.endswith('.mit')]
        
        for mit_file in mit_files:
            prefix = mit_file.replace('.mit', '')
            mis_file = os.path.join(class_path, prefix + ".mis")
            
            if not os.path.exists(mis_path := mis_file): continue
            
            # Extract 128x128 chunks (NIST 1st Ed Standard)
            with open(mis_path, 'rb') as f_mis:
                while class_count < limit_per_class:
                    chunk = f_mis.read(2048) # 128*128 / 8
                    if len(chunk) < 2048: break
                    
                    # Create TF Example
                    example = tf.train.Example(features=tf.train.Features(feature={
                        'image': _bytes_feature(chunk),
                        'label': _int64_feature(label)
                    }))
                    writer.write(example.SerializeToString())
                    class_count += 1
                    total_baked += 1

        print(f"✅ Baked {class_count} samples for class {hex_folder} (ASCII: {chr(label)})")

    writer.close()
    print(f"✨ Final Success! Baked {total_baked} total samples.")

if __name__ == "__main__":
    base = "/home/edwin/projects/feedback_analyzer/data/nist_sd19/1stEdition1995"
    out = "/home/edwin/projects/feedback_analyzer/data/tfrecords/nist_authentic.tfrecord"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bake_1st_edition(base, out)