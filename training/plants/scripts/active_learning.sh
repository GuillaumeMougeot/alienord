#!/bin/bash

# Define default values
model_dir=""
image_dir="/workspaces/.darwin/datasets/triforkext/biodiversity/images"
release_name="latest"
output_dir="datasets/active_learning"
pickle_dir="datasets/pickled_inference/data.pkl"
top_n=100
batch_size=50
run_inference=0  # Default value, set to 0 (false)

display_help() {
    echo "Usage: $0  -m <model_dir> [-i <image_dir>] [-a <annotation_dir>] [-n <top_n>] [--run_inference]"
    echo "Converts data from Darwin2.0 to YOLOv8 format and performs data splitting."
    echo "Options:"
    echo "  -m, --model_dir         Directory containing the model (required)"
    echo "  -i, --image_dir         Directory containing images (default: $image_dir)"
    echo "  -r, --release_name      Name of the Darwin2.0 release (default: $release_name)"
    echo "  -o, --output_dir        Directory to save the output (default: $output_dir)"
    echo "  -p, --pickle_dir        Directory to save the pickled data (default: $pickle_dir)"
    echo "  -n, --top_n             Number of images per class to be annotated (default: $top_n)"
    echo "  -b, --batch_size        Batch size for active learning (default: $batch_size)"
    echo "  --run_inference         Run the pickle_inference script (default: $run_inference)"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model_dir) model_dir="$2"; shift ;;
        -i|--image_dir) image_dir="$2"; shift ;;
        -r|--release_name) release_name="$2"; shift ;;
        -o|--output_dir) output_dir="$2"; shift ;;
        -p|--pickle_dir) pickle_dir="$2"; shift ;;
        -n|--top_n) top_n="$2"; shift ;;
        -b|--batch_size) batch_size="$2"; shift ;;
        --run_inference) run_inference=1 ;;  # Set run_inference to 1 (true)
        -h|--help) display_help ;;
        *) echo "Unknown option: $1"; display_help;;
    esac
    shift
done

# Check if required arguments are provided
if [ -z "$model_dir" ]; then
    echo "Error: Please provide the path to the models weights"
    display_help
fi


# Set annotation directory
annotation_dir="/workspaces/.darwin/datasets/triforkext/biodiversity/releases/$release_name/annotations"
echo "Model directory: $model_dir"
echo "Image directory: $image_dir"
echo "Annotation directory: $annotation_dir"
echo "Pickle directory: $pickle_dir"
echo "Output directory: $output_dir"
echo "Top n: $top_n"
echo "Batch size: $batch_size"
echo "Run inference: $run_inference"
echo ""


# Run the pickle_inference script if run_inference flag is set
if [ $run_inference -eq 1 ]; then
    echo "Running pickle_inference script..."
    python3 -m utils.pickle_inference \
        --model_dir "$model_dir" \
        --image_dir "$image_dir" \
        --annotation_dir "$annotation_dir" \
        --pickle_dir "$pickle_dir" \
        --batch_size "$batch_size"
fi

echo ""
echo "Running active learning script..."
# Run active_learning.py
python3 -m utils.active_learning \
    --model_dir "$model_dir" \
    --image_dir "$image_dir" \
    --annotation_dir "$annotation_dir" \
    --output_dir "$output_dir" \
    --pickle_dir "$pickle_dir" \
    --top_n "$top_n"
