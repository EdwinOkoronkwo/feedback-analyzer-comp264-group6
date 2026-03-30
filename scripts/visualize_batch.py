import matplotlib.pyplot as plt
from scripts.nist_loader import get_nist_dataset
import os

def visualize():
    path = os.path.expanduser("~/projects/feedback_analyzer/data/tfrecords/nist_authentic.tfrecord")
    dataset = get_nist_dataset(path, batch_size=9)
    
    # Take one batch
    for images, labels in dataset.take(1):
        plt.figure(figsize=(10, 10))
        for i in range(9):
            plt.subplot(3, 3, i + 1)
            # We use 'gray_r' because NIST is usually black-on-white
            plt.imshow(images[i].numpy(), cmap='gray_r')
            plt.title(f"Label: {chr(labels[i].numpy())}")
            plt.axis('off')
        
        plt.tight_layout()
        plt.savefig("nist_batch_check.png")
        print("🎨 Success! 'nist_batch_check.png' saved to project root.")

if __name__ == "__main__":
    visualize()