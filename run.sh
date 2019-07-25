#!/bin/bash -ex

NAME=ppbot
DB_LOCATION=/db/
DB_NAME=tg_pp_bot.db

docker build -t ${NAME} .
docker rm -f ${NAME} || true
docker run --name ${NAME} -d --restart=unless-stopped -e PP_BOT_TOKEN=${PP_BOT_TOKEN} -e PP_BOT_DB_PATH=${DB_LOCATION}/${DB_NAME} -v ~/.ppbot/:${DB_LOCATION} ${NAME}
docker logs -f ${NAME}
