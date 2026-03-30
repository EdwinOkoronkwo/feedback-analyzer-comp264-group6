import matplotlib.pyplot as plt
from scripts.mnist_loader import get_mnist_dataset
import os

def visualize_samples():
    # Path to your baked TFRecord
    path = "data/tfrecords/mnist_standard.tfrecord"
    
    # Use your validated loader!
    dataset = get_mnist_dataset(path, batch_size=9)
    
    # Take exactly one batch of 9 images
    for images, labels in dataset.take(1):
        plt.figure(figsize=(10, 10))
        
        for i in range(9):
            plt.subplot(3, 3, i + 1)
            # Remove the channel dimension for plotting: (28, 28, 1) -> (28, 28)
            img = images[i].numpy().squeeze()
            
            plt.imshow(img, cmap='gray')
            plt.title(f"Label: {labels[i].numpy()}")
            plt.axis('off')
        
        plt.tight_layout()
        plt.savefig("mnist_final_check.png")
        print("🎨 Success! 'mnist_final_check.png' saved to project root.")

if __name__ == "__main__":
    visualize_samples()