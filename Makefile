VERSION ?= latest

update_deps:
	uv sync --upgrade

publish:
	docker build -t secrover/secrover:$(VERSION) .
	docker push secrover/secrover:$(VERSION)