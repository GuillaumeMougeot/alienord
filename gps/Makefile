
gen-schemas:
	@python3 -m utils.generate_config_schema

build-dev:
	@docker build -t gps:dev .

build-jetson:
	@docker build --platform linux/arm64/v8 -t gps-l4t:release .

run-dev:
	@docker run -e ENV=dev gps:dev
