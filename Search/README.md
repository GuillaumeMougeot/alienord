# Search & API module

This is the repository for the Search & API module.

## Description

We want to store detections (gps coordinates + annotations + images) and recordings in a firestore database and provide search functionality to the users.

## Architecture

The module is divided in two parts, the update of the databse and the enpoint provided that allows the users to make queires to the database. They are both implemented using cloud functions.

The search update module will be as follows:

![image](../docs/architecture/search-update.png)

It's an event driven architecture based on google cloud services. For every file uploaded in the cloud bucket, it'll trigger an event to the cloud function endpoint that will update the database.

The search query module will be as follows:

![image](../docs/architecture/search-query.png)

It's a public endpoint where users can make queries to retrieve detections on the databse. In order for a user to query the endpoint they must provide a valid token in the HTTP request. If the token is valid, the query is send to the database that will provide the detections that meet the criteria provided in the query.


## Contributing

### Dev Setup to run update | query module

- `cd Search`
- Create `secrets` folder.
- Put the `db-service-account` file in there. It is available in LastPass. Ask jpes for access.
- Create a virtual environment `virtualenv venv` and activate it `source venv/bin/activate`
- Install requirements `pip install -r requirements.txt`
- `make local-dev-bucket-finalized` or `make local-dev-http-query`
- `bash tests/test-bucket-finalized.sh` or `bash tests/test-query.sh`

### Token generation

Run the following command from the root folder of the project:
```
python3 -m scripts.token_generator [-n <NUMBER_TOKENS>]
```

The script will randomly generate `<NUMBER_TOKENS>` tokens and save them in the firestore database.

**NOTE:** The `GOOGLE_APPLICATION_CREDENTIALS` must be set with the path to the `db-service-account` service account.

### Token invalidation

Run the following command from the root folder of the project:
```
python3 -m scripts.disable_token -t <TOKEN> [-f]
```
The script will invalidate the `<TOKEN>` from the database. Thus, when a user provides the `<TOKEN>` it'll raise an `401 unauthorized` error. If the `-f` option is provided, the `<TOKEN>` will be removed from the database.

**NOTE:** The `GOOGLE_APPLICATION_CREDENTIALS` must be set with the path to the `db-service-account` service account.

### Deployment

There's a CI/CD pipeline with Github actions in place so that any commit or PR in the main branch will trigger the deployment in google cloud. In case you want to do the dpeloy manually you can run the following commands:

- Deploy the update module:

```
make deploy-bucket-finalized
```
- Deploy the search module:
```
make deploy-search
```

When the deployment is done, you'll need to get the URL of the endpoint. You can get it with the following command:
```
make get-url
```

### Test functionality

To test the funcionality of both the update and query module locally, refer to the `Dev Setup` section of this document.

On the other hand, you can test the functionality once the deployment is successful. To test the update module just try uploading a file into the `data-biodiversity` bucket and check the database for the entry.

For the query module you can the `curl` command to test the functionality.
```
curl <URL> \
  -X POST \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
        "min_tp": "<VALUE>",
        "max_tp": "<VALUE>",
        "device": ["<VALUE_1>", ... ,"<VALUE_N>"],
        "country": [<VALUE_1>, ... , "<VALUE_N>"],
        "plant_type": ["<VALUE_1>", ..., "<VALUE_N>"]
      }'
```

**NOTE**: You need to provide the URL and the token to the `curl` command. Check the database for a valid token and the `Deployment` section of this document to get the public URL.