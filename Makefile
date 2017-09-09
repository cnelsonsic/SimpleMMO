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

test: unit-test client-test

unit-test:
	docker run --rm -u 1000 -v `pwd`:/SimpleMMO -it simplemmo-cli bash -c 'rm __init__.pyc; mv __init__.py __init__.py.bak; nosetests --with-coverage --exe -v tests/test_authserver.py tests/test_charserver.py tests/test_zoneserver.py tests/test_scriptserver.py tests/test_elixir_models.py; mv __init__.py.bak __init__.py || true'
	mv .coverage .coverage.1

client-test:
	docker run --rm -u 1000 -v `pwd`:/SimpleMMO -it simplemmo-cli bash -c 'rm __init__.pyc; mv __init__.py __init__.py.bak; nosetests --with-coverage --exe -v tests/test_client.py; mv __init__.py.bak __init__.py || true'
	mv .coverage .coverage.1

coverage: unit-test
	docker run --rm -u 1000 -v `pwd`:/SimpleMMO -it simplemmo-cli bash -c 'coverage combine; coverage html; coverage report'

full-test: build
	docker run --rm -v `pwd`:/SimpleMMO -it simplemmo-cli bash -c 'rm __init__.py*; \
	  nosetests --exe -v tests/test_authserver.py tests/test_charserver.py tests/test_zoneserver.py tests/test_scriptserver.py tests/test_elixir_models.py; \
	  tail -q -F log/* & \
	  nosetests --exe -s -v tests/test_client.py;\
	  '

build: 
	$(foreach PACKAGE_INFO,$(BUILDABLE_PACKAGES), \
		docker build --pull=false -t $(NAME)-$(notdir $(PACKAGE_INFO)):latest --file dockerfiles/$(notdir $(PACKAGE_INFO)) . ; \
		docker tag $(NAME)-$(notdir $(PACKAGE_INFO)) $(NAME)-$(notdir $(PACKAGE_INFO)):$(VERSION) ; \
	)

build-no-cache: clean
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
	docker run --detach --name simplemmo-authserver -p 1234:1234 -v $(CURDIR)/log:/SimpleMMO/log -v $(CURDIR):/database/ -it simplemmo-authserver
	docker run --detach --name simplemmo-charserver -p 1235:1235 -v $(CURDIR)/log:/SimpleMMO/log -v $(CURDIR):/database/ -it simplemmo-charserver
	docker run --detach --name simplemmo-masterzoneserver -p 1236:1236 -v $(CURDIR)/log:/SimpleMMO/log -v $(CURDIR):/database/ --net=host -v /var/run/docker.sock:/var/run/docker.sock -it simplemmo-masterzoneserver

cli: run
	@while ! curl -s localhost:1234/ping > /dev/null; do sleep 1; done
	docker kill simplemmo-zoneserver-GhibliHills || true
	docker rm simplemmo-zoneserver-GhibliHills || true
	docker run --rm --name simplemmo-cli --net=host -v $(CURDIR):/sqlite/ -it simplemmo-cli $(cmd)
