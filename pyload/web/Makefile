SHELL=/bin/bash
WRONG_PATH := $(shell type node &>/dev/null || type nodejs &>/dev/null && ln -s /usr/bin/nodejs node &>/dev/null && echo "yes")
PATH := ${PATH}:.

init-web: prepare
	npm install
	npm install bower grunt-cli
	node_modules/bower/bin/bower install
	$(MAKE) update-web
	
update-web: prepare
	node_modules/grunt-cli/bin/grunt build

prepare:
ifeq ($(WRONG_PATH),yes)
	@echo "creating node link in local dir"
endif

.PHONY: prepare
