include ./secrets/github.env
include ./secrets/darwin.env

build-train-yolo: 
	@docker build --no-cache --build-arg GITHUB_USER=$(GITHUB_USER) --build-arg GITHUB_TOKEN=$(GITHUB_TOKEN) --build-arg DARWIN_API_KEY=$(DARWIN_API_KEY) -t roadkill-train:latest -f dockerfiles/train-yolo.dockerfile .
