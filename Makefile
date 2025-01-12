DATE		= $(shell date)
PYTHON		= $(shell which python)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords
TEST_OPTS := -n auto -ra -m 'not integration'
QPC_COMPARISON_REVISION = a362b28db064c7a4ee38fe66685ba891f33ee5ba
PIP_COMPILE_ARGS = --no-upgrade
BINDIR  = bin

QUIPUCORDS_UI_PATH = ../quipucords-ui
QUIPUCORDS_UI_RELEASE = 0.9.3

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help                to show this message"
	@echo "  all                 to execute all following targets (except test)"
	@echo "  lint                to run all linters"
	@echo "  clean               to remove pyc/cache files"
	@echo "  clean-db            to remove postgres docker container / sqlite db"
	@echo "  clean-ui            to remove UI assets"
	@echo "  lint-flake8         to run the flake8 linter"
	@echo "  lint-pylint         to run the pylint linter"
	@echo "  lock-requirements   to lock all python dependencies"
	@echo "  test                to run unit tests"
	@echo "  test-coverage       to run unit tests and measure test coverage"
	@echo "  swagger-valid       to run swagger-cli validation"
	@echo "  setup-postgres      to create a default postgres container"
	@echo "  server-init         to run server initializion steps"
	@echo "  serve               to run the server with default db"
	@echo "  serve-swagger       to run the openapi/swagger ui for quipucords"
	@echo "  manpage             to build the manpage"
	@echo "  build-ui            to build ui and place result in django server"
	@echo "  fetch-ui            to fetch prebuilt ui and place it in django server"

all: lint test-coverage

clean:
	rm -rf .pytest_cache quipucords.egg-info dist build $(shell find . | grep -P '(.*\.pyc)|(\.coverage(\..+)*)$$|__pycache__')

clean-ui:
	rm -rf quipucords/client
	rm -rf quipucords/quipucords/templates
	rm -rf quipucords/staticfiles

clean-db:
	rm -rf quipucords/db.sqlite3
	docker rm -f qpc-db

lock-requirements:
	pip-compile $(PIP_COMPILE_ARGS) --generate-hashes --output-file=requirements.txt requirements.in
	pip-compile $(PIP_COMPILE_ARGS) --allow-unsafe --generate-hashes --output-file=requirements-build.txt requirements-build.in
	pip-compile $(PIP_COMPILE_ARGS) --generate-hashes --output-file=dev-requirements.txt dev-requirements.in requirements.in

upgrade-requirements:
	 $(MAKE) lock-requirements -e PIP_COMPILE_ARGS='--upgrade'

test:
	PYTHONHASHSEED=0 QUIPUCORDS_MANAGER_HEARTBEAT=1 QPC_DISABLE_AUTHENTICATION=True PYTHONPATH=`pwd`/quipucords \
	pytest $(TEST_OPTS)

test-case:
	echo $(pattern)
	$(MAKE) test -e TEST_OPTS="${TEST_OPTS} $(pattern)"

test-coverage:
	$(MAKE) test TEST_OPTS="${TEST_OPTS} --cov=quipucords"

test-integration:
	$(MAKE) test TEST_OPTS="-ra -vvv --disable-warnings -m integration"

swagger-valid:
	node_modules/swagger-cli/swagger-cli.js validate docs/swagger.yml

lint-flake8:
	git diff $(QPC_COMPARISON_REVISION) | flakeheaven lint --diff .

lint-black:
	darker --check --diff --revision $(QPC_COMPARISON_REVISION) .

lint: lint-black lint-flake8

server-makemigrations:
	$(PYTHON) quipucords/manage.py makemigrations api --settings quipucords.settings

server-migrate:
	$(PYTHON) quipucords/manage.py migrate --settings quipucords.settings -v 3

server-set-superuser:
	cat ./deploy/setup_user.py | python quipucords/manage.py shell --settings quipucords.settings -v 3

server-init: server-migrate server-set-superuser

setup-postgres:
	docker run --name qpc-db -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:14.1

server-static:
	$(PYTHON) quipucords/manage.py collectstatic --settings quipucords.settings --no-input

serve:
	$(PYTHON) quipucords/manage.py runserver --nostatic

$(QUIPUCORDS_UI_PATH):
	@echo "Couldn't find quipucords-ui repo (${QUIPUCORDS_UI_PATH})"
	@echo "Tip: git clone https://github.com/quipucords/quipucords-ui.git ${QUIPUCORDS_UI_PATH}"
	exit 1

build-ui: $(QUIPUCORDS_UI_PATH) clean-ui
	cd $(QUIPUCORDS_UI_PATH);yarn;yarn build
	cp -rf $(QUIPUCORDS_UI_PATH)/dist/client quipucords/client
	cp -rf $(QUIPUCORDS_UI_PATH)/dist/templates quipucords/quipucords/templates

fetch-ui: clean-ui
	curl -k -SL https://github.com/quipucords/quipucords-ui/releases/download/$(QUIPUCORDS_UI_RELEASE)/quipucords-ui-dist.tar.gz -o ui-dist.tar.gz &&\
    tar -xzvf ui-dist.tar.gz &&\
	mkdir -p quipucords/quipucords/templates quipucords/client &&\
    mv dist/templates quipucords/quipucords/templates &&\
    mv dist/client quipucords/client &&\
    rm -rf ui-dist* dist

qpc_on_ui_dir = ${QUIPUCORDS_UI_PATH}/.qpc/quipucords
$(qpc_on_ui_dir): $(QUIPUCORDS_UI_PATH)
	@echo "Creating quipucords symlink on UI repo"
	mkdir -p $(QUIPUCORDS_UI_PATH)/.qpc
	ln -sf $(TOPDIR) $(QUIPUCORDS_UI_PATH)/.qpc/quipucords

serve-swagger: $(qpc_on_ui_dir)
	cd $(QUIPUCORDS_UI_PATH);yarn;node ./scripts/swagger.js
