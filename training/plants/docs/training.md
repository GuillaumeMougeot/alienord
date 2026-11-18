# Iterative training process for the VD-Biodiversity project 
In this file we'll explain the iterative training and annotating process that we're following at the moment in the biodiversity project

## General overview:
1. Import the data from darwin in Darwin2.0 format
2. Convert the data to YOLO format and split it into train/test/validation
3. Train the model
4. Get the metrics of the model
5. Review the missclassifcations of the model (Confident learning)
6. Get a new batch of images that "confuse" the model and we annotate them (Active learning)
7. Back to setp 1

## Detailed overview

1. **Import data from darwin in Darwin2.0 format**
    
    1.1 Go to Darwin, select images we want to export and export them (Make sure to select Darwin2.0)
    
    1.2 Copy Darwin CLI command and run it (Will look like this: darwin dataset pull triforkext/biodiversity:< release>)

2. **Set up data**
    Run the training/scripts/setup_data.sh script
    
    This script will perform the transformation and splitting of the data

    The script has multiple arguments, all of which have default values. 

    - **-r, --release_name**:      Name of the Darwin2.0 release _(default: latest)_
    - **-o, --output_dir**:        Output directory for YOLOv8 format data _(default: datasets/postprocessed)_
    - **-i, --image_dir**:         Directory containing images _(default: /workspaces/.darwin/datasets/triforkext/biodiversity/images)_
    - **-c, --config_file**:       Configuration file containing the labels _(default: config.yaml)_
    - **-n, --no_plant**:          Percentage of no_plant images to keep _(default: 10)_
    - **-v, --validation_split**:  Percentage of data for validation _(default: 10)_
    - **-t, --test_split**:        Percentage of data for testing _(default: 5)_
    - **-m, --mandatory_file_split**: File where to specify the split a specific image should go to. Format: split_name image_name _(optional)_
    
    **Extra info on config_file**: Directory to yaml file where you specify the plants you want to train on. The darwin annotations will have this format: plant_mask or plant_box, in the config.yaml you need to put only the plant name, the script will strip the suffixes. You need to put a plant name per line in the **name** key

    **Extra info on mandatory_file_split**: This is done because we might want to specify an image to a split and we don't want it to end up in the wrong split.

    **Extra info on output_dir**: Will have this format: output_dir/ {images/labels} / {train/test/val}

    This script will also print the data distribution of all the classes in all three splits and the combination of all. Remember that multiple classes can appear in the same image

3. **Train the model**

    First we create a model_config.yaml file:

    Example: 

    ```{yaml}
        path: ../{SAME PATH AS OUTPUT_DIR IN PREVIOUS STEP}
        train: images/train  # train images (relative to 'path')
        val: images/val  # val images (relative to 'path') 
        test: images/test # test images (relative to 'path') 

        names: # The names NEED to be in the same order as the config.yaml in the second step!
        0: beach_rose
        1: goldenrod
        2: lupin
        3: scotch_broom
        4: parsley
    ```

    Then we train:

    Example:
    
        `yolo detect train data=model_config.yaml model=yolov8n.pt epochs=100`
        `yolo detect train data=model_config.yaml model=yolov8m.pt epochs=100 name=date_numspecies_size_info patience=10 resume=True`

    The training will create a folder inside of runs/detect/ there you'll find the best and last weights and also some images with plots.

    You can follow the progress of the training and compare it to others with tensorboard:

    `tensorboard --logdir runs/detect/ --host=127.0.0.1`

4. **Calculate metrics**

    Run the training/scripts/get_metrics.sh script

    This script will calculate the classfication metrics of our object detection model. It can also save a confusion matrix with the metrics, the predictions, a folder structure with the missclassifcations and a txt file with the url links to Darwin of those missclassified images

    The script has multiple arguments, all except the model have default values:

    - **-m, --model**:                  Directory to model .pt _(required)_
    - **-i, --image_dir**:              Directory to images _(default: datasets/postprocessed/images/test)_
    - **-a, --annotations_dir**:        Location of YOLO annotations _(default: datasets/postprocessed/labels/test)_
    - **-c, --config_file**:            Configuration file containing the labels and thresholds _(default: config.yaml)_
    - **-p, --plot**:                   Path to plot confusion matrix _(default: confusion_matrix/confusion_matrix.jpg)_
    - **-e, --errors**:                Directory to store missclassifications _(default: datasets/missclassifed)_
    - **-s, --save_pred**:              Whether to store predictions or not _(default: False)_
    - **-d, --darwin_annotation_path**: Path to the release darwin annotations _(default: /workspaces/.darwin/datasets/triforkext/biodiversity/releases/latest/annotations)_
    - **-f, --output_file**:            File where to save the darwin urls of the missclassifed images _(default: darwin_urls.txt)_

    Make sure to use the **best.pt** weights from the model you want to validate.

    If **plot** is not provided it won't save the confusion matrix. Same happens for **errors** 

5. **Confident learning**

    If you decide to save the errors you can study the missclassifcations and reannotate some part of the data.


6. **Active learning**

    Run the training/scripts/active_learning.sh script

    This script will run an inference on the data specified and then get the N images of each class that have a higher average entropy. 

    The script has multiple arguments, all except the model have default values:

    - **-m, --model_dir**         Directory containing the model _(required)_
    - **-i, --image_dir**         Directory containing images _(default: /workspaces/.darwin/datasets/triforkext/biodiversity/images)_
    - **-r, --release_name**      Name of the Darwin2.0 release _(default: latest)_
    - **-o, --output_dir**        Directory to save the output _(default: datasets/active_learning)_
    - **-p, --pickle_dir**        Directory to save the pickled data _(default: datasets/pickled_inference/data.pkl)_
    - **-n, --top_n**             Number of images per class to be annotated _(default: 100)_
    - **-b, --batch_size**        Batch size for active learning _(default: 50)_
    - **--run_inference**         Run the pickle_inference script _(Flag)_

    If you use the flag **run_inference** the inference will be rerun. If you don't it will only be rerun if the pickle file does not exist. (Doing the inference on a lot of images takes a long time)
