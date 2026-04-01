build:
	docker build . -t taskmaster

run: build
	docker run -it --rm -v ${PWD}:/app -w /app taskmaster sh