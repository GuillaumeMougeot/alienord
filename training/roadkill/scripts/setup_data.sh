#!/bin/bash

# Default values
#release_name="latest"
release_name="training-8-march-2024"
output_dir="/workspaces/vd-biodiversity/training/roadkill/datasets/postprocessed"
#image_dir="/workspaces/.darwin/datasets/triforkext/biodiversity/images"
#image_dir="/home/aleksandra/.darwin/datasets/triforkext/roadkill_vd_training/images"
image_dir="/workspaces/.darwin/datasets/triforkext/roadkill_vd_training/images"
config_file="config.yaml"
validation_split=10
test_split=5
mandatory_file_split=""

# Function to display script usage
display_help() {
    echo "Usage: $0 -r <release_name> [-o <output_dir>] [-i <image_dir>] [-c <config_file>] [-n <no_plant>] [-v <validation_split>] [-t <test_split>] [-m <mandatory_file_split>]"
    echo "Converts data from Darwin2.0 to YOLOv8 format and performs data splitting."
    echo "Options:"
    echo "  -r, --release_name      Name of the Darwin2.0 release (default: $release_name)"
    echo "  -o, --output_dir        Output directory for YOLOv8 format data (default: $output_dir)"
    echo "  -i, --image_dir         Directory containing images (default: $image_dir)"
    echo "  -c, --config_file       Config file (For class labels) (default: $config_file)"
    echo "  -v, --validation_split  Percentage of data for validation (default: $validation_split)"
    echo "  -t, --test_split        Percentage of data for testing (default: $test_split)"
    echo "  -m, --mandatory_file_split File where to specify the split a specific image should go to. Format: split_name image_name (optional)"
    exit 1
}

# Parse command-line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -r|--release_name) release_name="$2"; shift ;;
        -o|--output_dir) output_dir="$2"; shift ;;
        -i|--image_dir) image_dir="$2"; shift ;;
        -c|--config_file) config_file="$2"; shift ;;
        -v|--validation_split) validation_split="$2"; shift ;;
        -t|--test_split) test_split="$2"; shift ;;
        -m|--mandatory_file_split) mandatory_file_split="$2"; shift ;;
        -h|--help) display_help ;;
        *) echo "Unknown option: $1"; display_help ;;
    esac
    shift
done

# Set annotation directory
# annotation_dir="/workspaces/.darwin/datasets/triforkext/biodiversity/releases/$release_name/annotations"
#annotation_dir="/home/aleksandra/.darwin/datasets/triforkext/roadkill_vd_training/releases/$release_name/annotations"
annotation_dir="/workspaces/.darwin/datasets/triforkext/roadkill_vd_training/releases/$release_name/annotations"
echo "Annotation directory: $annotation_dir"
echo "Output directory: $output_dir"
echo "Image directory: $image_dir"
echo "Config file: $config_file"
echo "Validation split: $validation_split"
echo "Test split: $test_split"
echo "Mandatory file split: $mandatory_file_split"

# Inform the user about the process
echo "Converting data from Darwin2.0 to YOLOv8"

# Run the conversion script
python3 utils/darwin2yolo.py \
    --annotation_dir "$annotation_dir" \
    --image_dir "$image_dir" \
    --output_dir "datasets/yoloformat" \
    --config_file "$config_file" \
&& echo "Splitting data into train, test, and val" \
&& python3 utils/train_test_split_det.py \
    --image_dir "$image_dir" \
    --annotation_dir "datasets/yoloformat" \
    --output_dir "$output_dir" \
    --validation "$validation_split" \
    --test "$test_split" \
    --mandatory_dir "$mandatory_file_split" \
&& echo "Conversion successful." \
&& echo "Data distribution of all data" \
&& python3 utils/data_distribution.py \
    --annotation_dir "datasets/yoloformat" \
    --config_file "$config_file" \
&& echo "Data distribution of train split" \
&& python3 -m utils.data_distribution \
    --annotation_dir "$output_dir/labels/train" \
    --config_file "$config_file" \
&& echo "Data distribution of validation split" \
&& python3 -m utils.data_distribution \
    --annotation_dir "$output_dir/labels/val" \
    --config_file "$config_file" \
&& echo "Data distribution of test split" \
&& python3 -m utils.data_distribution \
    --annotation_dir "$output_dir/labels/test" \
    --config_file "$config_file" \
&& echo "Deleting datasets/yoloformat folder." \
&& rm -r datasets/yoloformat \
&& echo "Data processing complete!" \
|| echo "Conversion failed. Exiting script."
