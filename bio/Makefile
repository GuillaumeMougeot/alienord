include ../secrets/.env

build-dgpu: build-dgpu-base build-dgpu-dev

build-dgpu-base: 
	@docker build --build-arg GITHUB_USER=$(GITHUB_USER) --build-arg GITHUB_TOKEN=$(GITHUB_TOKEN) -t bio-dgpu:base -f dockerfiles/bio-dgpu-base.dockerfile .

build-dgpu-dev:
	docker build --network host -t bio-dgpu:dev -f dockerfiles/bio-dgpu-dev.dockerfile .

build-jetson:
	@docker build --network host -t bio-l4t:release -f dockerfiles/bio-l4t.dockerfile .

gen-schemas:
	@python3 -m utils.generate_config_schema

tar-setup:
	@tar -czvf setup.tar.gz ../secrets/nordfou-biodiversity-2cd0fb3af162.json ../secrets/bot.env ../secrets/tailscale.txt -C ../scripts/ setup-xnx.sh install-deps.sh