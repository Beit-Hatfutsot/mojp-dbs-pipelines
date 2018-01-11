# Datapackage pipelines for The Museum of The Jewish People

[![Travis](https://img.shields.io/travis/Beit-Hatfutsot/mojp-dbs-pipelines/master.svg)](https://travis-ci.org/Beit-Hatfutsot/mojp-dbs-pipelines)

Pipelines for data sync of Jewish data sources to the DB of The Museum of The Jewish People

Uses the [datapackage pipelines framework](https://github.com/frictionlessdata/datapackage-pipelines)


## Overview

This project provides pipelines that sync data from multiple external sources to the [MoJP](http://dbs.bh.org.il/) Elasticsearch DB.


## Running

Install some dependencies (the following should work on recent versions of Ubuntu / Debian)

```
sudo apt-get install -y python3.6 python3-pip python3.6-dev libleveldb-dev libleveldb1v5
sudo pip3 install pipenv
```

Install the app depepdencies

```
pipenv install
```

Activate the virtualenv

```
pipenv shell
```

Install the datapackage_pipelines_mojp package for development

```
pip install -e .
```

Get the list of available pipelines

```
dpp
```

Run a pipeline

```
dpp run <PIPELINE_ID>
```



### Running the full pipelines environment using docker

* Install Docker and Docker Compose (refer to Docker guides for your OS)
* `cp .docker/docker-compose.override.yml.example.full docker-compose.override.yml`
* edit docker-compose.override.yml and modify settings (most likely you will need to set the CLEARMASH_CLIENT_TOKEN
* `bin/docker/build_all.sh`
* `bin/docker/start.sh`

This will provide:

* Pipelines dashboard: http://localhost:5000/
* PostgreSQL server: postgresql://postgres:123456@localhost:15432/postgres
* Elasticsearch server: localhost:19200
* Data files under: .docker/.data

After every change in the code you should run `bin/docker/build.sh && bin/docker/start.sh`

Additional features:

* Kibana for visualizations over Elasticsearch
  * `docker-compose up -d kibana`
  * http://localhost:15601
* Adminer web interface for the postgresql db
  * `docker-compose up -d adminer`
  * http://localhost:18080/?pgsql=db&username=postgres
  * default password is 123456

Running the tests using docker

* Build the tests image
  * `bin/docker/build_tests.sh`
* Run the tests
  * `bin/docker/run_tests.sh`
* Make changes to the code
* Re-run the tests (no need to build again in most cases)
  * `bin/docker/run_tests.sh`

### Running the pipelines locally

Make sure you have Python 3.6 in a virtualenv

* `bin/install.sh`
* `cp .env.example.full .env`
* modify .env as needed
  * most likely you will need to connect to the db / elasticsearch instances
  * the default file connects to the docker instances, so if you ran `bin/docker/start.sh` it should work as is
* `source .env`
* `export DPP_DB_ENGINE=$DPP_DB_ENGINE`
* `bin/test.sh`
* `dpp`


## Available Data Sources

### Clearmash

Clearmash is A CMS system which is used by MoJP for the MoJP own data

Clearmash exposes an [API](https://bh.clearmash.com/API/V5/Services/) to get the data

relevant links and documentation (clearmash support site requires login)

* [overview of the services and api urls](https://www.clearmash.com/skn/c7/Support/e1043/External_Resources_API__Server_API_)
