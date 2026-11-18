import os
import argparse
import yaml

def load_labelmap_from_config(path_to_config: str) -> dict:
    """
    Load labelmap from a YAML configuration file.

    Args:
        path_to_config (str): Path to the YAML configuration file.

    Returns:
        dict: A dictionary mapping class indices to class names.
    """
    label_map = {}
    with open(path_to_config, 'r') as file:
        config = yaml.safe_load(file)
        labels = config.get('names', [])
        for idx, label in enumerate(labels):
            label_map[idx] = label
    return label_map

def count_classes(path_to_dir: str, labelmap: dict) -> dict:
    """
    Count the occurrences of each class in a dataset directory.

    Args:
        path_to_dir (str): Path to the dataset directory.
        labelmap (dict): Dictionary mapping class indices to class names.

    Returns:
        dict: A dictionary containing class counts and total image count.
    """
    # Initialize the count dictionary
    count = {label: 0 for label in labelmap.values()}
    count['NoClass'] = 0  # To count images with no class
    count['TotalImages'] = 0  # To count the total number of images 

    # Iterate through each folder, including subfolders, in the dataset directory
    for folder_path, _, filenames in os.walk(path_to_dir):
        # Iterate through each file in the folder
        for filename in filenames:
            file_path = os.path.join(folder_path, filename)

            # Read the file and count classes
            with open(file_path, 'r') as file:
                lines = file.readlines()
                if not lines:
                    count['NoClass'] += 1  # Count images with no class
                else:
                    count['TotalImages'] += 1  # Count the file itself
                    for line in lines:
                        class_label = int(line.split()[0])
                        count[labelmap[class_label]] += 1

    return count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Count classes in a dataset directory.')
    parser.add_argument('-a', '--annotation_dir', type=str, help='Location of YOLO annotations.', required=True)
    parser.add_argument('-c', '--config_file', type=str, help='Config yaml', required=True)
    args = parser.parse_args()

    labelmap = load_labelmap_from_config(args.config_file)
    result = count_classes(args.annotation_dir, labelmap)
    for name, num in result.items():
        print(f'{name:15}{num}')
