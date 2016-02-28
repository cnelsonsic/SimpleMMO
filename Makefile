NAME = simplemmo
VERSION = 0.1


define uniq =
  $(eval seen :=)
  $(foreach _,$1,$(if $(filter $_,${seen}),,$(eval seen += $_)))
  ${seen}
endef

BUILDABLE_PACKAGES := base $(filter-out dockerfiles/base,  $(wildcard dockerfiles/*))

.PHONY: all build

all: build

build: 
	$(foreach PACKAGE_INFO,$(BUILDABLE_PACKAGES), \
		docker build --pull=false -t $(NAME)-$(notdir $(PACKAGE_INFO)):latest --file dockerfiles/$(notdir $(PACKAGE_INFO)) dockerfiles/ ; \
		docker tag $(NAME)-$(notdir $(PACKAGE_INFO)) $(NAME)-$(notdir $(PACKAGE_INFO)):$(VERSION) ; \
	)

clean:
	$(foreach PACKAGE_INFO,$(BUILDABLE_PACKAGES), \
		docker rmi $(NAME)-$(notdir $(PACKAGE_INFO)):$(VERSION) $(NAME)-$(notdir $(PACKAGE_INFO)):latest ; \
	)
