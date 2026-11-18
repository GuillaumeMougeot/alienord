import argparse
import os
import heapq
import json
import pickle

from ultralytics import YOLO
from tqdm import tqdm

from core.infra.adapters.annotation.shapely.annotation import AnnotationAdapter as Annotation
from core.domain.geom import BBox
from core.infra.adapters.training.io.write import Darwin2Writer

import utils.util_metrics as utils

# TODO: Right now this only works with images from Darwin (Upload images to darwin, download them with annotations, run active learning and then reupload them)
#       We need to be able to perform active learning as a prior step (Run active learning and upload new images to darwin)


def get_image_subset(image_dir, annotation_dir):
    """
    Get subset of images that have annotations.

    Args:
        image_dir (str): Directory containing images.
        annotation_dir (str): Directory containing annotations.

    Returns:
        list: List of image file paths.
    """
    allowed_extensions = ['.jpg', '.png', '.jpeg', '.gif', '.bmp']
    
    files = []
    for file_name in os.listdir(annotation_dir):
        file_name = os.path.splitext(file_name)[0]
        for ext in allowed_extensions:
            full_path = os.path.join(image_dir, file_name + ext)
            if os.path.exists(full_path):
                files.append(full_path)
                break
    return files

def json_to_annotation(str_json):
    """
    Convert JSON annotations to Annotation objects.

    Args:
        str_json (str): JSON string containing annotations.

    Returns:
        list: List of Annotation objects.
    """
    json_data = json.loads(str_json)
    annotations = []
    for item in json_data:
        label = item["name"]+"_box"
        bbox_data = item["box"]
        bbox = BBox(bbox_data["x1"], bbox_data["y1"], bbox_data["x2"] - bbox_data["x1"], bbox_data["y2"] - bbox_data["y1"])
        annotations.append(Annotation(bbox=bbox, polygon=None, label=label))
    return annotations
    
def save_predictions(top_predictions, annotation_dir, output_dir):            
    """
    Save predicted images with annotations.

    Args:
        top_predictions (dict): Dictionary containing predicted images.
        annotation_dir (str): Directory containing original annotations.
        output_dir (str): Directory to save predicted images with annotations.
    """
    annotation_writer = Darwin2Writer(output_dir)
    for _, top_pred in top_predictions.items(): # Loop through all the classes
        for pred in top_pred: # Loop through the top n files
            try:
                darwin_annotations = []
                darwin_annotations.append({"id": "", "name": "autoannotated", "slot_names": ["0"], "tag": {}})
                for ann in json_to_annotation(pred[2]): # Each file might have multiple annotations
                    darwin_annotations.append(annotation_writer.get_darwin_annotation(ann))
                    
                name, _ = os.path.splitext(pred[1])
                with open(os.path.join(annotation_dir, name+".json"), 'r') as file: # Get the original json
                    json_content = json.load(file)
                
                json_content["annotations"].extend(darwin_annotations)
                
                with open(os.path.join(output_dir, name+".json"), 'w') as fp:
                    json.dump(json_content, fp)
            except FileNotFoundError as e:
                print(f"File not found: {e}")
                continue
       
def run_prediction(files, model):
    """
    Given a list of files and a model, run predictions on them.

    Args:
        files (list): List of file paths.
        model: YOLO model object.

    Returns:
        list: List of predictions.
    """
    print(f'Running predictions on {len(files)} images...')
    predictions = []
    for i in tqdm(range(0, len(files), 50)):
        batch_files = files[i:i + 50]
        batch_predictions = model(batch_files, verbose=False, conf=0.1)
        for prediction in batch_predictions:
            predictions.append([prediction.path, prediction.boxes, prediction.tojson()])
    return predictions

def load_predictions(model, pickle_dir=None, annotation_dir=None, image_dir=None):
    """Load predictions, from a saved pickle or by running the model on the images.

    Args:
        pickle_dir (str): Direction to pickled predictions.
        annotation_dir (str): Direction to annotations.
        image_dir (str): Direction to images.
        model: YOLO model object.

    Returns:
       predictions: List of predictions.
    """
    if pickle_dir and os.path.exists(pickle_dir):
        print(f'Loading predictions from {pickle_dir}')
        with open(pickle_dir, 'rb') as file:
            predictions = pickle.load(file)
    elif annotation_dir is not None:
        files = get_image_subset(image_dir, annotation_dir)
        predictions = run_prediction(files, model)
    else:
        files = []
        for file in os.listdir(image_dir):
            filename = os.path.join(image_dir, file)
            if os.path.isfile(filename):
                files.append(filename)              
        predictions = run_prediction(files, model)
    
    return predictions

def get_top_n_predictions(predictions, top_n, num_classes):
    """Get the top n predictions for each class.

    Args:
        predictions: List of predictions.
        top_n: Number of top predictions to get.
        num_classes: List of classes.

    Returns:
        top_n_predictions: Dictionary containing the top n predictions for each class.
    """
    top_n_predictions = {idx: [] for idx in range(num_classes)}    

    for prediction in tqdm(predictions):
        path, boxes, tojson = prediction[0], prediction[1], prediction[2]

        class_entropies = utils.entropy_from_yolo_boxes(boxes)
        avg_class_entropies = utils.calculate_avg_entropies(class_entropies, num_classes)
        
        for idx, avg_entropy in enumerate(avg_class_entropies):
            if avg_entropy == 0:
               continue
            
            class_heap = top_n_predictions[idx]
            if len(class_heap) < top_n:
                heapq.heappush(class_heap, (avg_entropy, path, tojson))
            elif avg_entropy > class_heap[0][0]:
                heapq.heappushpop(class_heap, (avg_entropy, path, tojson))
            top_n_predictions[idx] = class_heap
            
    return top_n_predictions
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Entropy based active learning')
    parser.add_argument('-m', '--model_dir', type=str, help='Directory where to find the models weights', required=True)
    parser.add_argument('-i', '--image_dir', type=str, help='Directory where to find the images', default='/workspaces/.darwin/datasets/triforkext/biodiversity/images')
    parser.add_argument('-a', '--annotation_dir', type=str, help='Directory where to find the annotations', required=True)
    parser.add_argument('-o', '--output_dir', type=str, help='Directory where to save predicted images', default='datasets/active_learning')
    parser.add_argument('-p', '--pickle_dir', type=str, help='Directory where to find pickled predictions', default='datasets/pickled_inference/data.pkl')
    parser.add_argument('-n', '--top_n', type=int, help='It will save top N images per class with highest avg entropy')
    
    args = parser.parse_args()
    
    print("Loading model...")
    model = YOLO(args.model_dir)
    
    print("Loading predictions...")
    predictions = load_predictions(model=model, pickle_dir=args.pickle_dir, annotation_dir=args.annotation_dir, image_dir=args.image_dir)

    print(f'Getting top {args.top_n} predictions for each class...')
    top_n_predictions = get_top_n_predictions(predictions=predictions, top_n=args.top_n, num_classes=len(model.names))

    print(f'Saving predictions to {args.output_dir}')
    save_predictions(top_predictions=top_n_predictions, annotation_dir=args.annotation_dir, output_dir=args.output_dir)