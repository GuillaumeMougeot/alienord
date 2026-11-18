import os
import json
import argparse
from tqdm import tqdm
from typing import List

def get_all_filenames(folder_path: str):
    """
    Retrieves all filenames within the specified folder path.

    Parameters:
        folder_path (str): The path to the folder.

    Returns:
        list: A list of tuples containing folder name and filename.
    """
    filenames = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            filenames.append((os.path.relpath(root, folder_path), os.path.splitext(os.path.basename(file))[0]))

    return filenames

def get_workview_urls(darwin_annotation_path: str, filenames: List[str]):
    """
    Retrieves workview URLs from JSON files based on the filenames.

    Parameters:
        darwin_annotation_path (str): The path to the directory containing JSON files.
        filenames (list): A list of tuples containing folder name and filename.

    Returns:
        list: A list of tuples containing folder name and workview URL.
    """
    workview_urls = []
    
    for folder, filename in filenames:
        json_file_path = os.path.join(darwin_annotation_path, filename + '.json')
        if os.path.isfile(json_file_path):
            with open(json_file_path, 'r') as json_file:
                data = json.load(json_file)
   
                workview_url = data.get('item').get('source_info').get('workview_url')
      
                if workview_url:
                    workview_urls.append((folder, workview_url))

    return workview_urls

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a txt file with links to Darwin annotations.")
    parser.add_argument("-f", "--folder_path", type=str, help="Path to the folder containing files.")
    parser.add_argument("-a", "--darwin_annotation_path", type=str, help="Path to the directory containing Darwin JSON files.", default="/workspaces/.darwin/datasets/triforkext/biodiversity/releases/latest/annotations")
    parser.add_argument("-o", "--output_file", type=str, help="Output file path.")

    args = parser.parse_args()

    filenames = get_all_filenames(args.folder_path)
    urls = get_workview_urls(args.darwin_annotation_path, filenames)

    with open(args.output_file, 'w') as file:
        for folder, item in tqdm(urls):
            file.write("%s\t%s\n" % (folder, item))