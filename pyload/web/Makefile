SHELL := /bin/sh
PATH := ${PATH}:.

.PHONY: build
build: install
    npm run postinstall

.PHONY: install
install: check
    npm install
    $(MAKE) clean

.PHONY: uninstall
uninstall:
    # $(MAKE) clean
    rm -rf node_modules
    ifdef $(wildcard "node")
        rm -f node
    endif

.PHONY: update
update: check
    npm update --depth 0

.PHONY: clean
clean:
    npm prune --production

.PHONY: check
check:
    ifdef $(shell type node &>/dev/null || type nodejs &>/dev/null && ln -s "$(shell which nodejs)" node &>/dev/null && echo true)
        @echo "nodejs linked to node in local dir"
    endif
