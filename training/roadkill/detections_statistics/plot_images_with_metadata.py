import os
import json
from PIL import Image, ImageDraw

# Paths
images_folder_path = "/Users/aleksandra/Desktop/2-4_Oct/checked"
meta_folder_path = "/Users/aleksandra/Desktop/meta"
plotted_images_path = "/Users/aleksandra/Desktop/2-4_Oct/FP_plot"

def get_image_dimensions(jpg_path):
    with Image.open(jpg_path) as img:
        return img.size

def get_rect_params(json_path):
    try:
        with open(json_path, 'r') as file:
            data = json.load(file)
            objects = data.get("objects", [])
            rect_params_list = [obj.get("rect_params_normalized", None) for obj in objects if "rect_params_normalized" in obj]
            
            if not rect_params_list:
                print(f"Warning: Expected rectangle parameters not found in JSON file: {json_path}")
                return None
            
            return rect_params_list

    except json.JSONDecodeError:
        print(f"Warning: Invalid or empty JSON format in file: {json_path}")
        return None


def draw_rectangle_on_image(jpg_path, rect_params, output_folder):
    if rect_params is None:
        print(f"Missing rectangle parameters for image: {jpg_path}")
        return

    with Image.open(jpg_path) as img:
        width, height = img.size
        
        # convert normalized values
        left = int(rect_params["left"] * width)
        top = int(rect_params["top"] * height)
        rect_width = int(rect_params["width"] * width)
        rect_height = int(rect_params["height"] * height)

        # draw rectangle
        draw = ImageDraw.Draw(img)
        draw.rectangle([left, top, left + rect_width, top + rect_height], outline="red")
        
        # save result
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        output_path = os.path.join(output_folder, os.path.basename(jpg_path))
        img.save(output_path)


def main(images_folder_path, meta_folder_path, output_folder):
    for jpg_filename in os.listdir(images_folder_path):
        if jpg_filename.endswith('.jpg'):
            # read image dimensions
            jpg_path = os.path.join(images_folder_path, jpg_filename)
            
            # find the corresponding .json file
            json_filename = jpg_filename.replace('.jpg', '.json')
            json_path = os.path.join(meta_folder_path, json_filename)
            
            # check if the corresponding .json file exists
            if os.path.exists(json_path):
                rect_params_list = get_rect_params(json_path)
                
                if rect_params_list is not None:
                    for rect_params in rect_params_list:
                        draw_rectangle_on_image(jpg_path, rect_params, output_folder)
            else:
                print(f"No corresponding .json file found for {jpg_filename}")
                
if __name__ == "__main__":
    main(images_folder_path, meta_folder_path, plotted_images_path)








