import json
from lib2to3.pytree import Base
import os
from PIL import Image, ImageDraw, ImageFont
import PIL
import cv2
import numpy as np
import shutil
path = '/Users/zud/Documents/Proj'
def json_to_dict(path):
    with open(path, 'r') as f:
        d = json.loads(f.read())
    return d

def mk_dir(path):
    try:
        os.makedirs(path)
    except Exception as e:
        shutil.rmtree(path)
        os.makedirs(path)
    if not os.path.exists(path):
            raise Exception("Could not create a new annotation directory.")

mk_dir(f'{path}/bbox')

for file in os.listdir(f'{path}/images_fullsize'):
    try:
        image = Image.open(f'{path}/images_fullsize/{file}')
    except BaseException as e:
        print(e)
        continue
    j = json_to_dict(f'{path}/meta/{file.split(".")[0]}' + '.json')
    bbox = []
    meta = []
    for obj in j['frame_metadata']['objects'].values():
        if obj['class_label'] == 'DeadAnimal':
            top = (obj['rect_params_normalized']['top']) 
            left = (obj['rect_params_normalized']['left']) 
            width = + obj['rect_params_normalized']['width']
            height = + obj['rect_params_normalized']['height']
            bbox.append([left*4024, top*3036, (left+width)*4024, (top+height)*3036])
            meta.append(f"Speed: {float(j['frame_metadata']['gps']['speed_kmh']):.2f}, Confidence: {float(obj['confidence']):.2f}")
    image_ex = ImageDraw.Draw(image.copy())
    print(meta)
    for line in bbox:
        image_ex.rectangle(line, fill = None, outline="#90EE90", width = 6)
        image_ex.text((1340,250), meta[0], fill = '#90EE90', font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 75))
    output_img = image_ex._image
    output_img.save(f'{path}/bbox/{file}')

