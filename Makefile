NAME = simplemmo
VERSION = 0.1
GITSHA = $(shell git describe --tags --long --always)


define uniq =
  $(eval seen :=)
  $(foreach _,$1,$(if $(filter $_,${seen}),,$(eval seen += $_)))
  ${seen}
endef

BUILDABLE_PACKAGES := base $(filter-out dockerfiles/base,  $(wildcard dockerfiles/*))

.PHONY: all build build-no-cache clean run cli

all: clean build

test:
	nosetests --exe -v tests/

build: 
	$(foreach PACKAGE_INFO,$(BUILDABLE_PACKAGES), \
		docker build --pull=false -t $(NAME)-$(notdir $(PACKAGE_INFO)):latest --file dockerfiles/$(notdir $(PACKAGE_INFO)) dockerfiles/ ; \
		docker tag $(NAME)-$(notdir $(PACKAGE_INFO)) $(NAME)-$(notdir $(PACKAGE_INFO)):$(VERSION) ; \
	)

build-no-cache:
	$(foreach PACKAGE_INFO,$(BUILDABLE_PACKAGES), \
		docker build --no-cache --pull=false -t $(NAME)-$(notdir $(PACKAGE_INFO)):latest --file dockerfiles/$(notdir $(PACKAGE_INFO)) dockerfiles/ ; \
		docker tag $(NAME)-$(notdir $(PACKAGE_INFO)) $(NAME)-$(notdir $(PACKAGE_INFO)):$(VERSION) ; \
	)


clean:
	$(foreach PACKAGE_INFO,$(BUILDABLE_PACKAGES), \
		docker rmi $(NAME)-$(notdir $(PACKAGE_INFO)):$(VERSION) $(NAME)-$(notdir $(PACKAGE_INFO)):latest || true ; \
	)
	rm -f simplemmo.sqlite

run: build
	docker kill simplemmo-authserver simplemmo-charserver simplemmo-masterzoneserver || true
	docker rm simplemmo-authserver simplemmo-charserver simplemmo-masterzoneserver || true
	docker run --detach --name simplemmo-authserver -p 1234:1234 -v $(CURDIR):/database/ -it simplemmo-authserver
	docker run --detach --name simplemmo-charserver -p 1235:1235 -v $(CURDIR):/database/ -it simplemmo-charserver
	docker run --detach --name simplemmo-masterzoneserver -p 1236:1236 -v $(CURDIR):/database/ -v /var/run/docker.sock:/var/run/docker.sock -it simplemmo-masterzoneserver

cli: run
	docker run --rm --name simplemmo-cli -v $(CURDIR):/sqlite/ --link simplemmo-authserver --link simplemmo-charserver --link simplemmo-masterzoneserver -it simplemmo-cli $(cmd)
