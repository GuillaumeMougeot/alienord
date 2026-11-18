
# Step one: Get video of files we are gonna test with
(inside training/plants)
ffmpeg -framerate 1 -pattern_type glob -i 'datasets/postprocessed/images/test/*.jpg' -c:v libx264 -pix_fmt yuv420p out2.mp4

# Step two: Run deepstream inference on the video jut generated (Change to software devcontainer)
(inside bio/)
python3 -m app.main

# Step three: Run the utils.object_detection_cls_metric_deepstream script on the files used to create the video and the output txt file from deepstream
(inside training/plants)
python3 -m utils.object_detection_cls_metric_deepstream -gt datasets/postprocessed/labels/test/ -pd deepstream.txt -c config.yaml -p confusion_matrix/deepstream.jpg