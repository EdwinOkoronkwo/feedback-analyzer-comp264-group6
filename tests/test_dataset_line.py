import os
from implementations.local.bridge.local_bridge import LocalPipelineBridge

def test_mnist_bridge():
    print("🚀 Testing Local Bridge (MNIST Baseline)...")
    local_bridge = LocalPipelineBridge(project_root=".")
    
    # REMOVE the "./data/nist" source. MNIST doesn't need it.
    payload = {
        "limit": 10,
        "dataset_type": "mnist" 
    }
    
    res = local_bridge.trigger_dataset_ingestion(payload)
    
    if res['status'] == 'error':
        print(f"❌ TEST FAILED: {res['message']}")
    else:
        print(f"✅ TEST PASSED: {res}")

if __name__ == "__main__":
    test_mnist_bridge()