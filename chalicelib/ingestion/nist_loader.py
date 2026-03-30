# chalicelib/ingestion/nist_loader.py
import io
import time
import tensorflow as tf
from PIL import Image

from PIL import Image
import io
import time
import numpy as np

import tensorflow as tf
import numpy as np
from PIL import Image
import io
import time

def get_prepared_nist_batch(dataset, limit=1):
    """
    Standardizes NIST Authentic samples for the Hybrid Bridge.
    Handles extraction, image cleaning, and metadata mapping with detailed logging.
    """
    prepared_samples = []
    print(f"\n[LOADER] 🚀 Starting NIST extraction for {limit} samples...")
    
    # Iterate through the TF Dataset object
    for i, record in enumerate(dataset.take(limit)):
        try:
            print(f"[LOADER] 🔍 Processing record index: {i}...")

            # 1. Extraction: Handle Tensors vs. Eager execution objects
            image_raw = record['image'].numpy() if hasattr(record['image'], 'numpy') else record['image']
            label = int(record['label'].numpy()) if hasattr(record['label'], 'numpy') else int(record['label'])

            # 2. Cleaning: Robustness against TFRecord corruption or NaNs
            # nan_to_num prevents 'RuntimeWarning: invalid value encountered in cast'
            image_raw = np.nan_to_num(image_raw, nan=0.0, posinf=1.0, neginf=0.0)
            image_raw = np.clip(image_raw, 0.0, 1.0)

            # 3. Metadata: Safe string decoding
            raw_filename = record.get('filename', b'unknown_nist')
            if hasattr(raw_filename, 'numpy'):
                filename = raw_filename.numpy().decode('utf-8')
            else:
                filename = raw_filename.decode('utf-8') if isinstance(raw_filename, bytes) else str(raw_filename)

            # 4. Conversion: Squeeze 3D (H, W, 1) to 2D (H, W) for PIL
            if len(image_raw.shape) == 3:
                image_raw = np.squeeze(image_raw)
                
            # Scale to uint8 for PNG encoding
            final_image_array = (image_raw * 255).astype('uint8')
            img = Image.fromarray(final_image_array)
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            png_bytes = img_byte_arr.getvalue()
            
            # 5. Mapping: Standardized Cloud Schema
            # Using unique feedback IDs ensures no DynamoDB collisions
            sample_id = f"nist_auth_{int(time.time())}_{i}"
            
            prepared_samples.append({
                "feedback_id": sample_id,
                "label": label,
                "image_bytes": png_bytes,
                "metadata": {
                    "source_file": filename,
                    "dataset": "NIST_AUTHENTIC",
                    "resolution": f"{image_raw.shape[0]}x{image_raw.shape[1]}"
                }
            })
            print(f"[LOADER] ✅ Record {i} ready | ID: {sample_id} | Size: {len(png_bytes)} bytes")

        except Exception as e:
            print(f"[LOADER] ❌ Error processing record {i}: {str(e)}")
            continue
            
    print(f"[LOADER] 🏁 Finished. Prepared {len(prepared_samples)} total NIST samples.\n")
    return prepared_samples


def parse_nist_record(example_proto):
    feature_description = {
        'image': tf.io.FixedLenFeature([], tf.string),
        'label': tf.io.FixedLenFeature([], tf.int64),
    }
    parsed = tf.io.parse_single_example(example_proto, feature_description)
    
    # 1. Decode the 512-float buffer (2048 bytes)
    image_raw = tf.io.decode_raw(parsed['image'], out_type=tf.float32)
    
    # 2. Reshape to the actual native shape of that 512-buffer (e.g., 32x16)
    image_reshaped = tf.reshape(image_raw, [32, 16, 1])
    
    # 3. Use TF Data API to Resize to the Cloud standard (128x128)
    # This "fakes" the high-res shape so the Analysis Worker doesn't crash
    image_final = tf.image.resize(image_reshaped, [128, 128])
    
    parsed['image'] = tf.squeeze(image_final)
    return parsed