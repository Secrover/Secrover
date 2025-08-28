update_deps:
	uv sync --upgrade

publish:
	docker build -t secrover/secrover .
	docker push secrover/secrover