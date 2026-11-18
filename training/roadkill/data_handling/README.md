# Data handling

## Setting Google Cloud Service Account Key

In order to access the cloud storage, a personal key needs to be set up. (Keep this key local!)

Go to [IAM & Admin - Service Accounts tab](https://console.cloud.google.com/iam-admin/serviceaccounts?hl=en&project=roadkill-vd-poc) in the roadkill-vd-poc project on Google Cloud.

Then locate the "ui-image-handling@roadkill-vd-poc.iam.gserviceaccount.com" service account and click it.

Go to "Keys" tab, "Add Key" -> "Create new key" and check off json file type.

Save this key to the data_handling folder when using it for data handling. 

Go to the config.yaml file and change `gcs_key_filename` to the filename of the newly generated key.

Ideally, everything should work now without further setup, if all the python required python packages are installed. Note that `google.cloud.storage` module can be installed by:

```bash
pip install google-cloud-storage
```

## Downloading Unchecked Data

Inside config.yaml, set `data_dir` to wherever the data directory is preferred. This will be where all the sorting of data can take place. report_roadkill.csv is then read from the gcs `images bucke` and all the images not in that file is downloaded to `YOUR_DATA_DIR/unchecked_images/`. 

Now, just run `download_unchecked_images.py` 

How it works: Read the checked_imgs.csv file inside the data-vd bucket of Google Cloud Storage and download all the images inside images/ that do not have an entry in checked_imgs.csv. The images will be downloaded to {data_dir}/unchecked_images


## Uploading Checked Image Info

After setting up the data directory correctly and changing `config.yaml` accordingly, you can run `checked_data_handler.py`. Be careful to only overwrite a correct version to gcs, the script will prompt you to answer y/n whether to upload to gcs. 

How it works:
* It reads the checked_imgs.csv file from data-vd bucket inside Google Cloud Storage.
* Checks all the local checked images folders (see `checked_img_dir_names` inside config.yaml) and append all the newly checked images into the csv file with animal and unblurred info.
* Lastly, if prompted to, it will upload edited version of the checked images csv and overwrite the one in gcs.

## What is needed?
Everything should be functional so refactoring and optimization is mostly what's left.

## Download all images

In the folder data_handling it is also script ´download_all_images´ that download all images that was manually checked from the google cloud. We don't need it in a basis pipeline.