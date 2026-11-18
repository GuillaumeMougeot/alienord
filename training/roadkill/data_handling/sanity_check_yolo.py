import os 
from PIL import Image, ImageDraw

from rw.read import Yolov8DetectionReader

annotation_path = 'data/preprocessed/val/labels'
images_path = 'data/preprocessed/val/images'
plotted = 'data/sanity'
all_annotations = os.listdir(annotation_path)
images = os.listdir(images_path)

yolov8reader = Yolov8DetectionReader(annotation_path, 'labelmap.json')

for anno_file in all_annotations:
    filename = anno_file.replace('.json', '')
    image_name = filename + '.jpg'
    image_path = os.path.join(images_path, image_name)
    img = Image.open(image_path)
    w, h = img.size
    draw = ImageDraw.Draw(img)
    annotations = yolov8reader.read(filename, w, h)
    for ann in annotations:
        draw.rectangle((ann.bbox.left, ann.bbox.top, ann.bbox.left + ann.bbox.width, ann.bbox.top + ann.bbox.height))
        draw.text((20,20), ann.label)
    image = draw._image
    image.save(os.path.join(plotted, image_name))



