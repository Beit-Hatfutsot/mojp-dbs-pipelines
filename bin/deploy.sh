#!/usr/bin/env bash

git pull origin ${DEPLOY_BRANCH:-master}
bin/docker/build_all.sh
docker stack deploy -c docker-compose.override.yml pipelines
docker service update --force --detach=false pipelines_app
docker stack ps pipelines
