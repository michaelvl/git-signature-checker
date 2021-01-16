IMAGE ?= git-signature-checker

.PHONY: build
build:
	docker build -t ${IMAGE} .

.PHONY: push
push:
	docker tag ${IMAGE} michaelvl/${IMAGE}
	docker push michaelvl/${IMAGE}

.PHONY: test-shell
test-shell:
	docker run --rm -it -v $(shell pwd)/tests:/tests:ro --entrypoint bash ${IMAGE}

.PHONY: test
test: test1 test2 test3 test4

.PHONY: test1
test1:
	docker run --rm -it -v $(shell pwd)/tests:/tests:ro --entrypoint /tests/test-simple-linear-history.sh ${IMAGE}

.PHONY: test2
test2:
	docker run --rm -it -v $(shell pwd)/tests:/tests:ro --entrypoint /tests/test-trust-levels.sh ${IMAGE}

.PHONY: test3
test3:
	docker run --rm -it -v $(shell pwd)/tests:/tests:ro --entrypoint /tests/test-revision-ranges.sh ${IMAGE}

.PHONY: test4
test4:
	docker run --rm -it -v $(shell pwd)/tests:/tests:ro --entrypoint /tests/test-keyring.sh ${IMAGE}
