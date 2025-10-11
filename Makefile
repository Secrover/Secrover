IMAGE_NAME = secrover:latest
WORKDIR = /app
STAMP = .docker-built

dev:
	docker run -it --rm \
		--env-file .env \
		-v $(PWD)/rclone.conf:/root/.config/rclone/rclone.conf:ro \
		-v $(PWD)/config.yaml:/config.yaml \
		-v $(PWD)/repos:/app/repos \
		-v $(PWD)/output:/output \
		-v $(PWD)/secrover:/app/secrover \
		-v $(PWD)/templates:/app/templates \
		-v $(PWD)/main.py:/app/main.py \
		$(IMAGE_NAME)

$(STAMP): Dockerfile
	docker build -t $(IMAGE_NAME) .
	touch $(STAMP)

build: $(STAMP)

run: build
	docker run -it --rm \
		-v $(PWD)/config.yaml:/config.yaml \
		-v $(PWD)/repos:/app/repos \
		-v $(PWD)/output:/output \
		$(IMAGE_NAME)

lint: build
	docker run --rm --entrypoint "" -v $(PWD):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv run ruff check secrover/.

format-check: build
	docker run --rm --entrypoint "" -v $(PWD):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv run ruff format --check secrover/.

format: build
	docker run --rm --entrypoint "" -v $(PWD):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv run ruff format secrover/.

update_deps: build
	docker run --rm --entrypoint "" -v $(PWD):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv sync --upgrade