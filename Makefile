build:
	docker build . -t taskmaster

run:
	docker run -it --rm -v ${PWD}:/app -w /app taskmaster sh