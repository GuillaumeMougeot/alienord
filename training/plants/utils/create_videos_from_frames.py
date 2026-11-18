import os
import re
import cv2
import argparse
from tqdm import tqdm

def filter_filenames(path):
    """
    Filter filenames in the given directory path.

    Args:
        path (str): Path to the directory containing files.

    Returns:
        list: List of filenames in the directory.
    """
    filenames = []
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)):
            filenames.append(filename)
    return filenames

def filter_and_extract_pattern(filenames, pattern):
    """
    Filter filenames based on the given pattern and extract them.

    Args:
        filenames (list): List of filenames to filter.
        pattern (str): Regular expression pattern to match filenames.

    Returns:
        list: List of extracted filenames matching the pattern.
    """
    extracted_filenames = []
    for filename in filenames:
        match = re.match(pattern, filename)
        if match:
            extracted_filenames.append(match.group())
    return extracted_filenames

def create_video(image_path, output_path, fps=5):
    """
    Create a video from images.

    Args:
        image_path (str): Path to the directory containing images.
        output_path (str): Path to save the output video.
        fps (int): Frames per second for the output video.
    """
    basename = os.path.basename(image_path)
    dirname = os.path.dirname(image_path)
    
    image_files = []
    for img in os.listdir(dirname):
        if img.startswith(basename):
            image_files.append(img)
        
    if not image_files:
        print(f"No supported image files found in {image_path}")
        return

    first_image = cv2.imread(os.path.join(dirname, image_files[0]))
    height, width, _ = first_image.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for image_file in image_files:
        img = cv2.imread(os.path.join(dirname, image_file))
        out.write(img)

    out.release()

def main(images_path, output_dir, fps=5):
    """
    Main function to create videos from images.

    Args:
        images_path (str): Path to the directory containing images.
        output_dir (str): Path to the directory to save the output videos.
        fps (int): Frames per second for the output videos.
    """
    filenames = filter_filenames(images_path)
    pattern = r'^\d{8}T\d{6}\.\d{3}'
    extracted_filenames = filter_and_extract_pattern(filenames, pattern)
    sorted_and_unique_filenames = sorted(set(extracted_filenames))

    os.makedirs(os.path.join(output_dir, "videos", "raw"), exist_ok=True)

    for recording in tqdm(sorted_and_unique_filenames):
        image_path = os.path.join(images_path, recording)
        create_video(image_path, os.path.join(output_dir, "videos", "raw", recording + ".mp4"), fps)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create videos from images.')
    parser.add_argument('-i', '--images_path', type=str, help='Path to the directory containing images')
    parser.add_argument('-o', '--output_dir', type=str, default='.', help='Path to the output directory (default: current directory)')
    parser.add_argument('--fps', type=int, default=5, help='Frames per second for the output videos (default: 5)')
    args = parser.parse_args()
    
    main(args.images_path, args.output_dir, args.fps)
