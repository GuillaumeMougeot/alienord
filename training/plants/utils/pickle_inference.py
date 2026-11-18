import argparse
import os
import pickle

from ultralytics import YOLO
from tqdm import tqdm

# This script goes through all the images in a directory, runs an object detection model on them and then pickles the predictions in batches.

def get_image_subset(image_dir, annotation_dir):
    """
    Get a subset of images based on the annotations directory.

    Args:
        image_dir (str): Directory containing the images.
        annotation_dir (str): Directory containing the annotations.

    Returns:
        list: List of file paths for the images.
    """
    files = []
    for file_name in os.listdir(annotation_dir):
        file_name = os.path.splitext(file_name)[0]
        for ext in ['.jpg', '.png', '.jpeg']:
            full_path = os.path.join(image_dir, file_name + ext)
            if os.path.exists(full_path):
                files.append(full_path)
                break
    return files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Predict images and save the predictions into a pickle file')
    parser.add_argument('-m', '--model_dir', type=str, help='Directory where to find the model weights', required=True)
    parser.add_argument('-i', '--image_dir', type=str, help='Directory where to find the images', default='/workspaces/.darwin/datasets/triforkext/biodiversity/images')
    parser.add_argument('-a', '--annotation_dir', type=str, help='Directory where to find the subselection of images to predict (Darwin release)')
    parser.add_argument('-p', '--pickle_dir', type=str, help='Directory where to save predicted images', default='datasets/pickled_inference/data.pkl')
    parser.add_argument('-b', '--batch_size', type=int, help='Batch size for predictions', default=50)
    args = parser.parse_args()

    if args.annotation_dir is not None:
        files = get_image_subset(args.image_dir, args.annotation_dir)
    else:
        files = []
        for file in os.listdir(args.image_dir):
            filename = os.path.join(args.image_dir, file)
            if os.path.isfile(filename):
                files.append(filename)

    model = YOLO(args.model_dir)
    predictions = []

    for i in tqdm(range(0, len(files), args.batch_size)):
        batch_files = files[i:i + args.batch_size]
        batch_predictions = model(batch_files, verbose=False, conf=0.1)
        for prediction in batch_predictions:
            predictions.append([os.path.basename(prediction.path), prediction.boxes, prediction.tojson()])
    
    os.makedirs(os.path.dirname(args.pickle_dir), exist_ok=True)
    with open(args.pickle_dir, 'wb') as file:
        pickle.dump(predictions, file)
