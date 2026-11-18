
zip-bucket-finalized:
	@mkdir app && \
	cp -r configs core infra utils app && \
	cp cloud-functions/bucket-finalized/main.py *.py requirements.txt app && \
	tar -cvf app.tar -C app .

deploy-bucket-finalized:
	@cp cloud-functions/bucket-finalized/main.py . && \
	gcloud functions deploy bucket_finalized \
	--gen2 \
	--region=europe-west1 \
	--runtime=python310 \
	--source=. \
	--run-service-account=db-service-account@nordfou-biodiversity.iam.gserviceaccount.com \
	--entry-point=bucket_finalized \
	--trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
	--trigger-event-filters="bucket=data-biodiversity" \
	--trigger-service-account=eventarc-trigger@nordfou-biodiversity.iam.gserviceaccount.com \
	--trigger-location=europe-west1

deploy-search:
	@cp cloud-functions/query/main.py . && \
	gcloud functions deploy http_query \
	--gen2 \
	--region=europe-west1 \
	--runtime=python310 \
	--source=. \
	--run-service-account=db-service-account@nordfou-biodiversity.iam.gserviceaccount.com \
	--entry-point=http_query \
	--trigger-http \
	--allow-unauthenticated

local-dev-bucket-finalized:
	@cp cloud-functions/bucket-finalized/main.py . && \
	export GOOGLE_APPLICATION_CREDENTIALS="secrets/nordfou-biodiversity-61ea21cbd788.json" && \
	functions-framework --target=bucket_finalized --signature-type=cloudevent

local-dev-http-query:
	@cp cloud-functions/query/main.py . && \
	export GOOGLE_APPLICATION_CREDENTIALS="secrets/nordfou-biodiversity-61ea21cbd788.json" && \
	functions-framework --target=http_query --debug

get-url:
	@gcloud functions describe http_query \
	--gen2 \
	--region=europe-west1 \
	--format="value(serviceConfig.uri)"

clean:
	@rm main.py
