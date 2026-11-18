gen-schemas:
	@python3 -m utils.generate_config_schema

build-dev:
	@docker build -t gcs:dev .

build-jetson:
	@docker build --platform linux/arm64/v8 -t gcs-l4t:release .

run-dev:
	@docker run -e ENV=dev -v ./data/:/workspaces/gcs/data -v ./secrets:/workspaces/gcs/secrets gcs:dev
