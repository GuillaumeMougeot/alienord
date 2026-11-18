# Detections statistics


## Prepare histogram with true-positives and false-positives


1. The first step to get statistics about detections is to download metadata in folder 'meta' from the google cloud. The metadata files consist information about confidence of detections. The second file that is needed is a file 'checked_imgs.csv' that provides information about true-positive animal detection. Put both to the input folder 'detections_statistics/input/'.

2. Then we can run 'check_confidence.py' python script, where we can adjust the data from which we want to get statistics. The output of this script is detections_confidence.txt in the folder 'detections_statistics/results/' file where we have information about filename, confidence, and if animal was detected or no. 

3. Now we can run 'histogram_results.py' to get histogram with true-positives and false-positives. You can find results in the output folder 'detections_statistics/results/'.

## Download images and divide to folders

1. To analyze true-positives and false-positives images we can download it directly to folders with names 'low_confidence_animal_false' , 'low_confidence_animal_true', 'high_confidence_animal_false', 'high_confidence_animal_true' by running 'download_and_divide_images.py'. You have to adjust the code to get folder with images that you need, it is not downloading all of them because of storage capacity.

## Plot images with metadata

1. If we want to draw bounding boxes on images to check what exactly was detected as a dead animal we run a script 'plot_images_with_metadata' by defining paths to:
- folder with images that we want to plot
- metadata folder downloaded from gcp
- output folder for images 
#### we can add those paths to the config folder  