from implementations.aws.bridge.aws_bridge import AWSPipelineBridge
from scripts.mnist_loader import get_mnist_dataset

def test_aws_mnist_batch():
    # 1. Load the local TFRecord we baked earlier
    local_path = "data/tfrecords/mnist_standard.tfrecord"
    dataset = get_mnist_dataset(local_path, batch_size=1)
    
    # 2. Trigger Bridge with the Iterator
    aws_bridge = AWSPipelineBridge(cloud_orchestrator=None)
    res = aws_bridge.trigger_dataset_ingestion({
        'limit': 5, 
        'dataset': dataset
    })
    
    print(f"✅ Batch Sync Complete: {res}")
if __name__ == "__main__":
    # test_mnist_bridge() # Comment out local
    test_aws_mnist_batch()