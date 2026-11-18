import argparse
import os
import yaml
import multiprocessing as mp
import numpy as np

from tqdm import tqdm
from hashlib import sha256
from typing import List, Tuple

from core.infra.adapters.training.io.read import ImgReader, Darwin2Reader, Annotation
from core.infra.adapters.training.io.write import YoloV8DetectionWriter

"""
Arguments:
- annotation_dir: Directory of Darwin annotations
- image_dir: Directory of images, only used to get the image size
- output_dir: Directory to save YOLO annotations
- config_file: Directory of config file 
- no_plant: Percentage of no plant images to use
- num-workers: Number of parallel workers

Description:
This script converts annotations from Darwin format to YOLO format. It uses the Darwin2Reader to read the annotations and the ImgReader to read the images. It uses the YoloV8DetectionWriter to write the annotations in YOLO format. 
The darwin annotations might have masks from which we'll take the bounding box information. Masks and bboxes of the same class will be merged into a single class.
This script will go through all the Darwin annotations and only convert those that the class is in the list of classes we want to train on. It will also keep a percentage of the no_plant images to use.

Example:
python3 -m training.utils.darwin2yolo -a /home/username/darwin_annotations -i /home/username/images -o /home/username/yolo_annotations -c /home/username/config_file.yaml -np 10 --num-workers 4

"""

def clean_class(class_name: str) -> str:
    return class_name.replace("_box", "").replace("_mask", "")


def keep_no_plant(class_name: str, name: str, no_plant_percent: int) -> bool:
    probs = (int.from_bytes(sha256(name.encode()).digest(), 'little') & 0xffffffff) / 0xffffffff
    return class_name == "no_plant" and probs <= no_plant_percent / 100


def is_good_annotation(annotation: Annotation, classes: List[str]) -> bool:
    # An annotation is good if it has a Bounding box and it's in the classes we want
    class_name = clean_class(annotation.label)
    return annotation.bbox and class_name in classes


def convert_annotations_chunk(chunk: Tuple[Darwin2Reader, YoloV8DetectionWriter, ImgReader, List[str], List[str], int, str, int]):
    darwin_reader, yolo_writer, image_reader, filenames, classes, no_plant_percent, output_dir, idx = chunk

    pbar = tqdm(filenames, position=idx, desc=f"Worker {idx: <3}")

    for filename in pbar:
        annotations = darwin_reader.read(filename, include_tags=True)

        good_annotations = []
        for annotation in annotations:
            if is_good_annotation(annotation, classes):
                annotation.label = clean_class(annotation.label)
                good_annotations.append(annotation)
            elif keep_no_plant(annotation.label, filename, no_plant_percent):
                open(os.path.join(output_dir, filename + ".txt"), 'a').close()

        if good_annotations:
            img_width, img_height = image_reader.read(filename).size
            yolo_writer.write(good_annotations, filename, img_width, img_height)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Change data from Darwin to YOLO format')

    parser.add_argument('-a', '--annotation_dir', type=str, help='Directory of Darwin annotations', required=True)
    parser.add_argument('-i', '--image_dir', type=str, help='Directory of images', required=True)
    parser.add_argument('-o', '--output_dir', type=str, help='Directory to save YOLO annotations', required=True)
    parser.add_argument('-c', '--config_file', type=str, help='Directory of file with classes we will train on', required=True)
    parser.add_argument('-np', '--no_plant', type=int, help='Percentage of no plant images to use', default=10)
    parser.add_argument('--num-workers', type=int, default=mp.cpu_count() - 1, help='Number of parallel workers')

    args = parser.parse_args()

    with open(args.config_file, 'r') as file:
        config = yaml.safe_load(file)
        classes = config['names']

    filenames = Darwin2Reader(args.annotation_dir).list_names()

    assert args.num_workers <= mp.cpu_count(), f"It is unwise to use more {args.num_workers=} than cores available {mp.cpu_count()=}"

    num_workers = min(len(filenames), args.num_workers)

    # prepare the chunks for parallel work
    chunks = list()
    chunk_idxs = np.linspace(0, len(filenames), num_workers + 1, endpoint=True, dtype=int)
    for idx, (chunk_begin, chunk_end) in enumerate(zip(chunk_idxs, chunk_idxs[1:])):
        
        darwin_reader = Darwin2Reader(args.annotation_dir)
        yolo_writer = YoloV8DetectionWriter(args.output_dir, labels=classes)
        image_reader = ImgReader(args.image_dir)
        
        chunks.append((darwin_reader, yolo_writer, image_reader, filenames[chunk_begin:chunk_end], classes, args.no_plant, args.output_dir, idx))

    # execute the chunks in parallel
    with mp.Pool(processes=num_workers) as pool:
        list(pool.imap_unordered(convert_annotations_chunk, chunks))
