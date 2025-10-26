IMAGE_NAME = secrover:latest
WORKDIR = /app
STAMP = .docker-built

dev:
	docker run -it --rm \
		--env-file .env \
		-v $(pwd)/rclone.conf:/root/.config/rclone/rclone.conf:ro \
		-v $(pwd)/config.yaml:/config.yaml \
		-v $(pwd)/repos:/app/repos \
		-v $(pwd)/output:/output \
		-v $(pwd)/secrover:/app/secrover \
		-v $(pwd)/templates:/app/templates \
		-v $(pwd)/main.py:/app/main.py \
		$(IMAGE_NAME)

$(STAMP): Dockerfile
	docker build -t $(IMAGE_NAME) .
	touch $(STAMP)

build: $(STAMP)

run: build
	docker run -it --rm \
		--env-file .env \
		-v $(pwd)/rclone.conf:/root/.config/rclone/rclone.conf:ro \
		-v $(pwd)/config.yaml:/config.yaml \
		-v $(pwd)/repos:/app/repos \
		-v $(pwd)/output:/output \
		$(IMAGE_NAME)

lint: build
	docker run --rm --entrypoint "" -v $(pwd):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv run ruff check secrover/.

format-check: build
	docker run --rm --entrypoint "" -v $(pwd):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv run ruff format --check secrover/.

format: build
	docker run --rm --entrypoint "" -v $(pwd):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv run ruff format secrover/.

update_deps:
	docker run --rm --entrypoint "" -v $(pwd):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv sync --upgrade
