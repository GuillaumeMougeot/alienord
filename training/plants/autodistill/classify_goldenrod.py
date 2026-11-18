import json
import os
from typing import List
import torch
from PIL import Image, ImageDraw, ImageFont
from lavis.models import load_model_and_preprocess

def read_darwin2(path: str, filter_label: str = 'goldenrod_box') -> List:
        annotations = []
        with open(os.path.join(path), 'r') as f:
            darwin_annotations = json.load(f)
            for ann in darwin_annotations['annotations']:
                label = ann['name']
                if label != filter_label:
                     continue
                
                try:
                    # try getting bbox and polygon
                    bbox_coords = ann['bounding_box']
                except KeyError as e:
                    continue

                annotations.append(bbox_coords)
        return annotations


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

BASE_PATH = '/media/data/darwin_datasets/triforkext/biodiversity'
IMAGE_PATH = os.path.join(BASE_PATH, 'images')
LABEL_PATH = os.path.join(BASE_PATH, 'releases', '20231015-goldenrod-box', 'annotations')
IMAGE_PATHS = [os.path.join(IMAGE_PATH, img_basename) for img_basename in sorted(os.listdir(IMAGE_PATH))]
LABEL_PATHS = [os.path.join(LABEL_PATH, label_basename) for label_basename in sorted(os.listdir(LABEL_PATH))]

model, vis_processors, txt_processors = load_model_and_preprocess(name="blip_vqa", model_type="vqav2", is_eval=True, device=DEVICE)

# question = "Is the annotated plant's stem leafy?"
question = "Is the annotated plant's stem hairy?"
question = txt_processors["eval"](question)

font = ImageFont.truetype('DejaVuSans.ttf', 40)

for image_path, label_path in zip(IMAGE_PATHS, LABEL_PATHS):
    image_basename = os.path.basename(image_path)
    image_name, _ = os.path.splitext(image_basename)
    raw_image = Image.open(image_path).convert('RGB')
    annotations = read_darwin2(label_path, filter_label='goldenrod_box')
    
    original_image = raw_image.copy()
    draw = ImageDraw.Draw(raw_image)

    image_answers = []
    for i, ann in enumerate(annotations):
        left, top, width, height = ann['x'], ann['y'], ann['w'], ann['h']
        right, bottom = left + width, top + height
        
        annotated_image = original_image.copy()
        draw_ann = ImageDraw.Draw(annotated_image)
        for d in [draw, draw_ann]:
            d.rectangle((round(left), round(top), round(right), round(bottom)), outline='red', width=2)
        
        # draw text on the image
        text_left, text_top, text_right, text_bottom = draw.textbbox((round(left), round(bottom-20)), f"{i}", font)
        draw.rectangle((text_left-5, text_top-5, text_right+5, text_bottom+5), fill='black')
        draw.text((round(left), round(bottom-20)), f"{i}", fill='white', font=font)
        
        image = vis_processors["eval"](annotated_image).unsqueeze(0).to(DEVICE)

        answers = model.predict_answers(samples={"image": image, "text_input": question}, inference_method="generate")

        image_answers.append(f"{i}: {answers}\n")

    with open(f'goldenrod/answers/{image_name}.txt', 'w') as f:
        f.writelines(image_answers)

    raw_image.save(f'goldenrod/annotated/{image_basename}')