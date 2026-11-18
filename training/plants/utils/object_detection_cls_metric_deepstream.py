import argparse
import os
import yaml

import utils.mlcm as mlcm
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import MultiLabelBinarizer
from typing import List

def load_config_yaml(config_file_dir_: str):
    with open(config_file_dir_, 'r') as file:
        config = yaml.safe_load(file)
        return config['names']

def get_predictions(prediction_dir: str, label_map: dict, num_files: int):
    predictions = [[] for _ in range(num_files)]
    # open prediction_dir file and read the lines
    with open(prediction_dir, 'r') as file:
        lines = file.readlines()
        for line in lines:
            frame_num, class_name = line.split()
            predictions[int(frame_num)].append(label_map[class_name])

    for idx, pred in enumerate(predictions):
        pred = list(set(pred))
        predictions[idx] = pred

    return predictions

def get_ground_truth(annotation_path: str) -> List[int]:
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

def load_data(ground_truth_dir: str, prediction_dir: str, label_map):

    labels = []
    predictions = []

    filenames = sorted(os.listdir(ground_truth_dir))
    
    for file in filenames:
        # Read annotation
        annotation_path = os.path.join(ground_truth_dir, file)
        label = get_ground_truth(annotation_path)
        labels.append(label)

    predictions = get_predictions(prediction_dir, label_map, len(filenames))

    return labels, predictions

def multilabel_classification_report(labels: list, predictions: list):
    """Given labels and predictions get confusion matrix and report

    Args:
        labels (List[int]): List of ground truth labels
        predictions (List[int]): List of predcitions


    Returns:
        Matrix of floats: One-vs-one normalized confusion matrix (recall)
    """

    mlb = MultiLabelBinarizer()
    labels_bin = mlb.fit_transform(labels)
    predictions_bin = mlb.transform(predictions)
    print("labels_bin", labels_bin)
    print("predictions_bin", predictions_bin)

    conf_mat, normal_conf_mat = mlcm.cm(labels_bin, predictions_bin, print_note=False)

    report = mlcm.stats(conf_mat, print_binary_mat=False, verbose=True)

    print("\nClassification Report:")
    print(report) 
    print('\nOvO confusion Matrix:')
    print(conf_mat)
    print('\nOvO normalized confusion Matrix (%):')
    print(normal_conf_mat)

    return normal_conf_mat

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate clasification metrics out of object detection model')

    parser.add_argument('-gt', '--ground_truth', type=str, help='Location of YOLO ground truth.', required=True)
    parser.add_argument('-pd', '--predictions', type=str, help='Location of Deepstream predictions.', required=True)
    parser.add_argument('-c', '--config_file', type=str, help='Config yaml with names and thresholds', required=True)
    parser.add_argument('-p', '--plot', type=str, help='Path to plot confusion matrix')
    
    args = parser.parse_args()
    
    print(f'Loading names from {args.config_file}...')    
    names = load_config_yaml(args.config_file)

    label_map = {}
    for idx, name in enumerate(names):
        label_map[name] = idx

    print(f'Loading labels and predictions...')
    labels, predictions = load_data(args.ground_truth, args.predictions, label_map)
    
    # We get the normalized one-vs-one confusion matrix (recall) and a matrix with the files of each cell
    confusion_matrix = multilabel_classification_report(labels, predictions)
    
    if args.plot is not None:
        print(f'Saving plot in {args.plot}...')
        make_plot(matrix=confusion_matrix, class_names=names, plot_dir=args.plot)