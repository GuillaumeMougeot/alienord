import argparse
import os
import shutil
import yaml

import utils.mlcm as mlcm
import matplotlib.pyplot as plt
import seaborn as sns

from ultralytics import YOLO
from tqdm import tqdm
from sklearn.preprocessing import MultiLabelBinarizer
from typing import List

def get_labels(annotation_path: str) -> List[int]:
    """Given the path to a YOLO annotation file extract the class ids and return a set of the unique ids in the annotation file

    Args:
        annotation_path (str): path to YOLO annotation

    Returns:
        List[int]: List of unique class ids in the annotation file
    """
    labels = []
    with open(annotation_path, "r") as f:
        for line in f:
            elements = line.split()
            if elements: 
                labels.append(int(elements[0])) # First element is the class id

    return list(set(labels)) # Remove duplicates

def get_prediction(img_path: str, model, thresholds: List[float], save_dir: str) -> List[int]:
    """Get predictions of an image given a model and a set of class thresholds

    Args:
        img_path (str): path to image
        model: YOLO model
        thresholds List[float]: Thresholds per class
        save (bool): Whether to save or not

    Returns:
        List[int]: List of unique class predictions 
    """
    # We set the confidence low to get all the predictions and then apply the threshold
    result = model(img_path, verbose=False, conf=0.01)[0]
    
    class_ids = result.boxes.cls.tolist()
    confidences = result.boxes.conf.tolist()
    if save_dir:
        os.makedirs(os.path.join(save_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(save_dir, "labels"), exist_ok=True)
        img_name = os.path.basename(img_path)
        result.save(filename=os.path.join(save_dir, "images", img_name))
        result.save_txt(txt_file=os.path.join(save_dir, "labels", img_name[:-4]+".txt"), save_conf=True)

        # If there are no objects, but we want are saving predictions we create an empty file
        if len(class_ids) == 0: 
            # Hardcoded path, because YOLO doesn't allow you to specify the path so it doesn't make sense to specify it here either
            with open(os.path.join(save_dir, "labels", img_name[:-4]+".txt"), "w") as f:
                f.write("")
           
    # Apply thresholds 
    final_predictions = [int(class_ids[i]) for i, conf in enumerate(confidences) if conf >= thresholds[int(class_ids[i])]]

    return list(set(final_predictions)) # Remove duplicates

def multilabel_classification_report(labels: list, predictions: list, filenames: List[str]):
    """Given labels and predictions get confusion matrix and report

    Args:
        labels (List[int]): List of ground truth labels
        predictions (List[int]): List of predcitions
        filenames (List[str]): List of the filenames of the images


    Returns:
        Matrix of floats: One-vs-one normalized confusion matrix (recall)
        Matrix of strings: One-vs-one of the filenames of the images
    """

    mlb = MultiLabelBinarizer()
    labels_bin = mlb.fit_transform(labels)
    predictions_bin = mlb.transform(predictions)

    conf_mat, normal_conf_mat, files_mat = mlcm.cm(labels_bin, predictions_bin, filenames, print_note=False)
    
    report = mlcm.stats(conf_mat, print_binary_mat=False, verbose=True)
    
    print("\nClassification Report:")
    print(report) 
    print('\nOvO confusion Matrix:')
    print(conf_mat)
    print('\nOvO normalized confusion Matrix (%):')
    print(normal_conf_mat)
    
    return normal_conf_mat, files_mat

def organize_errors(matrix, class_names: List[str], output_dir: str, image_dir: str):
    """Given the matrix of files it will create a directory structure where to copy the images that have been missclassified

    Args:
        matrix NDArray[float64]: Matrix of files
        class_names (List[str]): Name of classes
        output_dir (str): Where to create the folder structure where we'll save the missclassifications
        image_dir (str): Where to find the images
    """

    # We create the folder structure. It will be like this: output_dir/true_label_1/predicted_label_1
    # Imagine we have 2 classes (A, B)
    # output_dir/A/B/*.jpg
    # output_dir/A/empty/*.jpg 
    # output_dir/B/A/*.jpg
    # output_dir/B/empty/*.jpg
    # output_dir/empty/A/*.jpg
    # output_dir/empty/B/*.jpg

    os.makedirs(output_dir, exist_ok=True)
    class_names.append("empty")
    # Iterate over matrix (not diagonal)
    num_classes = len(class_names)
    for i in range(num_classes):
        class_folder = os.path.join(output_dir, class_names[i]) # Folder for true_label
        os.makedirs(class_folder, exist_ok=True)
        for j in range(num_classes):
            if i == j:
                continue
            subfolder_path = os.path.join(class_folder, class_names[j]) # Subfolder for predicted_label
            os.makedirs(subfolder_path, exist_ok=True)
            for file in matrix[i][j]:
                image_path = os.path.join(image_dir, file)
                output_path = os.path.join(subfolder_path, file)
                shutil.copy(image_path, output_path)

def make_plot(matrix, class_names: List[str], plot_dir: str):
    """Create confusion matrix plot

    Args:
        matrix NDArray[float64]: Values of the confusion matrix
        class_names (List[str]): Name of classes
        plot_dir (str): Directory where to save it
    """
    if os.path.dirname(plot_dir) != "":
        os.makedirs(os.path.dirname(plot_dir), exist_ok=True)
    x = class_names + ["No prediction"]
    y = class_names + ["No target"]

    plt.figure(figsize=(9, 7))
    sns.heatmap(matrix, annot=True, cmap='Blues', xticklabels=x, yticklabels=y, vmin=0, vmax=100)
    plt.xlabel("Predicted label")
    plt.ylabel("True label")
    plt.title("Confusion matrix (%)\nRow: true label, Column: predicted label\n Diagonal is recall per class")
    plt.savefig(plot_dir, dpi=300)
    plt.close()
    
    
def load_config_yaml(config_file_dir_: str):
    with open(config_file_dir_, 'r') as file:
        config = yaml.safe_load(file)
        return config['names'], config['thresholds']


def load_data(image_dir: str, annotations_dir: str, model, thresholds: List[float], save_dir: str):
    labels = []
    predictions = []
    img_filenames = sorted(os.listdir(image_dir))
    for img_filename in tqdm(img_filenames):
        # Read annotation
        annotation_path = os.path.join(annotations_dir, img_filename[:-4] + ".txt")
        label = get_labels(annotation_path)
        labels.append(label)
        
        # Get prediction
        img_path = os.path.join(image_dir, img_filename)  
        prediction = get_prediction(img_path, model, thresholds, save_dir)
        predictions.append(prediction)  
        
    return labels, predictions, img_filenames

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate clasification metrics out of object detection model')

    parser.add_argument('-m', '--model', type=str, help='Directory to model .pt', required=True)
    parser.add_argument('-i', '--image_dir', type=str, help='Directory to images.', required=True)
    parser.add_argument('-a', '--annotations_dir', type=str, help='Location of YOLO annotations.', required=True)
    parser.add_argument('-c', '--config_file', type=str, help='Config yaml with names and thresholds', required=True)
    parser.add_argument('-p', '--plot', type=str, help='Path to plot confusion matrix')
    parser.add_argument('-e', '--errors', type=str, help='Directory to store miss classifications')
    parser.add_argument('-s', '--save_dir', type=str, help='Where to save predictions')
    
    args = parser.parse_args()
    
    print(f'Loading model from {args.model}...')    
    model = YOLO(args.model) # Load model

    print(f'Loading names and thresholds from {args.config_file}...')    
    names, thresholds = load_config_yaml(args.config_file)
        
    print(f'Loading labels, predictions and filenames...')
    labels, predictions, img_filenames = load_data(args.image_dir, args.annotations_dir, model, thresholds, args.save_dir)
    
    print(f'Running clasificationr report...')
    # We get the normalized one-vs-one confusion matrix (recall) and a matrix with the files of each cell
    confusion_matrix, files_matrix = multilabel_classification_report(labels, predictions, img_filenames)
    
    if args.plot is not None:
        print(f'Saving plot in {args.plot}...')
        make_plot(matrix=confusion_matrix, class_names=names, plot_dir=args.plot)
    
    if args.errors is not None:
        print(f'Saving errors in {args.errors}...')
        organize_errors(matrix=files_matrix, class_names=names, output_dir=args.errors, image_dir=args.image_dir)