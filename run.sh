#!/bin/bash -ex

NAME=ppbot

docker build -t ${NAME} .
docker rm -f ${NAME} || true
docker run --name ${NAME} -d --restart=unless-stopped -e PP_BOT_TOKEN=${PP_BOT_TOKEN} ${NAME}
docker logs -f ${NAME}
