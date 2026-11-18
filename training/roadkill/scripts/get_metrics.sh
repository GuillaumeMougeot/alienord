#!/bin/bash

# Default values
model=""
image_dir="datasets/postprocessed/images/test"
annotations_dir="datasets/postprocessed/labels/test"
config_file="config.yaml"
plot="confusion_matrix/confusion_matrix.jpg"
errors="datasets/missclassifed"
save_dir=""

darwin_annotation_path="/workspaces/.darwin/datasets/triforkext/roadkill_vd_training/releases/latest/annotations"
output_file="darwin_urls.txt"


# Function to display script usage
display_help() {
    echo "Usage: $0 -m <model> -i <image_dir> -a <annotations_dir> -c <config_file> [-p <plot>] [-e <errors>] [-s <save_dir>]"
    echo "Calculate classification metrics out of object detection model."
    echo "Options:"
    echo "  -m, --model                 Directory to model .pt (required)"
    echo "  -i, --image_dir             Directory to images (default: $image_dir)"
    echo "  -a, --annotations_dir       Location of YOLO annotations (default: $annotations_dir)"
    echo "  -c, --config_file           Config yaml with names and thresholds(default: $config_file)"
    echo "  -p, --plot                  Path to plot confusion matrix (default: $plot)"
    echo "  -e, --errors                Directory to store missclassifications (default: $errors)"
    echo "  -s, --save_dir              Path to store predictions (default: $save_dir)"
    echo "  -d, --darwin_annotation_path Path to the release darwin annotations (default: $darwin_annotation_path)"
    echo "  -f, --output_file           File where to save the darwin urls of the missclassifed images (default: $output_file)"
    exit 1
}

# Parse command-line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -m|--model) model="$2"; shift ;;
        -i|--image_dir) image_dir="$2"; shift ;;
        -a|--annotations_dir) annotations_dir="$2"; shift ;;
        -c|--config_file) config_file="$2"; shift ;;
        -p|--plot) plot="$2"; shift ;;
        -e|--errors) errors="$2"; shift ;;
        -s|--save_dir) save_dir="$2"; shift ;;
        -d|--darwin_annotation_path) darwin_annotation_path="$2"; shift ;;
        -f|--output_file) output_file="$2"; shift ;;
        -h|--help) display_help ;;
        *) echo "Unknown option: $1"; display_help ;;
    esac
    shift
done

# Check if required arguments are provided
if [ -z "$model" ]; then
    echo "Error: Please provide the path to the models weights"
    display_help
fi


echo "Calculating metrics..."
# Execute the Python script to calculate classification metrics
python3 -m utils.object_detection_cls_metric \
    -m "$model" \
    -i "$image_dir" \
    -a "$annotations_dir" \
    -c "$config_file" \
    -p "$plot" \
    -e "$errors" \
    -s "$save_dir" \
&& if [ -n "$errors" ]; then
    echo "Getting darwins urls..." \
    && python3 -m utils.get_darwin_urls \
        -f "$errors" \
        -a "$darwin_annotation_path" \
        -o "$output_file"
   fi