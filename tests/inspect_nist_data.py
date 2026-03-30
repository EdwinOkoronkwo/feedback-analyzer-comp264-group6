import tensorflow as tf

def inspect_record(path):
    raw_dataset = tf.data.TFRecordDataset(path)
    for raw_record in raw_dataset.take(1):
        example = tf.train.Example()
        example.ParseFromString(raw_record.numpy())
        
        # This prints the keys and the length of the data lists
        for key, feature in example.features.feature.items():
            kind = feature.WhichOneof('kind')
            val = getattr(feature, kind).value
            print(f"Key: {key} | Type: {kind} | Length/Size: {len(val)}")

print("--- NIST RECORD ---")
inspect_record("data/tfrecords/nist_authentic.tfrecord")