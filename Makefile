USE_ALEMBIC ?= 1
LOAD_DATA ?= 1

build:
	docker build -t trustpilot-api-test -f application.dockerfile .

run: build
	docker run --rm -it -p 8000:8000 \
		-e USE_ALEMBIC=$(USE_ALEMBIC) \
		-e LOAD_DATA=$(LOAD_DATA) \
		trustpilot-api-test

clean:
	docker rmi trustpilot-api-test
