.PHONY: install test clean docker-build docker-start docker-logs docker-logs-f docker-restart docker-clean-start docker-stop deploy

DEPLOY_BRANCH ?= master

install:
	pip install --upgrade pip setuptools
	pip install --upgrade -e .[develop]

test:
	tox -r

clean:
	pip uninstall -y mojp_dbs_pipelines || true
	pip freeze | xargs pip uninstall -y || true

docker-build:
	docker build -t mojp-dbs-pipelines .

docker-start:
	docker-compose up -d

docker-logs:
	docker-compose logs

docker-logs-f:
	docker-compose logs -f

docker-restart:
	docker-compose restart
	make docker-logs-f

docker-clean-start:
	docker-compose down
	make docker-build
	make docker-start
	echo
	echo "waiting 5 seconds to let services start"
	sleep 5
	echo
	make docker-logs-f

docker-stop:
	docker-compose stop

deploy:
	git pull origin $(DEPLOY_BRANCH)
	make docker-build
	make docker-start
