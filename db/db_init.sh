#!/bin/bash

PSQL_BIN=/usr/lib/postgresql/10/bin
DATA_PATH=/home/haow/microblog/data
LOG=${DATA_PATH}/logfile
USER=${1:-postgres}
DB_NAME=${2:-product}
PORT=${3:-5432}
DB_HOST=${4:-localhost}

${PSQL_BIN}/initdb -D ${DATA_PATH}
${PSQL_BIN}/pg_ctl -D ${DATA_PATH} -l ${LOG} start -o "-p ${PORT}"
echo "wait 3 second ..."
sleep 3
# this step is very important, we need create a user with host and port.
createuser -s ${USER} -h ${DB_HOST} -p ${PORT}
echo "create database ${DB_NAME} encoding='utf-8' template=template0;" | psql -U ${USER} -h ${DB_HOST} -p ${PORT}
echo "create database test encoding='utf-8' template=template0;" | psql -U ${USER} -h ${DB_HOST} -p ${PORT}
