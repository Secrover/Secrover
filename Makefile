IMAGE_NAME = secrover:latest
WORKDIR = /app
STAMP = .docker-built

$(STAMP): Dockerfile
	docker build -t $(IMAGE_NAME) .
	touch $(STAMP)

build: $(STAMP)

lint: build
	docker run --rm --entrypoint "" -v $(PWD):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv run ruff check secrover/.

format-check: build
	docker run --rm --entrypoint "" -v $(PWD):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv run ruff format --check secrover/.

update_deps: build
	docker run --rm --entrypoint "" -v $(PWD):$(WORKDIR) -w $(WORKDIR) $(IMAGE_NAME) uv sync --upgrade