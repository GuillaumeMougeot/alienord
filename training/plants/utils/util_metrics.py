import math

from ultralytics.engine.results import Boxes

def entropy(p):
    """
    Calculate entropy for a given probability.
    
    Args:
        p (float): Probability value.

    Returns:
        float: Entropy value.
    """
    if p == 0 or p == 1:
        return 0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def entropy_from_yolo_boxes(boxes: Boxes):
    """
    Given the Boxes objects from a YOLO results it calculate the entropy for each detection and creates a dict where the key 
    is the class of the detection and the value a list of the entropies of the detections.

    Args:
        boxes: Detected boxes.

    Returns:
        dict: Dictionary containing a list of entropies for each class.
    """
    classes = boxes.cls.tolist()
    classes = [int(x) for x in classes]
    
    confidences = boxes.conf.tolist()

    class_entropy = {}
    for cls, conf in zip(classes, confidences):
        if cls not in class_entropy:
            class_entropy[cls] = []
        class_entropy[cls].append(entropy(conf))
    return class_entropy


def calculate_avg_entropies(class_entropy, num_classes):
    """
    Calculate average entropies for each class.

    Args:
        class_entropy (dict): Dictionary containing entropy for each class.
        num_classes (int): Number of classes.

    Returns:
        list: List of average entropies for each class.
    """
    class_entropies = [0] * num_classes
    for cls, entropies in class_entropy.items():
        class_entropies[cls] = sum(entropies) / len(entropies) if entropies else 0
    return class_entropies