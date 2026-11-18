include ../secrets/.env

build-train-yolo: 
	@docker build --build-arg GITHUB_USER=$(GITHUB_USER) --build-arg GITHUB_TOKEN=$(GITHUB_TOKEN) -t bio-train:yolo -f dockerfiles/train-yolo.dockerfile .


build-train-autodistill: 
	@docker build --build-arg GITHUB_USER=$(GITHUB_USER) --build-arg GITHUB_TOKEN=$(GITHUB_TOKEN) -t bio-train:autodistill -f dockerfiles/train-autodistill.dockerfile .
