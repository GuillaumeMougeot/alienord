import os
from dataclasses import dataclass
import zlib
from typing import Optional, List
import shutil
import re
from typing import Dict
import argparse
from tqdm import tqdm

from core.infra.adapters.training.io.read import ImgReader, Darwin2Reader
from core.infra.adapters.training.io.write import ImgWriter
from core.domain.annotation import Annotation

"""
Arguments:
- validation: Percent of the validation set
- test: Percent of the test set
- image_dir: Directory of images
- annotation_dir: Directory of Darwin annotations
- output_dir: Directory to save YOLO annotations
- mandatory_dir: Directory to txt file with filenames that have to go to test or val

Description:
This scripts performs the split of images and annotations into the train, test and validation split.

The split must be reproducible, so we use the filename to calculate the split (we do it using zlib.crc32 although it should be changed to sha256). 
If the filename is in the mandatory directory, we use the split from there. 
The mandatory file structure is as follows:
split filename
split filename
...

This way you can define the split for specific files.


There is a regex to get the source of the image, if it's not from the data we've collected it will not be assigned to test or val.
"""

@dataclass
class DetectionDatasetYoloConfig:
    validation_percent: float
    test_percent: float
    annotation_dir: str
    images_dir: str
    output_dir: str

@dataclass
class MandatoryFile:
    filename: str
    split: str

class PrepareDetectionDatasetYolo:
    def __init__(
        self,
        config: DetectionDatasetYoloConfig
    ) -> None:
        self.config = config
        self.create_output_directories()

        self.img_reader = ImgReader(config.images_dir)
        self.annotation_reader = Darwin2Reader(config.annotation_dir)

        self.img_writers: dict[str, ImgWriter] = {
            'train': ImgWriter(os.path.join(config.output_dir, 'images', 'train')),
            'val': ImgWriter(os.path.join(config.output_dir, 'images', 'val')),
            'test': ImgWriter(os.path.join(config.output_dir, 'images', 'test'))
        }


    def get_filenames(self):
        return self.annotation_reader.list_names()


    def get_image_split(self, filepath: str, mandatory_files: Dict[str, str] = None):
        """
        Stable way of calculating the split an image belongs to based on the image name.
        
        If the image is in the mandatory_files dictionary, it will return the split from there.
        
        If the image does not come from the data we've collected it will be assigned to train. (We can tell by the name of the image)

        Arguments
        ---------
        The image filepath as a string.
        The dictionary with the mandatory files and their split.

        Returns
        -------
        The split as a string.
        """
        if mandatory_files and filepath in mandatory_files:
            return mandatory_files[filepath]            
        
        match = re.match(r'\d{8}T\d{6}', filepath) # See if the image starts with the timestamp in YYYYMMDDTHHMMSS format
        if match:
            filepath = match.group(0)

        x = zlib.crc32(filepath.encode()) & 0xffffffff # TODO: change to sha256

        val = self.config.validation_percent / 100 * 2**32
        test = val + self.config.test_percent / 100 * 2**32
        if x < val and match:
            return 'val'
        elif x < test and match:
            return 'test'
        else:
            return 'train'


    def create_output_directories(self):

        os.makedirs(os.path.join(self.config.output_dir, 'images', 'train'), exist_ok=True)
        os.makedirs(os.path.join(self.config.output_dir, 'images', 'val'), exist_ok=True)
        os.makedirs(os.path.join(self.config.output_dir, 'images', 'test'), exist_ok=True)

        os.makedirs(os.path.join(self.config.output_dir, 'labels', 'train'), exist_ok=True)
        os.makedirs(os.path.join(self.config.output_dir, 'labels', 'val'), exist_ok=True)
        os.makedirs(os.path.join(self.config.output_dir, 'labels', 'test'), exist_ok=True)

    def prepare_data_for_name(self, filename: str, mandatory_files: Dict[str, str] = None) -> Optional[List[Annotation]]:
        # Get split and read image
        split = self.get_image_split(filename, mandatory_files)  
        img = self.img_reader.read(filename)
        
        # Write image and annotation into corresponding split
        self.img_writers[split].write(img, filename)
        filename_with_ext = filename + ".txt"
        try:
            shutil.copy(os.path.join(self.config.annotation_dir, filename_with_ext),
                    os.path.join(self.config.output_dir, "labels", split, filename_with_ext))
        except FileNotFoundError:
            print("Error: The source file '{}' was not found.".format(os.path.join(self.config.annotation_dir, filename_with_ext)))
        except IOError as e:
            print("Error: Input/output error occurred:", str(e))
        except Exception as e:
            print("An unexpected error occurred:", str(e))
     

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare data for object detection')

    parser.add_argument('-val', '--validation', type=int, help='Percent of the validation set', default='10')
    parser.add_argument('-test', '--test', type=int, help='Percent of the test set', default='5')
    parser.add_argument('-i', '--image_dir', type=str, help='Directory to get images.')
    parser.add_argument('-a', '--annotation_dir', type=str, help='Location of YOLO annotations.')
    parser.add_argument('-o', '--output_dir', type=str, help='Output directory.')
    parser.add_argument('-m', '--mandatory_dir', type=str, help='Directory to txt file with filenames that have to go to test or val')

    args = parser.parse_args()

    config = DetectionDatasetYoloConfig(
        validation_percent=args.validation,
        test_percent=args.test,
        annotation_dir=args.annotation_dir,
        images_dir=args.image_dir,
        output_dir=args.output_dir,
    )
    
    mandatory_files = {}
    if args.mandatory_dir:
        try:
            with open(args.mandatory_dir, "r") as f:
                for line in f:
                    split, filename = line.strip().split(' ', 1)
                    mandatory_files[filename] = split
        except FileNotFoundError:
            print("Error: The specified file '{}' was not found.".format(args.mandatory_dir))
        except ValueError:
            print("Error: Invalid format in the input file.")
        except Exception as e:
            print("An unexpected error occurred:", str(e))

    
    prep = PrepareDetectionDatasetYolo(config)

    filenames = prep.get_filenames()

    # Iterate over filenames sequentially
    for filename in tqdm(filenames):
        prep.prepare_data_for_name(filename, mandatory_files)
